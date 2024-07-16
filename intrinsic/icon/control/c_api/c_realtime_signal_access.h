// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SIGNAL_ACCESS_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SIGNAL_ACCESS_H_

#include <stdint.h>

#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_types.h"

#ifdef __cplusplus
extern "C" {
#endif

struct XfaIconRealtimeSignalAccess;

struct XfaIconRealtimeSignalAccessVtable {
  XfaIconRealtimeStatus (*read_signal)(XfaIconRealtimeSignalAccess* self,
                                       uint64_t id,
                                       XfaIconSignalValue* signal_value);
};

#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SIGNAL_ACCESS_H_
