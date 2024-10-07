// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_REALTIME_SIGNAL_TYPES_H_
#define INTRINSIC_ICON_CONTROL_REALTIME_SIGNAL_TYPES_H_

#include <cstdint>

#include "intrinsic/production/external/intops/strong_int.h"

namespace intrinsic::icon {

// Identifier for a Real-time Signal.
DEFINE_STRONG_INT_TYPE(RealtimeSignalId, int64_t);

// Hold both the current and previous signal value, to allow easy querying of
// rising edges.
struct SignalValue {
  bool current_value = false;
  bool previous_value = false;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_REALTIME_SIGNAL_TYPES_H_
