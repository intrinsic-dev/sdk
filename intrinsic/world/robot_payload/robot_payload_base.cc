// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/world/robot_payload/robot_payload_base.h"

#include <cstdlib>
#include <ostream>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/proto/robot_payload.pb.h"

namespace intrinsic {

RobotPayloadBase::RobotPayloadBase()
    : mass_kg_(0.0),
      tip_t_cog_(Pose3d::Identity()),
      inertia_in_cog_(eigenmath::Matrix3d::Zero()) {}

RobotPayloadBase::RobotPayloadBase(double mass, const Pose3d& tip_t_cog,
                                   const eigenmath::Matrix3d& inertia)
    : mass_kg_(mass), tip_t_cog_(tip_t_cog), inertia_in_cog_(inertia) {}

bool RobotPayloadBase::MassAlmostEqual(double mass, double other_mass) {
  return std::abs(mass - other_mass) <
         Eigen::NumTraits<double>::dummy_precision();
}

bool RobotPayloadBase::operator==(const RobotPayloadBase& other) const {
  return MassAlmostEqual(mass_kg_, other.mass_kg_) &&
         tip_t_cog_.isApprox(other.tip_t_cog_) &&
         inertia_in_cog_.isApprox(other.inertia_in_cog_);
}

std::ostream& operator<<(std::ostream& os, const RobotPayloadBase& payload) {
  os << "Payload: mass: " << payload.mass()
     << " tip_t_cog: " << payload.tip_t_cog()
     << " inertia: " << payload.inertia();
  return os;
}

}  // namespace intrinsic
