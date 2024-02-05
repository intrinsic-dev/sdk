// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_EQUIPMENT_EQUIPMENT_UTILS_H_
#define INTRINSIC_ICON_EQUIPMENT_EQUIPMENT_UTILS_H_

#include <memory>
#include <optional>
#include <string>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "absl/types/optional.h"
#include "intrinsic/icon/equipment/channel_factory.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic {
namespace icon {

// Keys that identify ICON2 equipment in
// intrinsic/skills/proto/equipment.proto
constexpr char kIcon2ConnectionKey[] = "intrinsic_proto.icon.IconApi";
constexpr char kIcon2PositionPartKey[] = "Icon2PositionPart";
constexpr char kIcon2TorquePartKey[] = "Icon2TorquePart";
constexpr char kIcon2GripperPartKey[] = "Icon2GripperPart";
constexpr char kIcon2AdioPartKey[] = "Icon2AdioPart";
constexpr char kIcon2ForceTorqueSensorPartKey[] = "Icon2ForceTorqueSensorPart";
constexpr char kIcon2RangefinderPartKey[] = "Icon2RangefinderPart";
constexpr char kIconRobotObservationStreamParamsKey[] =
    "IconRobotObservationStreamParams";

// Combines a Channel (i.e. a connection to the ICON Application Layer)
// with additional equipment configuration parameters.
struct IconEquipment {
  std::shared_ptr<ChannelInterface> channel;
  std::optional<std::string> position_part_name;
  std::optional<std::string> torque_part_name;
  std::optional<std::string> gripper_part_name;
  std::optional<std::string> adio_part_name;
  std::optional<std::string> force_torque_sensor_part_name;
  std::optional<std::string> rangefinder_part_name;
};

// Connects to the ICON Application Layer equipment at `equipment_slot` in the
// `equipment_pack`, and extracts other relevant information (specifically the
// `arm_part_name`).
//
// Returns an error if the connection is not made within `timeout` of attempting
// to start the connection, or if the equipment configuration is malformed (ie.
// bad configuration type or slot name).
absl::StatusOr<IconEquipment> ConnectToIconEquipment(
    const skills::EquipmentPack& equipment_pack,
    absl::string_view equipment_slot, const ChannelFactory& channel_factory,
    absl::Duration timeout = kGrpcClientConnectDefaultTimeout);

class Icon2ResourceSelectorBuilder {
 public:
  intrinsic_proto::skills::ResourceSelector Build() const;

  Icon2ResourceSelectorBuilder& WithPositionControlledPart();

  Icon2ResourceSelectorBuilder& WithTorqueControlledPart();

  Icon2ResourceSelectorBuilder& WithGripperPart();

  Icon2ResourceSelectorBuilder& WithAdioPart();

  Icon2ResourceSelectorBuilder& WithForceTorqueSensorPart();

  Icon2ResourceSelectorBuilder& WithRangefinderPart();

  Icon2ResourceSelectorBuilder& WithObservationStream();

 private:
  bool position_part_ = false;
  bool torque_part_ = false;
  bool gripper_part_ = false;
  bool adio_part_ = false;
  bool force_torque_sensor_part_ = false;
  bool rangefinder_part_ = false;
  bool observation_stream_ = false;
};

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_EQUIPMENT_EQUIPMENT_UTILS_H_
