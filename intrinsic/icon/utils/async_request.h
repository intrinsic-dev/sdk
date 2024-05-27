// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_ASYNC_REQUEST_H_
#define INTRINSIC_ICON_UTILS_ASYNC_REQUEST_H_

#include <optional>
#include <utility>

#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/platform/common/buffers/rt_promise.h"

namespace intrinsic::icon {

// This movable request wraps a request and a promise.
// Used as communication channel between a non-rt async call and an rt thread.
// RequestDataType is the data type that should be passed from non-rt to rt.
// ResponseDataType is the data type used to convey the response from rt to
// non-rt. Both types must be movable.
//
// Example:
//
// NonRealtimeFuture<bool> rt_job_result;
// ASSIGN_OR_RETURN(auto promise, rt_job_result.GetPromise());
// AsyncRequest<int, bool> request(request_value, std::move(promise));

// Thread rt_thread;
// Thread::Options rt_thread_options;

// auto status = (rt_thread.Start(rt_thread_options,
//                    [request = std::move(request)]() mutable {
//   auto& actual_request_value = request.GetRequest();
//   // Do fancy real time stuff.
//   // ...
//   request.SetResponse(true);
// });
// INTR_RETURN_IF_ERROR(bool job_result, rt_job_result.Get());
// rt_thread.Join();
template <typename RequestDataType, typename ResponseDataType>
class AsyncRequest {
 public:
  // Default construction.
  AsyncRequest() = default;
  // Not copy constructable nor copy assignable.
  AsyncRequest(const AsyncRequest&) = delete;
  AsyncRequest& operator=(const AsyncRequest&) = delete;
  // Move constructable and move assignable.
  AsyncRequest(AsyncRequest&&) = default;
  AsyncRequest& operator=(AsyncRequest&&) = default;
  // Use this constructor when no reply is needed.
  explicit AsyncRequest(const RequestDataType& request) : request_(request) {}
  // Use this constructor to specify the `request` and the `promise` on which
  // the non-rt will wait with the corresponding future.
  AsyncRequest(const RequestDataType& request,
               RealtimePromise<ResponseDataType>&& promise)
      : request_(request), promise_(std::move(promise)) {}

  ~AsyncRequest() = default;

  // Returns the request.
  const RequestDataType& GetRequest() const& INTRINSIC_CHECK_REALTIME_SAFE {
    return request_;
  }
  // Returns a moved request. Use this function, when the request data is on the
  // heap and you need the request somewhere else. Do not copy the request data
  // when it is on the heap! Further calls to `GetRequest()` or
  // `GetMovedRequest()` will return an object in an unspecified state.
  RequestDataType&& GetMovedRequest() INTRINSIC_CHECK_REALTIME_SAFE {
    return std::move(request_);
  }

  // Returns if the promise (or its corresponding future) has been cancelled up
  // until now. Cancellation could still happen later.
  bool IsCancelled() const INTRINSIC_CHECK_REALTIME_SAFE {
    if (!promise_.has_value()) {
      return false;
    }
    auto is_cancelled = promise_->IsCancelled();
    if (!is_cancelled.ok()) {
      return false;
    }
    return is_cancelled.value();
  }

  // Sets the return status, which will be communicated through the promise
  // back to its corresponding future. Returns an error if setting the value
  // on the promise fails (i.e. due to cancellation). Returns OK, if default
  // constructed without promise.
  RealtimeStatus SetResponse(ResponseDataType reply)
      INTRINSIC_CHECK_REALTIME_SAFE {
    if (!promise_.has_value()) {
      // No need to set anything if we don't have a promise.
      return OkStatus();
    }
    return promise_->SetValue(reply);
  }

  // Cancels the promise and informs the corresponding future.
  icon::RealtimeStatus Cancel() INTRINSIC_CHECK_REALTIME_SAFE {
    if (!promise_.has_value()) {
      return icon::OkStatus();
    }
    return promise_->Cancel();
  }

 private:
  // The request value.
  RequestDataType request_;
  // The promise. Optional, in case there is no need for a reply.
  std::optional<RealtimePromise<ResponseDataType>> promise_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_ASYNC_REQUEST_H_
