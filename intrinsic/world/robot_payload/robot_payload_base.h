// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_BASE_H_
#define INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_BASE_H_

#include <ostream>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/proto/robot_payload.pb.h"

namespace intrinsic {

// Base class of the payload of a robot. It is read-only and real-time
// safe.
class RobotPayloadBase {
 public:
  RobotPayloadBase();

  // Mass of the robot payload. Unit is kg.
  double mass() const { return mass_kg_; }

  // Center of gravity of the robot payload relative to the robot flange/tip
  // frame.
  const Pose3d& tip_t_cog() const { return tip_t_cog_; }

  // 3x3 symmetric inertia matrix of the robot payload expressed about the
  // payloads center of mass. Unit is kg*m^2.
  const eigenmath::Matrix3d& inertia() const { return inertia_in_cog_; }

  bool operator==(const RobotPayloadBase& other) const;

 protected:
  // This constructor is protected to force the use of the factory method in the
  // derived class. The factory method ensures that the payload is valid.
  RobotPayloadBase(double mass, const Pose3d& tip_t_cog,
                   const eigenmath::Matrix3d& inertia);

  static bool MassAlmostEqual(double mass, double other_mass);

  double mass_kg_;
  Pose3d tip_t_cog_;
  eigenmath::Matrix3d inertia_in_cog_;
};

std::ostream& operator<<(std::ostream& os, const RobotPayloadBase& payload);

}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_BASE_H_
