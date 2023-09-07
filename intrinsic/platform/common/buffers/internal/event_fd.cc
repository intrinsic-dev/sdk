// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/platform/common/buffers/internal/event_fd.h"

#include <poll.h>
#include <sys/eventfd.h>
#include <unistd.h>

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>

#include "absl/log/check.h"

namespace intrinsic {
namespace internal {

EventFd::~EventFd() {
  if (fd_ >= 0) {
    close(fd_);
  }
}

bool EventFd::Init() {
  if (fd_ >= 0) {
    return false;
  }

  fd_ = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK);

  return fd_ >= 0;
}

bool EventFd::TestAndClear() const {
  uint64_t val;
  int ret;

  ret = ::read(fd_, &val, sizeof(val));

  return ret == sizeof(val);
}

void EventFd::Signal() const {
  uint64_t val = 1;
  // The manual says that the write size must be 8 bytes.
  int e = write(fd_, &val, 8);
  if (e < 0) {
    perror("failed to signal event");
  }
}

void EventFd::SetupPoll(struct pollfd &poll_fd) const {
  poll_fd.fd = fd_;
  poll_fd.events = POLLIN;
  poll_fd.revents = 0;
}

uint64_t EventFd::Read() const {
  uint64_t count = 0;
  int ret = ::read(fd_, &count, sizeof(count));
  if (ret == -1 && errno == EAGAIN) {
    return 0;
  }

  CHECK(ret != -1) << "read() failed with errno value: "
                   << std::strerror(errno);

  return count;
}

}  // namespace internal
}  // namespace intrinsic
