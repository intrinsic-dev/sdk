// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SLOT_MAP_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SLOT_MAP_H_

#include <stdint.h>

#include "intrinsic/icon/control/c_api/c_feature_interfaces.h"

#ifdef __cplusplus
extern "C" {
#endif

struct XfaIconRealtimeSlotMap;

struct XfaIconRealtimeSlotMapVtable {
  XfaIconFeatureInterfacesForSlot (*get_mutable_feature_interfaces_for_slot)(
      XfaIconRealtimeSlotMap* self, uint64_t slot_id);
  XfaIconConstFeatureInterfacesForSlot (*get_feature_interfaces_for_slot)(
      const XfaIconRealtimeSlotMap* self, uint64_t slot_id);
};

#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_REALTIME_SLOT_MAP_H_
