// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/equipment/equipment_utils.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/equipment/channel_factory.h"
#include "intrinsic/icon/equipment/icon_equipment.pb.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_utils.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
namespace icon {

absl::StatusOr<IconEquipment> ConnectToIconEquipment(
    const skills::EquipmentPack& equipment_pack,
    absl::string_view equipment_slot, const ChannelFactory& channel_factory,
    absl::Duration timeout) {
  IconEquipment out;

  INTR_ASSIGN_OR_RETURN(auto handle, equipment_pack.GetHandle(equipment_slot));
  INTR_ASSIGN_OR_RETURN(const auto connection_config,
                        skills::GetConnectionParamsFromHandle(handle));
  auto maybe_position_part =
      equipment_pack.Unpack<intrinsic_proto::icon::Icon2PositionPart>(
          equipment_slot, kIcon2PositionPartKey);
  if (maybe_position_part.ok()) {
    out.position_part_name = maybe_position_part->part_name();
  }
  auto maybe_gripper_part =
      equipment_pack.Unpack<intrinsic_proto::icon::Icon2GripperPart>(
          equipment_slot, kIcon2GripperPartKey);
  if (maybe_gripper_part.ok()) {
    out.gripper_part_name = maybe_gripper_part->part_name();
  }
  auto maybe_adio_part =
      equipment_pack.Unpack<intrinsic_proto::icon::Icon2AdioPart>(
          equipment_slot, kIcon2AdioPartKey);
  if (maybe_adio_part.ok()) {
    if (!maybe_adio_part->has_icon_target()) {
      return absl::InvalidArgumentError(
          "ICON connection config for Adio Part does not specify an ICON "
          "target.");
    }
    out.adio_part_name = maybe_adio_part->icon_target().part_name();
  }
  auto maybe_force_torque_part =
      equipment_pack.Unpack<intrinsic_proto::icon::Icon2ForceTorqueSensorPart>(
          equipment_slot, kIcon2ForceTorqueSensorPartKey);
  if (maybe_force_torque_part.ok()) {
    out.force_torque_sensor_part_name = maybe_force_torque_part->part_name();
  }

  auto maybe_rangefinder_part =
      equipment_pack.Unpack<intrinsic_proto::icon::Icon2RangefinderPart>(
          equipment_slot, kIcon2RangefinderPartKey);
  if (maybe_rangefinder_part.ok()) {
    out.rangefinder_part_name = maybe_rangefinder_part->part_name();
  }

  INTR_ASSIGN_OR_RETURN(
      out.channel, channel_factory.MakeChannel(connection_config, timeout));

  return out;
}

intrinsic_proto::skills::ResourceSelector Icon2ResourceSelectorBuilder::Build()
    const {
  intrinsic_proto::skills::ResourceSelector selector;
  selector.add_capability_names(kIcon2ConnectionKey);
  if (position_part_) {
    selector.add_capability_names(kIcon2PositionPartKey);
  }
  if (gripper_part_) {
    selector.add_capability_names(kIcon2GripperPartKey);
  }
  if (adio_part_) {
    selector.add_capability_names(kIcon2AdioPartKey);
  }
  if (force_torque_sensor_part_) {
    selector.add_capability_names(kIcon2ForceTorqueSensorPartKey);
  }
  if (observation_stream_) {
    selector.add_capability_names(kIconRobotObservationStreamParamsKey);
  }
  if (rangefinder_part_) {
    selector.add_capability_names(kIcon2RangefinderPartKey);
  }
  return selector;
}

Icon2ResourceSelectorBuilder&
Icon2ResourceSelectorBuilder::WithPositionControlledPart() {
  position_part_ = true;
  return *this;
}

Icon2ResourceSelectorBuilder& Icon2ResourceSelectorBuilder::WithGripperPart() {
  gripper_part_ = true;
  return *this;
}

Icon2ResourceSelectorBuilder& Icon2ResourceSelectorBuilder::WithAdioPart() {
  adio_part_ = true;
  return *this;
}

Icon2ResourceSelectorBuilder&
Icon2ResourceSelectorBuilder::WithForceTorqueSensorPart() {
  force_torque_sensor_part_ = true;
  return *this;
}

Icon2ResourceSelectorBuilder&
Icon2ResourceSelectorBuilder::WithObservationStream() {
  observation_stream_ = true;
  return *this;
}

Icon2ResourceSelectorBuilder&
Icon2ResourceSelectorBuilder::WithRangefinderPart() {
  rangefinder_part_ = true;
  return *this;
}

}  // namespace icon
}  // namespace intrinsic
