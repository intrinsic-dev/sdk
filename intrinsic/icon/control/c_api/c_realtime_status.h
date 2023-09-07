// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_STATUS_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_STATUS_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

const size_t kXfaIconRealtimeStatusMaxMessageLength = 100;
struct XfaIconRealtimeStatus {
  int status_code;
  // Message string. Not necessarily null-terminated, see `size`
  char message[kXfaIconRealtimeStatusMaxMessageLength];
  size_t size;
};

#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_STATUS_H_
