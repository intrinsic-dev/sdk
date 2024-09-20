// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_server.h"

#include <sys/file.h>
#include <sys/resource.h>
#include <sys/socket.h>

#include <cerrno>
#include <cstddef>
#include <cstring>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/cleanup/cleanup.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/memory/memory.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"
#include "ortools/base/filesystem.h"
#include "ortools/base/options.h"
#include "ortools/base/path.h"

namespace intrinsic::icon {

namespace {

constexpr absl::string_view kLockSuffix = ".lock";

// Returns the path of the lockfile.
std::string LockName(absl::string_view socket_directory,
                     absl::string_view module_name) {
  return absl::StrCat(file::JoinPath(socket_directory, module_name),
                      kLockSuffix);
}

// Uses flock (https://linux.die.net/man/2/flock) to lock `absolute_lock_path`.
// The operating system automatically releases the Lock when the process exits.
// An alternative is using https://linux.die.net/man/2/fcntl on the
// socket fd.
// Tries once when `timeout` is absl::ZeroDuration or negative.
absl::StatusOr<int> TryLockPath(absl::string_view absolute_lock_path,
                                absl::Duration timeout) {
  absl::Time deadline = absl::Now() + timeout;
  if (absolute_lock_path.empty()) {
    return absl::InvalidArgumentError("path cannot be empty.");
  }

  if (!file::IsAbsolutePath(absolute_lock_path)) {
    return absl::InvalidArgumentError(
        absl::StrCat("Path must be absolute. Got: ", absolute_lock_path));
  }
  // Don't delete the lock file, even on shutdown.
  // Otherwise there is a potential race between deletion and re-creation of the
  // file.
  // Example of the race where a new process is started while the old is
  // shutting down:
  //
  // 1. The newer process checks for existence of the lock file, finds the
  //    file, and waits to acquire the lock.
  // 2. The older process then executes the DomainSocketServer destructor
  //    as part of its shutdown, and releases the lock.
  // 3. The newer process acquires the lock.
  // 4. The older process deletes the lock file.
  // 5. Another process may acquire the lock at any time, because the file
  //    doesn't exist on the filesystem anymore.
  int lock_fd = open(absolute_lock_path.data(), O_WRONLY | O_CREAT,
                     S_IRWXU | S_IRWXG | S_IRWXO);

  if (lock_fd == -1) {
    return absl::InternalError(absl::StrCat("Unable to open lock '",
                                            absolute_lock_path,
                                            "' with error: ", strerror(errno)));
  }

  absl::Cleanup close_lock_fd = [&lock_fd, absolute_lock_path]() {
    if (close(lock_fd) == -1) {
      LOG(WARNING) << "Failed to close lock fd for '" << absolute_lock_path
                   << "' with error: " << strerror(errno) << ".";
    }
  };
  // Try once even if the deadline has passed.
  bool logged_error = false;
  do {
    // Uses LOCK_NB to make flock nonblocking and avoid blocking the process.
    if (int err = flock(lock_fd, LOCK_EX | LOCK_NB); err == 0) {
      LOG(INFO) << "Acquired exclusive lock '" << absolute_lock_path << "'.";
      std::move(close_lock_fd).Cancel();
      return lock_fd;
    } else {
      if (errno == EWOULDBLOCK) {
        LOG_IF(WARNING, !logged_error)
            << "File '" << absolute_lock_path
            << "' is locked by another process, will retry until " << deadline
            << ".";
        logged_error = true;
        absl::SleepFor(absl::Seconds(1));
        continue;
      } else {
        return absl::InternalError(
            absl::StrCat("Unable to lock '", absolute_lock_path,
                         "' with error: ", strerror(errno)));
      }
    }
  } while (absl::Now() < deadline);
  return absl::DeadlineExceededError(
      absl::StrCat("Timed out waiting for lock '", absolute_lock_path,
                   "' to become exclusive"));
}

// Releases the flock held by the server.
// It's important that the lock file is not deleted on shutdown.
// Otherwise there is a potential race between deletion and re-creation.
absl::Status UnlockPathCloseLockfile(int lockfile_fd) {
  if (lockfile_fd == -1) {
    return absl::InvalidArgumentError("Lockfile is invalid");
  }

  if (int err = flock(lockfile_fd, LOCK_UN); err != 0) {
    return absl::InternalError(
        absl::StrCat("Unable to unlock with error: ", strerror(errno)));
  }

  if (close(lockfile_fd) == -1) {
    LOG(WARNING) << "Failed to close lockfile fd with error: "
                 << strerror(errno) << ".";
  };
  return absl::OkStatus();
}

}  // namespace

// Prepares a single message.
absl::StatusOr<std::unique_ptr<const DomainSocketServer::Message>>
DomainSocketServer::PrepareMessage(
    size_t message_index, size_t num_messages,
    const domain_socket_internal::ShmDescriptors& descriptors) {
  if (message_index == 0) {
    return absl::OutOfRangeError("message_index starts at one");
  }
  if (num_messages == 0) {
    return absl::OutOfRangeError("num_messages starts at one");
  }
  if (message_index > num_messages) {
    return absl::OutOfRangeError(absl::StrCat(
        "message_index (", message_index,
        ") cannot be greater than num_messages (", num_messages, ")"));
  }

  auto message = std::make_unique<Message>();
  message->descriptors = descriptors;

  message->descriptors.transfer_data.message_index = message_index;
  message->descriptors.transfer_data.num_messages = num_messages;
  if (protocol_version_ !=
      domain_socket_internal::kDomainSocketProtocolVersion) {
    LOG(WARNING) << "Overriding protocol version from "
                 << domain_socket_internal::kDomainSocketProtocolVersion
                 << " to " << protocol_version_
                 << ". This should only happen in tests.";

    message->descriptors.transfer_data.domain_socket_protocol_version =
        protocol_version_;
  }

  message->iov = {.iov_base = &message->descriptors.transfer_data,
                  .iov_len = sizeof(message->descriptors.transfer_data)};

  message->msgh = {.msg_name = nullptr,
                   .msg_namelen = 0,
                   .msg_iov = &message->iov,
                   .msg_iovlen = 1};

  // char has a size of 1 byte.
  message->cmsg_buf = std::vector<char>(
      CMSG_SPACE(message->descriptors.file_descriptors_in_order.size() *
                 sizeof(int)),
      0);

  message->msgh.msg_control = message->cmsg_buf.data();
  message->msgh.msg_controllen = message->cmsg_buf.size();
  struct cmsghdr* cmsgp = CMSG_FIRSTHDR(&message->msgh);
  if (!cmsgp) {
    return absl::InternalError("Failed to get first control message header");
  }
  cmsgp->cmsg_level = SOL_SOCKET;
  cmsgp->cmsg_type = SCM_RIGHTS;
  cmsgp->cmsg_len = CMSG_LEN(
      message->descriptors.file_descriptors_in_order.size() * sizeof(int));
  for (int i = 0; i < message->descriptors.file_descriptors_in_order.size();
       ++i) {
    reinterpret_cast<int*>(CMSG_DATA(cmsgp))[i] =
        message->descriptors.file_descriptors_in_order[i];
  }

  return message;
}

absl::StatusOr<std::vector<std::unique_ptr<const DomainSocketServer::Message>>>
DomainSocketServer::PrepareMessages(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map) {
  std::vector<std::unique_ptr<const DomainSocketServer::Message>> messages;

  if (segment_name_to_file_descriptor_map.empty()) {
    return absl::InvalidArgumentError(
        "segment_name_to_file_descriptor_map is empty.");
  }
  // Computes the number of required messages starting at 1.
  // Example:
  // Assuming kMaxFdsPerMessage = 10
  // kNumMessages =  1 for [  1 -  10] fds.
  // kNumMessages =  2 for [ 11 -  20] fds.
  // ...
  // kNumMessages =  9 for [ 81 -  90] fds.
  // kNumMessages = 10 for [ 91 - 100] fds.
  // kNumMessages = 11 for [101 - 110] fds.
  const size_t kNumMessages =
      1 + ((segment_name_to_file_descriptor_map.size() - 1) /
           (domain_socket_internal::kMaxFdsPerMessage));
  size_t descriptor_count = 0;
  auto map_it = segment_name_to_file_descriptor_map.begin();
  // One indexed, so message_index == kNumMessages is OK.
  for (size_t message_index = 1; message_index <= kNumMessages;
       ++message_index) {
    LOG(INFO) << "Preparing message " << message_index << " of "
              << kNumMessages;
    // Fill descriptors for this message.
    domain_socket_internal::ShmDescriptors descriptors;
    auto& fd_names = descriptors.transfer_data.file_descriptor_names;
    for (fd_names.mutate_size(0);
         // Should not send more than kMaxFdsPerMessage FDs
         (fd_names.size() < domain_socket_internal::kMaxFdsPerMessage) &&
         // Cannot add more names than the fixed-size `names`
         // array supports
         (fd_names.size() < fd_names.names()->size()) &&
         // Cannot add more names than we got as inputs
         (map_it != segment_name_to_file_descriptor_map.end());
         ++map_it, fd_names.mutate_size(fd_names.size() + 1)) {
      SegmentName segment_name;
      const int kMaxSegmentStringSize = segment_name.value()->size();
      const auto& name = map_it->first;
      // fbs doesn't have char as datatype, only int8_t which is byte
      // compatible.
      auto* data =
          reinterpret_cast<char*>(segment_name.mutable_value()->Data());
      std::memset(data, '\0', kMaxSegmentStringSize);
      // bytes is the number of bytes that would have been written if the
      // string was not truncated, not counting the terminal null character.
      if (const int bytes =
              absl::SNPrintF(data, kMaxSegmentStringSize, "%s", name);
          bytes != name.size()) {
        // errno is only set when the return value is negative.
        if (bytes < 0) {
          return absl::InternalError(
              absl::StrCat("Failed to copy segment name '", name,
                           "'  to buffer with Error: ", strerror(errno)));
        }

        if (bytes < name.size()) {
          return absl::InternalError(
              absl::StrCat("Wrote fewer bytes (", bytes, ") than expected (",
                           name.size(), ") for segment name '", name,
                           "'. Segment name may contain a stray null byte."));
        }
        // SNPrintF automatically truncates the string to fit into the buffer.
        // bytes doesn't count the terminating zero, but we need
        // room in our buffer for it.
        if (bytes > (kMaxSegmentStringSize - 1)) {
          return absl::InternalError(
              absl::StrCat("Segment name '", name,
                           "' is longer than maximum allowed length (",
                           kMaxSegmentStringSize - 1, ")"));
        }

        // E.g. null byte in the string.
        return absl::InternalError(absl::StrCat(
            "Failed to copy segment name '", name,
            "'  to buffer. SNPrintF returned ", bytes,
            " bytes, but the segment name has ", name.size(), " bytes)"));
      }
      descriptors.transfer_data.file_descriptor_names.mutable_names()->Mutate(
          fd_names.size(), segment_name);

      descriptors.file_descriptors_in_order.push_back(map_it->second);
    }
    descriptor_count += fd_names.size();
    INTR_ASSIGN_OR_RETURN(auto message,
                          PrepareMessage(
                              /*message_index=*/message_index,
                              /*num_messages=*/kNumMessages, descriptors));
    messages.push_back(std::move(message));
  }
  if (descriptor_count != segment_name_to_file_descriptor_map.size()) {
    return absl::InternalError(
        absl::StrCat("Expected ", segment_name_to_file_descriptor_map.size(),
                     " descriptors, but only got ", descriptor_count));
  }

  return messages;
}

absl::Status DomainSocketServer::ServeShmDescriptors(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map) {
  if (request_handler_) {
    return absl::FailedPreconditionError(
        absl::StrCat("Server is already serving descriptors on socket ",
                     absolute_socket_path_));
  }
  const size_t kNumDescriptors = segment_name_to_file_descriptor_map.size();

  // Determine the number of possible file descriptors.
  struct rlimit fd_limit;
  if (getrlimit(RLIMIT_NOFILE, &fd_limit) == -1) {
    return absl::FailedPreconditionError(
        absl::StrCat("Failed to get limit of in-flight file descriptors "
                     "(RLIMIT_NOFILE) with error: ",
                     strerror(errno)));
  }
  // rlim_cur is one greater than the maximum number of FDs.
  if (kNumDescriptors >= fd_limit.rlim_cur) {
    return absl::OutOfRangeError(absl::StrCat(
        "Number of file descriptors (", kNumDescriptors,
        ") >= current soft limit (rlim_cur: ", fd_limit.rlim_cur,
        "). Max limit (rlim_max) of RLIMIT_NOFILE is ", fd_limit.rlim_max));
  }

  // On Linux, at least one byte of “real data” is required to successfully
  // send ancillary data over a Unix domain stream socket.
  if (kNumDescriptors < 1) {
    return absl::InvalidArgumentError(
        "At least one file descriptor and name must be provided");
  }

  INTR_ASSIGN_OR_RETURN(messages_,
                        PrepareMessages(segment_name_to_file_descriptor_map));

  if (listen(socket_fd_, /*backlog=*/1) == -1) {
    return absl::InternalError(absl::StrCat(
        "Failed to listen to socket with error: ", strerror(errno)));
  }
  LOG(INFO) << "Socket '" << absolute_socket_path_ << "' is serving  "
            << kNumDescriptors << " descriptors.";

  absl::Notification handler_started;
  request_handler_ = std::make_unique<intrinsic::Thread>();

  // Accepts a connection, sends the prepared message and closes the connection.
  INTR_RETURN_IF_ERROR(request_handler_->Start(
      ThreadOptions().SetName("DSHandler"), [this, &handler_started]() -> void {
        handler_started.Notify();
        while (!ThisThreadStopRequested()) {
          LOG(INFO) << "Waiting for new connection.";

          // Accept all new connections.
          // A blocking socket is fine, because closing the socket unblocks.
          int to_client_sock = accept(socket_fd_, nullptr, nullptr);
          if (to_client_sock == -1) {
            LOG(ERROR) << "Error while calling accept on '"
                       << absolute_socket_path_ << "': " << strerror(errno)
                       << ". Exiting. This is expected during shutdown.";
            return;
          }
          LOG(INFO) << "Accepted new connection on '" << absolute_socket_path_
                    << "'.";
          // Timeout stops rogue clients from blocking the server.
          // One second is more than enough time to send a message.
          struct timeval tv = absl::ToTimeval(absl::Seconds(1));
          if (setsockopt(to_client_sock, SOL_SOCKET, SO_SNDTIMEO,
                         (const char*)&tv, sizeof tv) == -1) {
            LOG(ERROR) << "Failed to set socket timeout with error: "
                       << strerror(errno);
          }

          for (const auto& message : messages_) {
            // Only sending a single message without an explicit protocol.
            ssize_t bytes_sent = sendmsg(to_client_sock, &message->msgh, 0);
            if (bytes_sent == -1) {
              LOG(ERROR) << "sendmsg failed with error: " << strerror(errno)
                         << ".";
              continue;
            }

            if (size_t expected_bytes =
                    sizeof(message->descriptors.transfer_data);
                bytes_sent != expected_bytes) {
              LOG(ERROR) << "Expected to send " << expected_bytes
                         << "bytes, but only sent " << bytes_sent << "bytes.";
            }

            LOG(INFO) << "Sent "
                      << message->descriptors.file_descriptors_in_order.size()
                      << " file descriptors and " << bytes_sent
                      << " bytes of TransferData in message "
                      << message->descriptors.transfer_data.message_index
                      << " of " << messages_.size() << ".";
          }

          LOG(INFO) << "Finished sending " << messages_.size() << " messages.";

          // Close the socket to the client.
          if (close(to_client_sock) == -1) {
            LOG(ERROR) << "Failed to close socket to client with error: "
                       << strerror(errno) << ".";
            continue;
          }
        }
      }));

  if (!handler_started.WaitForNotificationWithTimeout(absl::Seconds(10))) {
    return absl::InternalError(
        absl::StrCat("Failed to start request handler thread for '",
                     absolute_socket_path_, "'"));
  }

  return absl::OkStatus();
}

DomainSocketServer::~DomainSocketServer() {
  LOG(INFO) << "Shutting down DomainSocketServer on " << absolute_socket_path_;
  if (socket_fd_ != -1) {
    QCHECK_NE(shutdown(socket_fd_, SHUT_RDWR), -1)
        << "Failed to shutdown socket with error: " << strerror(errno) << ".";

    // Closing the socket stops the server loop.
    if (close(socket_fd_) == -1) {
      LOG(WARNING) << "Failed to close socket fd for '" << absolute_socket_path_
                   << "'. with error: " << strerror(errno) << ".";
    }
  }
  if (!absolute_socket_path_.empty()) {
    if (unlink(absolute_socket_path_.c_str()) == -1) {
      LOG(WARNING) << "Failed to unlink socket file '" << absolute_socket_path_
                   << "'. with error: " << strerror(errno) << ".";
    }
  }

  if (request_handler_ != nullptr && request_handler_->Joinable()) {
    request_handler_->RequestStop();
    request_handler_->Join();
  }

  if (const auto& status = UnlockPathCloseLockfile(flock_fd_); !status.ok()) {
    LOG(ERROR) << "Failed to unlock lock '" << absolute_lock_path_
               << "' for socket' " << absolute_socket_path_ << "': " << status;
  }
}

// static
absl::StatusOr<std::unique_ptr<DomainSocketServer>> DomainSocketServer::Create(
    absl::string_view socket_directory, absl::string_view module_name,
    absl::Duration lock_acquire_timeout, size_t protocol_version) {
  INTR_RETURN_IF_ERROR(
      domain_socket_internal::CreateSocketDirectory(socket_directory));

  std::string absolute_lock_path = LockName(socket_directory, module_name);
  INTR_ASSIGN_OR_RETURN(int flock_fd,
                        TryLockPath(absolute_lock_path, lock_acquire_timeout));

  absl::Cleanup clear_flock = [&flock_fd]() {
    if (const auto& status = UnlockPathCloseLockfile(flock_fd); !status.ok()) {
      LOG(ERROR) << "Failed to unlock flock with error: " << status;
    }
  };

  INTR_ASSIGN_OR_RETURN(std::string absolute_socket_path,
                        domain_socket_internal::AbsoluteSocketPath(
                            socket_directory, module_name));

  // A preexisting socket file needs to be unlinked before binding. This also
  // closes all connections of hypothetical clients.
  // https://gavv.net/articles/unix-socket-reuse/
  // Since we hold the lock, we know that nobody else is using this socket.
  if (file::Exists(absolute_socket_path, file::Defaults()).ok()) {
    LOG(INFO) << "Socket file '" << absolute_socket_path
              << "' already exists. Unlinking.";
    if (unlink(absolute_socket_path.data()) == -1) {
      return absl::InternalError(
          absl::StrCat("Failed to unlink socket file '", absolute_socket_path,
                       "'. with error: ", strerror(errno)));
    }
  }

  // Uses SOCK_STREAM (TCP) for connections, because it already supports
  // sessions. Otherwise we'd need to implement a simple handshake protocol.
  int socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);

  INTR_ASSIGN_OR_RETURN(
      sockaddr_un addr,
      domain_socket_internal::AddressFromAbsolutePath(absolute_socket_path));

  if (bind(socket_fd, (sockaddr*)&addr, sizeof(sockaddr_un)) == -1) {
    int savedErrno = errno;
    LOG(ERROR) << "Failed to bind to socket with error: "
               << strerror(savedErrno)
               << ". Cleaning up, then returning error.";
    if (close(socket_fd) == -1) {
      LOG(WARNING) << "Failed to close socket fd for '" << absolute_socket_path
                   << "'. with error: " << strerror(errno) << ".";
    };
    return absl::InternalError(
        absl::StrCat("Failed to bind socket file '", absolute_socket_path,
                     "'. with error: ", strerror(savedErrno)));
  }
  std::move(clear_flock).Cancel();

  return absl::WrapUnique(new DomainSocketServer(
      absolute_socket_path, absolute_lock_path,
      /*socket_fd=*/socket_fd,
      /*flock_fd=*/flock_fd, /*protocol_version=*/protocol_version));
}

}  // namespace intrinsic::icon
