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

class StopSource;

// Token to be passed to threads to communicate cancellations, for example in
// context of deadlines or when the client cancels the request. Follows
// std::stop_token semantics and API; The intent is to replace this class
// eventually by std::stop_token. This class is thread safe.
class StopToken {
 public:
  // Constructs an empty StopToken with no associated stop-state.
  StopToken() noexcept = default;

  // Default copy and move constructors.
  StopToken(const StopToken& other) noexcept = default;
  StopToken(StopToken&& other) noexcept = default;

  ABSL_MUST_USE_RESULT bool stop_requested() const noexcept {
    return stop_state_ != nullptr && stop_state_->stopped;
  }

  ABSL_MUST_USE_RESULT bool stop_possible() const noexcept {
    return stop_state_ != nullptr;
  }

 private:
  // Required to make the constructor below private.
  friend class StopSource;

  // Constructs a StopToken with the given stop-state.
  explicit StopToken(detail::SharedStopState state)
      : stop_state_(std::move(state)) {}

  detail::SharedStopState stop_state_ = nullptr;
};

// Source of StopTokens and the interface to request a stop.
class StopSource {
 public:
  // Constructs a StopSource with new stop-state.
  explicit StopSource() : stop_state_(std::make_shared<detail::StopState>()) {}

  // Constructs an empty StopSource with no associated stop-state.
  explicit StopSource(detail::NoStopStateType /*unused*/) noexcept {}

  // Default copy and move constructors.
  StopSource(const StopSource& other) noexcept = default;
  StopSource(StopSource&& other) noexcept = default;

  StopSource& operator=(StopSource&& other) noexcept = default;

  // Issues a stop request to the stop-state, if the stop_source object has a
  // stop-state and it has not yet already had stop requested.
  bool request_stop() const noexcept {
    return stop_possible() && stop_state_->request_stop();
  }

  // Returns a StopToken object, which will be empty if stop_possible() ==
  // false.
  StopToken get_token() const noexcept { return StopToken(stop_state_); }

  // Checks whether the associated stop-state has been requested to stop.
  ABSL_MUST_USE_RESULT bool stop_requested() const noexcept {
    return stop_state_ != nullptr && stop_state_->stopped;
  }

  // Checks whether associated stop-state can be requested to stop.
  // If the StopSource object has a stop-state and a stop request has already
  // been made, this function still returns true.
  ABSL_MUST_USE_RESULT bool stop_possible() const noexcept {
    return stop_state_ != nullptr;
  }

 private:
  detail::SharedStopState stop_state_ = nullptr;
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_
