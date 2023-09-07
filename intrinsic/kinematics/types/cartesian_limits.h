// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_KINEMATICS_TYPES_CARTESIAN_LIMITS_H_
#define INTRINSIC_KINEMATICS_TYPES_CARTESIAN_LIMITS_H_

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {

// Holds Cartesian-space limits for translational position, velocity,
// acceleration and jerk, as well as rotational velocity, acceleration and jerk.
struct CartesianLimits {
 public:
  // Sets each limit range to (-infinity, infinity).
  void SetUnlimited();

  // Returns a shared instance for unlimited CartesianLimits. This is equivalent
  // to CartesianLimits().SetUnlimited() but allows us to share the instance.
  //
  // NOTE: This uses lazy but shared allocation, the first call will allocate on
  // the heap and all subsequent calls will share the instance.
  static const CartesianLimits& Unlimited();

  // Returns true if all limits are valid:
  // * For all min/max pairs: min < max
  // * For all values but position: min <= 0, max >= 0
  // * No special treatment for infinity (in particular, a CartesianLimits
  //   object is valid after calling SetUnlimited() on it!)
  bool IsValid() const;

  eigenmath::Vector3d min_translational_position = eigenmath::Vector3d::Zero();
  eigenmath::Vector3d max_translational_position = eigenmath::Vector3d::Zero();
  eigenmath::Vector3d min_translational_velocity = eigenmath::Vector3d::Zero();
  eigenmath::Vector3d max_translational_velocity = eigenmath::Vector3d::Zero();
  eigenmath::Vector3d min_translational_acceleration =
      eigenmath::Vector3d::Zero();
  eigenmath::Vector3d max_translational_acceleration =
      eigenmath::Vector3d::Zero();
  eigenmath::Vector3d min_translational_jerk = eigenmath::Vector3d::Zero();
  eigenmath::Vector3d max_translational_jerk = eigenmath::Vector3d::Zero();
  double max_rotational_velocity = 0.;
  double max_rotational_acceleration = 0.;
  double max_rotational_jerk = 0.;

  bool operator==(const CartesianLimits& other) const;
  bool operator!=(const CartesianLimits& other) const;
};

CartesianLimits CreateSimpleCartesianLimits(
    double max_translational_position, double max_translational_velocity,
    double max_translational_acceleration, double max_translational_jerk,
    double max_rotational_velocity, double max_rotational_acceleration,
    double max_rotational_jerk);

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_CARTESIAN_LIMITS_H_
