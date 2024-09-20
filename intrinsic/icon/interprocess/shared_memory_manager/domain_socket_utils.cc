// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"

#include <sys/file.h>

#include <array>
#include <cerrno>
#include <cstddef>
#include <cstring>
#include <string>
#include <vector>

#include "absl/cleanup/cleanup.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_utils.h"
#include "intrinsic/util/status/status_macros.h"
#include "ortools/base/filesystem.h"
#include "ortools/base/options.h"
#include "ortools/base/path.h"

namespace intrinsic::icon {

namespace {

constexpr absl::string_view kDomainSocketDirectory = "/tmp/intrinsic_icon";

// Validates that the socket path fits into `sockaddr_un`.
absl::Status PathLengthIsValidForSockaddrUn(absl::string_view socket_path) {
  // sockaddr_un::sun_path requires a null terminator.
  const size_t kMaxSocketPathLength = sizeof(sockaddr_un::sun_path) - 1;
  if (socket_path.length() > kMaxSocketPathLength) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Socket path is too long. Got: ", socket_path, " with length ",
        socket_path.length(), ". Max length is ", kMaxSocketPathLength));
  }
  return absl::OkStatus();
}

// Closes socket on error.
absl::Status ConnectToServer(int to_server_sock,
                             absl::string_view absolute_socket_path,
                             absl ::Time deadline) {
  INTR_ASSIGN_OR_RETURN(
      sockaddr_un addr,
      domain_socket_internal::AddressFromAbsolutePath(absolute_socket_path));

  do {
    if (connect(to_server_sock, (sockaddr*)&addr, sizeof(sockaddr_un)) == 0) {
      LOG(INFO) << "Connected to server.";
      return absl::OkStatus();
    }

    LOG_FIRST_N(WARNING, 1)
        << "Failed to connect to socket '" << absolute_socket_path
        << "' with error: " << strerror(errno) << " Retrying until "
        << deadline;
    absl::SleepFor(absl::Seconds(1));
  } while (absl::Now() < deadline);
  LOG(ERROR) << "Failed to connect to socket before " << deadline
             << ". Cleaning up.";
  if (close(to_server_sock) == -1) {
    LOG(WARNING) << "Failed to close socket fd for '" << absolute_socket_path
                 << "' with error: " << strerror(errno) << ".";
  };

  return absl::DeadlineExceededError(
      absl::StrCat("Failed to connect to socket '", absolute_socket_path,
                   "' before ", deadline, "."));
}

}  // namespace

namespace domain_socket_internal {

absl::StatusOr<std::string> AbsoluteSocketPath(absl::string_view absolute_path,
                                               absl::string_view module_name) {
  if (!file::IsAbsolutePath(absolute_path)) {
    return absl::InvalidArgumentError(absl::StrCat(
        "The path `socket_directory` must be absolute. Got: ", absolute_path));
  }

  std::string full_socket_path =
      absl::StrCat(file::JoinPath(absolute_path, module_name),
                   domain_socket_internal::kSocketSuffix);

  INTR_RETURN_IF_ERROR(PathLengthIsValidForSockaddrUn(full_socket_path));
  return full_socket_path;
}

absl::Status CreateSocketDirectory(absl::string_view absolute_path) {
  if (!file::IsAbsolutePath(absolute_path)) {
    return absl::InvalidArgumentError(absl::StrCat(
        "The path `socket_directory` must be absolute. Got: ", absolute_path));
  }

  INTR_RETURN_IF_ERROR(
      file::RecursivelyCreateDir(absolute_path, file::Defaults()));

  return absl::OkStatus();
}

absl::StatusOr<sockaddr_un> AddressFromAbsolutePath(
    absl::string_view absolute_socket_path) {
  sockaddr_un addr;
  memset(&addr, 0, sizeof(struct sockaddr_un));
  addr.sun_family = AF_UNIX;

  INTR_RETURN_IF_ERROR(PathLengthIsValidForSockaddrUn(absolute_socket_path));
  // SNPrintF always includes the null terminator as required by
  // sockaddr_un::sun_path.
  if (absl::SNPrintF(addr.sun_path, sizeof(addr.sun_path), "%s",
                     absolute_socket_path) < 0) {
    return absl::InternalError(
        absl::StrCat("Failed to copy socket path '", absolute_socket_path,
                     "' to addr. With error: ", strerror(errno)));
  }
  return addr;
}

}  // namespace domain_socket_internal

