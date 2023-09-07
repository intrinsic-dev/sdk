// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_ACTIONS_TARE_FORCE_TORQUE_SENSOR_INFO_H_
#define INTRINSIC_ICON_ACTIONS_TARE_FORCE_TORQUE_SENSOR_INFO_H_

#include "intrinsic/icon/actions/tare_force_torque_sensor.pb.h"

namespace intrinsic {
namespace icon {

struct TareForceTorqueSensorInfo {
  static constexpr char kActionTypeName[] = "xfa.tare_force_torque_sensor";
  static constexpr char kActionDescription[] =
      "Resets the force-torque sensor bias under the assumption that no forces "
      "or torques are applied to the sensor, other than those resulting from "
      "the attached tool. The saved bias will subsequently be subtracted from "
      "all sensor readings, which means that the sensor readings are "
      "'calibrated' around the setpoint for which the bias was stored. "
      "Modelled post-sensor inertia (or configured payload) is not affected by "
      "the taring step. Run this Action before calling the "
      "CartesianAdmittanceAction or other compliance control Actions that "
      "involve a force-torque sensor.";

  static constexpr char kForceTorqueSensorSlotName[] = "ft_sensor";
  static constexpr char kForceTorqueSensorSlotDescription[] =
      "After the Action reports it is done, the sensor represented by this "
      "Part is finished taring.";

  using FixedParams = xfa::icon::actions::proto::TareForceTorqueSensorParams;
};

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_ACTIONS_TARE_FORCE_TORQUE_SENSOR_INFO_H_
