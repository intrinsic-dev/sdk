// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_SLOT_TYPES_H_
#define INTRINSIC_ICON_CONTROL_SLOT_TYPES_H_

#include <cstdint>

#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/util/int_id.h"

namespace intrinsic::icon {

INTRINSIC_DEFINE_INT_ID_TYPE(RealtimeSlotId, int64_t);

struct SlotInfo {
  // Contains things like the supported FeatureInterfaceTypes, and (depending on
  // which types are supported) number of DoFs, maximum limits, etc.
  //
  // Actions may need this information in their Non-RT initialization routine.
  intrinsic_proto::icon::PartConfig config;
  // Action Factories should save this ID and use it to access this slot from
  // realtime functions.
  RealtimeSlotId slot_id;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_SLOT_TYPES_H_
