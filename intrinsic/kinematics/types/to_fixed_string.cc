// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/kinematics/types/to_fixed_string.h"

#include <ostream>

#include "absl/strings/string_view.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/utils/fixed_str_cat.h"
#include "intrinsic/icon/utils/fixed_string.h"
#include "intrinsic/kinematics/types/cartesian_limits.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/state_rn.h"
#include "intrinsic/math/pose3.h"

namespace intrinsic {

using icon::FixedStrCat;
using icon::FixedString;

namespace eigenmath {

// We use the eigenmath namespace to distinguish from ToFixedString(StateRnP)
// since StateRnP has an implicit constructor from VectorNd.
FixedString<kVectorNdStrSize> ToFixedString(const eigenmath::VectorNd& vec) {
  if (vec.size() == 0) {
    return {""};
  }

  FixedString<kVectorNdStrSize> str = FixedStrCat<kVectorNdStrSize>(vec[0]);
  for (size_t i = 1; i < vec.size(); ++i) {
    str = FixedStrCat<kVectorNdStrSize>(str, ",", vec[i]);
  }
  return str;
}

icon::FixedString<kPose3dStrSize> ToFixedString(const Pose3d& pose) {
  return FixedStrCat<kPose3dStrSize>(
      pose.translation().x(), ",", pose.translation().y(), ",",
      pose.translation().z(), ",", pose.quaternion().w(), ",",
      pose.quaternion().x(), ",", pose.quaternion().y(), ",",
      pose.quaternion().z());
}

}  // namespace eigenmath

FixedString<kStateStrSize> ToFixedString(const StateRnP& state) {
  return FixedStrCat<kStateStrSize>("p=",
                                    eigenmath::ToFixedString(state.position));
}

FixedString<kStateStrSize> ToFixedString(const StateRnV& state) {
  return FixedStrCat<kStateStrSize>("v=",
                                    eigenmath::ToFixedString(state.velocity));
}

FixedString<kStateStrSize> ToFixedString(const StateRnA& state) {
  return FixedStrCat<kStateStrSize>(
      "a=", eigenmath::ToFixedString(state.acceleration));
}

FixedString<kStateStrSize> ToFixedString(const StateRnJ& state) {
  return FixedStrCat<kStateStrSize>("j=", eigenmath::ToFixedString(state.jerk));
}

FixedString<kStateStrSize> ToFixedString(const StateRnT& state) {
  return FixedStrCat<kStateStrSize>("t=",
                                    eigenmath::ToFixedString(state.torque));
}

FixedString<2 * kStateStrSize> ToFixedString(const StateRnPV& state) {
  return FixedStrCat<2 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnP&>(state)), "\n",
      ToFixedString(static_cast<const StateRnV&>(state)));
}

FixedString<3 * kStateStrSize> ToFixedString(const StateRnPVA& state) {
  return FixedStrCat<3 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnPV&>(state)), "\n",
      ToFixedString(static_cast<const StateRnA&>(state)));
}

FixedString<3 * kStateStrSize> ToFixedString(const StateRnPVT& state) {
  return FixedStrCat<3 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnPV&>(state)), "\n",
      ToFixedString(static_cast<const StateRnT&>(state)));
}

FixedString<4 * kStateStrSize> ToFixedString(const StateRnPVAJ& state) {
  return FixedStrCat<4 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnPVA&>(state)), "\n",
      ToFixedString(static_cast<const StateRnJ&>(state)));
}

FixedString<4 * kStateStrSize> ToFixedString(const StateRnPVAT& state) {
  return FixedStrCat<4 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnPVA&>(state)), "\n",
      ToFixedString(static_cast<const StateRnT&>(state)));
}

FixedString<2 * kStateStrSize> ToFixedString(const StateRnVA& state) {
  return FixedStrCat<2 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnV&>(state)), "\n",
      ToFixedString(static_cast<const StateRnA&>(state)));
}

FixedString<3 * kStateStrSize> ToFixedString(const StateRnVAJ& state) {
  return FixedStrCat<3 * kStateStrSize>(
      ToFixedString(static_cast<const StateRnVA&>(state)), "\n",
      ToFixedString(static_cast<const StateRnJ&>(state)));
}

icon::FixedString<kLimitStrSize> ToFixedString(const JointLimits& limits) {
  return FixedStrCat<kLimitStrSize>(
      "min_p=", eigenmath::ToFixedString(limits.min_position),
      "\nmax_p=", eigenmath::ToFixedString(limits.max_position),
      "\nmax_v=", eigenmath::ToFixedString(limits.max_velocity),
      "\nmax_a=", eigenmath::ToFixedString(limits.max_acceleration),
      "\nmax_j=", eigenmath::ToFixedString(limits.max_jerk),
      "\nmax_t=", eigenmath::ToFixedString(limits.max_torque));
}

icon::FixedString<kCartLimitStrSize> ToFixedString(
    const CartesianLimits& limits) {
  return FixedStrCat<kCartLimitStrSize>(
      "min_p=", eigenmath::ToFixedString(limits.min_translational_position),
      "\nmax_p=", eigenmath::ToFixedString(limits.max_translational_position),
      "\nmin_v=", eigenmath::ToFixedString(limits.min_translational_velocity),
      "\nmax_v=", eigenmath::ToFixedString(limits.max_translational_velocity),
      "\nmin_a=",
      eigenmath::ToFixedString(limits.min_translational_acceleration),
      "\nmax_a=",
      eigenmath::ToFixedString(limits.max_translational_acceleration),
      "\nmin_j=", eigenmath::ToFixedString(limits.min_translational_jerk),
      "\nmax_j=", eigenmath::ToFixedString(limits.max_translational_jerk),
      "\nmax_rot_v=", limits.max_rotational_velocity,
      "\nmax_rot_a=", limits.max_rotational_acceleration,
      "\nmax_rot_j=", limits.max_rotational_jerk);
}

void PrintTo(const JointLimits& joint_limits, std::ostream* os) {
  *os << absl::string_view(ToFixedString(joint_limits));
}

void PrintTo(const StateRnP& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnV& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnA& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnJ& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnT& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnPV& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnPVA& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnPVT& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnPVAJ& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnPVAT& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnVA& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

void PrintTo(const StateRnVAJ& state, std::ostream* os) {
  *os << absl::string_view(ToFixedString(state));
}

}  // namespace intrinsic
