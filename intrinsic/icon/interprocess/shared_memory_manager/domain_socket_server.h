// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_DOMAIN_SOCKET_SERVER_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_DOMAIN_SOCKET_SERVER_H_

#include <cstddef>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {

// Allows sharing file descriptors across process boundaries using a UNIX Domain
// Socket.
// It is intended to be used by developers of ICON and the hardware abstraction
// layer for sharing anonymous memory segments of the hardware abstraction
// layer, but is not limited to that use case.
//
// Recommended reading list before adjusting this class:
// * https://medium.com/swlh/getting-started-with-unix-domain-sockets-4472c0db4eb1
// * https://man7.org/linux/man-pages/man2/accept.2.html
// * https://linux.die.net/man/2/sendmsg
// * https://linux.die.net/man/2/recvmsg
// * https://gist.github.com/kentonv/bc7592af98c68ba2738f4436920868dc
// * https://linux.die.net/man/1/flock
// * https://linux.die.net/man/2/setrlimit
//
// The connection uses a very simple protocol and version check.
// `domain_socket_internal::kDomainSocketProtocolVersion` must be updated on
// protocol changes.
//
// Expected usage:
//
// 1. Create a DomainSocketServer to lock the name of the socket file.
// 2. Open / Create the (anonymous) files that should be shared.
// 3. Call ServeShmDescriptors(...) to start serving the file descriptors.
// 4. Clients call GetSegmentNameToFileDescriptorMap(...) to receive the file
// descriptors. See
// intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h
// 5. Delete the server to release the lock and socket.
//
// The file descriptors that you pass to ServeShmDescriptors() must remain open
// for the lifetime of DomainSocketServer.
// However, DomainSocketServer does not take ownership of the file descriptors.
// You are still responsible for closing them.
// Closing file descriptors shared via DomainSocketServer does not close the
// file descriptors that were already received by clients in other processes.
//
// The socket is locked via flock (https://linux.die.net/man/1/flock) using a
// separate lock file to ensure that only one server is active at a time.
//
class DomainSocketServer {
 public:
  static constexpr absl::Duration kDefaultLockAcquireTimeout =
      absl::ZeroDuration();

  // Creates a DomainSocketServer that serves file descriptors across process
  // boundaries using a UNIX Domain Socket.
  // The newly created server holds a lock on the socket, but is not yet
  // serving any file descriptors.
  // Creates the paths to the socket and lock file based on `socket_directory`
  // and `module_name`.
  // Recursively creates the socket directory if it doesn't exist.
  // The parameter `protocol_version` allows overriding the protocol version for
  // testing purposes.
  //
  // Returns DeadlineExceededError if the lock can't be acquired within
  // `lock_acquire_timeout`.
  // Returns InvalidArgumentError if `socket_directory` is not an absolute path.
  // Returns InvalidArgumentError if the generated socket path is too long.
  // Returns InternalError on file handling errors.
  // Returns a unique_ptr on success. The return value is not a bare
  // DomainSocketServer instance, because other classes regularly hold
  // references to DomainSocketServer, and moving a bare DomainSocketServer
  // would invalidate those references.
  static absl::StatusOr<std::unique_ptr<DomainSocketServer>> Create(
      absl::string_view socket_directory, absl::string_view module_name,
      absl::Duration lock_acquire_timeout,
      size_t protocol_version =
          domain_socket_internal::kDomainSocketProtocolVersion);

  // Closes and unlinks the server socket.
  // Releases the lock.
  // Blocks while joining the server thread.
  ~DomainSocketServer();

  // Starts the server and serves the provided descriptors in the background.
  //
  // While RLIMIT_NOFILE defines the absolute limit of file descriptors that can
  // be shared, anything above a few thousand is untested.
  // Note: [RLIMIT_NOFILE] specifies a value one greater than the maximum file
  // descriptor number that can be opened by this process.
  // https://www.man7.org/linux/man-pages/man2/getrlimit.2.html
  //
  // Returns FailedPreconditionError if the server is already serving.
  // Returns InvalidArgumentError if `segment_name_to_file_descriptor_map` is
  // empty.
  // Returns InvalidArgumentError if the number of file descriptors is larger
  // than RLIMIT_NOFILE.
  // The file descriptors must not be closed until all clients have received
  // them.
  absl::Status ServeShmDescriptors(const SegmentNameToFileDescriptorMap&
                                       segment_name_to_file_descriptor_map);

  // Adds the special Segment `SegmentInfo` to the `shared_memory_manager` and
  // starts the server to serve the file descriptors for all segments previously
  // added to `shared_memory_manager`.
  // Any segments added to `shared_memory_manager` after this call will not be
  // served.
  absl::Status AddSegmentInfoServeShmDescriptors(
      SharedMemoryManager& shared_memory_manager);

 private:
  // Contains all the data that is sent over the socket.
  // An initialized Message must not be copied or moved, because `msgh`
  // contains pointers to data in the other members, `iov` holds a pointer to
  // descriptors.transfer_data. Changing `cmsg_buf` can invalidate pointers.
  struct Message {
    domain_socket_internal::ShmDescriptors descriptors;
    iovec iov;
    msghdr msgh;
    std::vector<char> cmsg_buf;
  };

  DomainSocketServer(absl::string_view absolute_socket_path,
                     absl::string_view absolute_lock_path, int socket_fd,
                     int flock_fd, size_t protocol_version)
      : protocol_version_(protocol_version),
        socket_fd_(socket_fd),
        flock_fd_(flock_fd),
        absolute_socket_path_(absolute_socket_path),
        absolute_lock_path_(absolute_lock_path) {}

  // Creates a self contained message that can be sent over the socket.
  //
  // `message_index` is the index of the current message starting at one.
  // `num_messages` is the number of messages.
  // Examples:
  //   One message:
  //     * message_index = 1, num_messages = 1
  //   Two messages:
  //     * message_index = 1, num_messages = 2
  //     * message_index = 2, num_messages = 2
  //
  // Returns a unique_ptr to ensure pointer stability within the generated
  // message.
  // Returns OutOfRangeError when message_index, or num_messages are invalid.
  // Returns InternalError when creating the message fails.
  absl::StatusOr<std::unique_ptr<const Message>> PrepareMessage(
      size_t message_index, size_t num_messages,
      const domain_socket_internal::ShmDescriptors& descriptors);

  // Creates a vector of self contained messages that can be sent over the
  // socket.
  // Splits the contents of `segment_name_to_file_descriptor_map` as required.
  absl::StatusOr<std::vector<std::unique_ptr<const Message>>> PrepareMessages(
      const SegmentNameToFileDescriptorMap&
          segment_name_to_file_descriptor_map);

  size_t protocol_version_;
  int socket_fd_ = -1;
  int flock_fd_ = -1;
  std::vector<std::unique_ptr<const Message>> messages_;
  std::string absolute_socket_path_ = "";
  // Absolute path to the lock file. Only required for logging.
  std::string absolute_lock_path_ = "";

  std::string module_name_;
  std::string shared_memory_namespace_;

  std::unique_ptr<intrinsic::Thread> request_handler_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_DOMAIN_SOCKET_SERVER_H_