// Receives a single message from the open socket `to_server_sock`.
// Returns InternalError if a received file descriptor is not valid.
// Returns InternalError on parsing errors.
// Returns InternalError when the size of the received message is wrong.
// Returns FailedPreconditionError when the socket protocol version of the
// message doesn't match domain_socket_internal::kDomainSocketProtocolVersion.
absl::StatusOr<domain_socket_internal::ShmDescriptors> GetSingleMessage(
    int to_server_sock) {
  domain_socket_internal::ShmDescriptors descriptors;
  descriptors.file_descriptors_in_order.reserve(
      domain_socket_internal::kMaxFdsPerMessage);

  constexpr size_t kExpectedBytes = sizeof(descriptors.transfer_data);

  // Allocates size for the max number of fds.
  std::array<char, CMSG_SPACE(domain_socket_internal::kMaxFdsPerMessage *
                              sizeof(int))>
      cmsg_buf{0};

  iovec iov{.iov_base = (char*)(&descriptors.transfer_data),
            .iov_len = kExpectedBytes};

  msghdr msgh{
      .msg_name = nullptr, .msg_namelen = 0, .msg_iov = &iov, .msg_iovlen = 1};

  // ancillary data = file descriptors.
  msgh.msg_control = cmsg_buf.data();
  msgh.msg_controllen = cmsg_buf.size();

  // Copy of the first message header, with the pointer to the ancillary data
  // that contains the file descriptors.
  msghdr first_msghdr = msgh;
  size_t received_bytes_sum = 0;

  // Receiving a single message can require multiple calls to recvmsg
  // https://gist.github.com/kentonv/bc7592af98c68ba2738f4436920868dc
  while (received_bytes_sum < kExpectedBytes) {
    if (received_bytes_sum > 0) {
      // recvmsg() transmits the control message (which contains the file
      // descriptors) on the first call. For subsequent calls, we set the
      // msg_control and msg_controllen fields of msgh to zero so recvmsg() does
      // not overwrite the control message.
      //
      // Because we made a copy of msgh before the loop, we can still access the
      // control message later.
      msgh.msg_control = nullptr;
      msgh.msg_controllen = 0;
    }

    // Returns the number of bytes received.
    ssize_t received_bytes = recvmsg(to_server_sock, &msgh, 0);
    if (received_bytes == -1) {
      return absl::InternalError(absl::StrCat(
          "Failed to receive data with error: ", strerror(errno), "."));
    }

    if (received_bytes == 0) {
      return absl::InternalError("No data received. Likely due to shutdown.");
    }

    received_bytes_sum += received_bytes;
    if ((received_bytes_sum) > kExpectedBytes) {
      return absl::OutOfRangeError(
          absl::StrCat("Received ", (received_bytes_sum),
                       " bytes, but only expected ", kExpectedBytes, " bytes"));
    }

    msgh.msg_iov->iov_base =
        (char*)(&descriptors.transfer_data) + received_bytes_sum;
    msgh.msg_iov->iov_len = kExpectedBytes - received_bytes_sum;
  }

  // // Returns error instead of retrying because the data is transmitted as a
  // // single message.
  if (received_bytes_sum != kExpectedBytes) {
    return absl::InternalError(absl::StrCat("Received ", received_bytes_sum,
                                            " bytes. Expected [",
                                            kExpectedBytes, "]."));
  }

  if (descriptors.transfer_data.domain_socket_protocol_version !=
      domain_socket_internal::kDomainSocketProtocolVersion) {
    return absl::FailedPreconditionError(absl::StrCat(
        "Incompatible domain socket protocol version. Got: ",
        descriptors.transfer_data.domain_socket_protocol_version, " expected: ",
        domain_socket_internal::kDomainSocketProtocolVersion, "."));
  }

  const int kNumNames = descriptors.transfer_data.file_descriptor_names.size();
  const auto segment_names = GetNamesFromFileDescriptorNames(
      descriptors.transfer_data.file_descriptor_names);

  // Parses fd data.
  struct cmsghdr* cmsg = CMSG_FIRSTHDR(&first_msghdr);
  if (!cmsg) {
    return absl::InternalError("No control message received.");
  }

  if (cmsg->cmsg_len != CMSG_LEN(kNumNames * sizeof(int))) {
    return absl::InternalError(absl::StrCat(
        "Control message has wrong size. Expected [",
        CMSG_LEN(kNumNames * sizeof(int)), "] got [", cmsg->cmsg_len, "]."));
  }

  if (cmsg->cmsg_level != SOL_SOCKET) {
    return absl::InternalError(
        absl::StrCat("Control message has wrong level. Expected [", SOL_SOCKET,
                     "] got [", cmsg->cmsg_level, "]."));
  }
  if (cmsg->cmsg_type != SCM_RIGHTS) {
    return absl::InternalError(
        absl::StrCat("Control message has wrong type. Expected [", SCM_RIGHTS,
                     "] got [", cmsg->cmsg_type, "]."));
  }
  descriptors.file_descriptors_in_order.resize(kNumNames);
  // https://man7.org/linux/man-pages/man7/unix.7.html
  // If the number of file descriptors received in the ancillary data cause
  // the process to exceed its RLIMIT_NOFILE resource limit, the excess file
  // descriptors are automatically closed in the receiving process. One cannot
  // split the list over multiple recvmsg calls.
  for (int i = 0; i < kNumNames; ++i) {
    int fd = reinterpret_cast<int*>(CMSG_DATA(cmsg))[i];
    if (fcntl(fd, F_GETFD) == -1) {
      return absl::InternalError(absl::StrCat(
          "File descriptor for segment '", segment_names[i],
          "' is not valid. Either the receiving process can't open any more "
          "files, or the server sent a closed file descriptor. Error: ",
          strerror(errno), "."));
    }

    descriptors.file_descriptors_in_order[i] = fd;
  }

  LOG(INFO) << "Received " << kNumNames << " valid file descriptors in message "
            << descriptors.transfer_data.message_index << " of "
            << descriptors.transfer_data.num_messages << ".";

  return descriptors;
}

