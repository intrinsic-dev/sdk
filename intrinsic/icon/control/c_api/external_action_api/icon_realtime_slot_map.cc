// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/c_api/external_action_api/icon_realtime_slot_map.h"

#include "intrinsic/icon/control/c_api/c_realtime_slot_map.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_feature_interfaces.h"
#include "intrinsic/icon/control/slot_types.h"

namespace intrinsic::icon {

const IconConstFeatureInterfaces IconRealtimeSlotMap::FeatureInterfacesForSlot(
    RealtimeSlotId slot_id) const {
  auto feature_interfaces =
      realtime_slot_map_vtable_.get_feature_interfaces_for_slot(
          realtime_slot_map_, slot_id.value());
  return FromCApiFeatureInterfaces(feature_interfaces,
                                   feature_interfaces_vtable_);
}

IconFeatureInterfaces IconRealtimeSlotMap::MutableFeatureInterfacesForSlot(
    RealtimeSlotId slot_id) {
  auto feature_interfaces =
      realtime_slot_map_vtable_.get_mutable_feature_interfaces_for_slot(
          realtime_slot_map_, slot_id.value());
  return FromCApiFeatureInterfaces(feature_interfaces,
                                   feature_interfaces_vtable_);
}

const IconConstFeatureInterfaces
IconConstRealtimeSlotMap::FeatureInterfacesForSlot(
    RealtimeSlotId slot_id) const {
  auto feature_interfaces =
      realtime_slot_map_vtable_.get_feature_interfaces_for_slot(
          realtime_slot_map_, slot_id.value());
  return FromCApiFeatureInterfaces(feature_interfaces,
                                   feature_interfaces_vtable_);
}

}  // namespace intrinsic::icon
