// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_
#define INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_

#include <atomic>

#include "absl/base/attributes.h"

namespace intrinsic::longrunning {

// Token to be passed to long running threads to communicate cancellations,
// for example in context of deadlines or when the client cancels the request.
// Loosely follows std::stop_token terminology; The intent is to replace this
// class eventually by std::stop_token.
// This class is thread safe.
class StopToken {
 public:
  void request_stop() { stopped_ = true; }
  ABSL_MUST_USE_RESULT bool stop_requested() const { return stopped_; }

 private:
  std::atomic_bool stopped_ = false;
};

}  // namespace intrinsic::longrunning

#endif  // INTRINSIC_UTIL_THREAD_STOP_TOKEN_H_
