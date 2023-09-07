// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_PLATFORM_COMMON_BUFFERS_INTERNAL_EVENT_FD_H_
#define INTRINSIC_PLATFORM_COMMON_BUFFERS_INTERNAL_EVENT_FD_H_

#include <poll.h>

#include <cstdint>

namespace intrinsic {
namespace internal {

// Convenience class to wrap a linux event fd.
//
// For details on eventfd see the eventfd(2) man page
//
// EventFd should be initialized with the Init() methods before use.
class EventFd {
 public:
  EventFd() = default;
  ~EventFd();

  // Initializes the EventFd by allocating a new eventfd. Returns true on
  // success.
  bool Init();

  // Tests and clears the EventFd. Does a non-blocking test if the EventFd is
  // signaled and clears the signaled state. Returns true if the EventFd was
  // signaled.
  bool TestAndClear() const;

  // Signals the EventFd.
  void Signal() const;

  // Reads the associated filed descriptor using a non-blocking read. Returns
  // the count in the file descriptor, or returns zero on EAGAIN. Resets the
  // count to zero on a successful read.
  uint64_t Read() const;

  // Fills out a struct pollfd so the user can implement their own poll loop.
  // When this pollfd signals, the user should call testAndClear().
  void SetupPoll(struct pollfd& poll_fd) const;

 private:
  int fd_ = -1;
};

}  // namespace internal
}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_COMMON_BUFFERS_INTERNAL_EVENT_FD_H_