absl::StatusOr<SegmentNameToFileDescriptorMap>
GetSegmentNameToFileDescriptorMap(absl::string_view socket_directory,
                                  absl::string_view module_name,
                                  absl::Duration connection_timeout) {
  absl::Time deadline = absl::Now() + connection_timeout;
  int to_server_sock = socket(AF_UNIX, SOCK_STREAM, 0);
  if (to_server_sock == -1) {
    return absl::InternalError(absl::StrCat(
        "Failed to create GetShmDescriptors client socket with error: ",
        strerror(errno), "."));
  }

  INTR_RETURN_IF_ERROR(
      domain_socket_internal::CreateSocketDirectory(socket_directory));

  INTR_ASSIGN_OR_RETURN(std::string absolute_socket_path,
                        domain_socket_internal::AbsoluteSocketPath(
                            socket_directory, module_name));

  INTR_RETURN_IF_ERROR(
      ConnectToServer(to_server_sock, absolute_socket_path, deadline));

  // Closes the socket on exit
  absl::Cleanup close_socket = [to_server_sock]() {
    if (close(to_server_sock) == -1) {
      LOG(ERROR)
          << "Failed to close GetShmDescriptors client socket with error: "
          << strerror(errno) << ".";
    }
  };

  // The socket blocks at most for one Second if no data is received.
  // This stops a misbehaving server from doing damage.
  struct timeval socket_receive_timeout = absl::ToTimeval(absl::Seconds(1));
  if (setsockopt(to_server_sock, SOL_SOCKET, SO_RCVTIMEO,
                 (const char*)&socket_receive_timeout,
                 sizeof socket_receive_timeout) == -1) {
    return absl::InternalError(absl::StrCat(
        "Failed to set socket timeout with error: ", strerror(errno), "."));
  }

  SegmentNameToFileDescriptorMap segment_name_to_file_descriptor_map;
  // Reserves enough data for at least one message.
  // Reserves more data below once we know how many messages are expected.
  segment_name_to_file_descriptor_map.reserve(
      domain_socket_internal::kMaxFdsPerMessage);

  size_t remaining_messages = 0;
  size_t expected_message_index = 1;
  size_t expected_num_messages = 0;
  do {
    INTR_ASSIGN_OR_RETURN(const auto message, GetSingleMessage(to_server_sock));

    if (expected_message_index != message.transfer_data.message_index) {
      return absl::InternalError(
          absl::StrCat("Expected message with index ", expected_message_index,
                       " got ", message.transfer_data.message_index));
    }
    // Reserve the correct space after receiving the first message.
    if (expected_message_index == 1) {
      expected_num_messages = message.transfer_data.num_messages;

      segment_name_to_file_descriptor_map.reserve(
          domain_socket_internal::kMaxFdsPerMessage * expected_num_messages);
    }

    if (expected_num_messages != message.transfer_data.num_messages) {
      return absl::FailedPreconditionError(absl::StrCat(
          "Expected ", expected_num_messages, " messages, but message (",
          message.transfer_data.message_index, ") declares ",
          message.transfer_data.num_messages, "."));
    }
    remaining_messages = expected_num_messages - expected_message_index;
    expected_message_index++;

    std::vector<std::string> names = GetNamesFromFileDescriptorNames(
        message.transfer_data.file_descriptor_names);

    if (names.size() != message.file_descriptors_in_order.size()) {
      return absl::FailedPreconditionError(
          absl::StrCat("Names and file descriptors have different sizes. Got: ",
                       names.size(), " and ",
                       message.file_descriptors_in_order.size(), "."));
    }

    for (int i = 0; i < names.size(); ++i) {
      segment_name_to_file_descriptor_map[names.at(i)] =
          message.file_descriptors_in_order[i];
    }
  } while (remaining_messages > 0);

  return segment_name_to_file_descriptor_map;
}

std::string SocketDirectoryFromNamespace(
    absl::string_view shared_memory_namespace) {
  return file::JoinPath(kDomainSocketDirectory, shared_memory_namespace);
}

}  // namespace intrinsic::icon
