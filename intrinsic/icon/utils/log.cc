// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/log.h"

#include <memory>

#include "intrinsic/icon/utils/log_internal.h"
#include "intrinsic/icon/utils/realtime_log_sink.h"

namespace intrinsic {

void RtLogInitForThisThread() {
  intrinsic::icon::GlobalLogContext::SetThreadLocalLogSink(
      std::make_unique<intrinsic::icon::RealtimeLogSink>());
}

}  // namespace intrinsic
