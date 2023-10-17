// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/common/buffers/realtime_write_queue.h"

#include <poll.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdint>
#include <cstring>

#include "absl/log/log.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/platform/common/buffers/internal/event_fd.h"

namespace intrinsic::internal {

namespace {

bool HasPollinEvent(const struct pollfd& poll_fd) {
  return (poll_fd.revents & POLLIN) != 0;
}

}  // namespace

Events PollEvents(const EventFd& count_event_fd, const EventFd& closed_event_fd,
                  absl::Time deadline) {
  std::array<struct pollfd, 2> pollfds;
  count_event_fd.SetupPoll(pollfds[0]);
  closed_event_fd.SetupPoll(pollfds[1]);

  timespec timeout;
  timespec* timeout_ptr = nullptr;
  if (deadline != absl::InfiniteFuture()) {
    timeout = absl::ToTimespec(
        std::max(deadline - absl::Now(), absl::ZeroDuration()));
    timeout_ptr = &timeout;
  }
  // NB: ppoll(2) with nullptr sigmask for timeout precision
  int poll_result = ppoll(pollfds.data(), pollfds.size(), timeout_ptr, nullptr);
  Events events;
  if (poll_result == 0) {
    events.timedout = true;
    return events;
  }
  // If the poll was interrupted by a signal, simply report no events and carry
  // on.
  if (poll_result == -1 && errno == EINTR) {
    events.timedout = true;
    return events;
  }
  // NB: This can only happen due to an interrupt or inability to allocate
  // memory, or an internal error in  setting the args in this function.
  CHECK(poll_result != -1) << "Poll() failed with errno value: "
                           << std::strerror(errno);

  if (HasPollinEvent(pollfds[0])) {
    events.count = count_event_fd.Read();
  }

  if (HasPollinEvent(pollfds[1])) {
    (void)closed_event_fd.Read();
    events.closed = true;
  }

  return events;
}

}  // namespace intrinsic::internal
