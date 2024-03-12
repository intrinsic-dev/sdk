// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_H_
#define INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_H_

#include <ostream>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/proto/robot_payload.pb.h"

namespace intrinsic {

// Dynamic payload of a robot.
class RobotPayload {
 public:
  RobotPayload();

  // Creates a Payload from the given parameters. Fails if parameters are
  // invalid.
  static absl::StatusOr<RobotPayload> Create(
      double mass_kg, const Pose3d& tip_t_cog,
      const eigenmath::Matrix3d& inertia);

  // Sets the mass of the robot payload. Unit is kg.
  absl::Status SetMass(double mass_kg);

  // Mass of the robot payload. Unit is kg.
  double mass() const { return mass_kg_; }

  // Set the center of gravity.
  absl::Status SetTipTCog(const Pose3d& tip_t_cog);

  // Center of gravity of the robot payload relative to the robot flange/tip
  // frame.
  const Pose3d& tip_t_cog() const { return tip_t_cog_; }

  // Sets the inertia matrix expressed about the payloads center of mass. Unit
  // is kg*m^2.
  absl::Status SetInertia(const eigenmath::Matrix3d& inertia);

  // 3x3 symmetric inertia matrix of the robot payload expressed about the
  // payloads center of mass. Unit is kg*m^2.
  const eigenmath::Matrix3d& inertia() const { return inertia_in_cog_; }

  bool operator==(const RobotPayload& other) const;

 private:
  RobotPayload(double mass, const Pose3d& tip_t_cog,
               const eigenmath::Matrix3d& inertia);

  double mass_kg_;
  Pose3d tip_t_cog_;
  eigenmath::Matrix3d inertia_in_cog_;
};

std::ostream& operator<<(std::ostream& os, const RobotPayload& payload);

// Converts a payload proto to a Payload. Fails for invalid parameters. Sets
// empty mass to 0 kg, empty tip_t_cog to the identity transform and an empty
// inertia to a 3x3 zero matrix.
absl::StatusOr<RobotPayload> FromProto(
    const intrinsic_proto::world::RobotPayload& proto);

// Converts a Payload to a payload proto.
intrinsic_proto::world::RobotPayload ToProto(const RobotPayload& payload);

}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_ROBOT_PAYLOAD_ROBOT_PAYLOAD_H_
