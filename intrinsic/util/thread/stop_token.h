// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_
#define INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_

#include <atomic>
#include <memory>
#include <utility>

#include "absl/base/attributes.h"

namespace intrinsic {

namespace detail {

// Empty tag type intended for use as a placeholder in StopSource's non-default
// constructor, that makes the constructed StopSource empty with no
// associated stop-state
struct NoStopStateType {
  explicit NoStopStateType() = default;
};

// The corresponding constant object instance of NoStopStateType for use in
// constructing an empty StopSource, as a placeholder value in the non-default
// constructor.
inline constexpr NoStopStateType NoState{};

// The state of stop request which is shared between StopSource and StopToken.
struct StopState {
  std::atomic_bool stopped = false;

  // Requests a stop. Returns true if the stop was not already requested.
  bool request_stop() { return !stopped.exchange(true); }
};

using SharedStopState = std::shared_ptr<StopState>;

}  // namespace detail

// Token to be passed to long running threads to communicate cancellations,
// for example in context of deadlines or when the client cancels the request.
// Loosely follows std::stop_token terminology; The intent is to replace this
// class eventually by std::stop_token.
// This class is thread safe.
class StopToken {
 public:
  StopToken() : stop_state_(std::make_shared<detail::StopState>()) {}

  explicit StopToken(detail::SharedStopState state)
      : stop_state_(std::move(state)) {}

  bool request_stop() { return stop_state_->request_stop(); }

  ABSL_MUST_USE_RESULT bool stop_requested() const noexcept {
    return stop_state_ != nullptr && stop_state_->stopped;
  }

  ABSL_MUST_USE_RESULT bool stop_possible() const noexcept {
    return stop_state_ != nullptr;
  }

 private:
  detail::SharedStopState stop_state_ = nullptr;
};

class StopSource {
 public:
  explicit StopSource() : stop_state_(std::make_shared<detail::StopState>()) {}
  explicit StopSource(detail::NoStopStateType /*unused*/) noexcept {}

  StopSource(const StopSource& other) noexcept = default;
  StopSource(StopSource&& other) noexcept = default;

  bool request_stop() const noexcept {
    return stop_possible() && stop_state_->request_stop();
  }

  StopToken get_token() const noexcept { return StopToken(stop_state_); }

  bool stop_requested() const noexcept {
    return stop_state_ != nullptr && stop_state_->stopped;
  }

  bool stop_possible() const noexcept { return stop_state_ != nullptr; }

 private:
  detail::SharedStopState stop_state_ = nullptr;
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_
