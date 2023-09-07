// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SLOT_MAP_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SLOT_MAP_H_

#include <optional>
#include <utility>

#include "intrinsic/icon/control/c_api/c_realtime_slot_map.h"
#include "intrinsic/icon/control/c_api/c_rtcl_action.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_feature_interfaces.h"
#include "intrinsic/icon/control/slot_types.h"

namespace intrinsic::icon {

class IconRealtimeSlotMap {
 public:
  IconRealtimeSlotMap(XfaIconRealtimeSlotMap* realtime_slot_map,
                      XfaIconRealtimeSlotMapVtable realtime_slot_map_vtable,
                      XfaIconFeatureInterfaceVtable feature_interfaces_vtable)
      : realtime_slot_map_(realtime_slot_map),
        realtime_slot_map_vtable_(std::move(realtime_slot_map_vtable)),
        feature_interfaces_vtable_(std::move(feature_interfaces_vtable)) {}

  // Returns const FeatureInterfaces for `slot_id`.
  //
  // Returns a struct with all members set to std::nullopt for invalid
  // `slot_id`s.
  const IconConstFeatureInterfaces FeatureInterfacesForSlot(
      RealtimeSlotId slot_id) const;

  // Returns the FeatureInterfaces for `slot_id`.
  //
  // Returns a struct with all members set to std::nullopt for invalid
  // `slot_id`s.
  IconFeatureInterfaces MutableFeatureInterfacesForSlot(RealtimeSlotId slot_id);

 private:
  XfaIconRealtimeSlotMap* realtime_slot_map_ = nullptr;
  XfaIconRealtimeSlotMapVtable realtime_slot_map_vtable_;
  XfaIconFeatureInterfaceVtable feature_interfaces_vtable_;
};

class IconConstRealtimeSlotMap {
 public:
  IconConstRealtimeSlotMap(
      const XfaIconRealtimeSlotMap* realtime_slot_map,
      const XfaIconRealtimeSlotMapVtable realtime_slot_map_vtable,
      const XfaIconFeatureInterfaceVtable feature_interfaces_vtable)
      : realtime_slot_map_(realtime_slot_map),
        realtime_slot_map_vtable_(std::move(realtime_slot_map_vtable)),
        feature_interfaces_vtable_(std::move(feature_interfaces_vtable)) {}

  // Returns the FeatureInterfaces for `slot_id`.
  //
  // Returns a struct with all members set to std::nullopt for invalid
  // `slot_id`s.
  const IconConstFeatureInterfaces FeatureInterfacesForSlot(
      RealtimeSlotId slot_id) const;

 private:
  const XfaIconRealtimeSlotMap* realtime_slot_map_ = nullptr;
  const XfaIconRealtimeSlotMapVtable realtime_slot_map_vtable_;
  const XfaIconFeatureInterfaceVtable feature_interfaces_vtable_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SLOT_MAP_H_
