// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/kinematics/types/cartesian_limits.h"

#include <cmath>
#include <limits>

namespace intrinsic {

CartesianLimits::CartesianLimits() { SetUnlimited(); }

const CartesianLimits& CartesianLimits::Unlimited() {
  static const CartesianLimits* limits = []() {
    auto ret = new CartesianLimits();
    ret->SetUnlimited();
    return ret;
  }();
  return *limits;
}

void CartesianLimits::SetUnlimited() {
  min_translational_position.setConstant(
      -std::numeric_limits<double>::infinity());
  max_translational_position.setConstant(
      std::numeric_limits<double>::infinity());
  min_translational_velocity.setConstant(
      -std::numeric_limits<double>::infinity());
  max_translational_velocity.setConstant(
      std::numeric_limits<double>::infinity());
  min_translational_acceleration.setConstant(
      -std::numeric_limits<double>::infinity());
  max_translational_acceleration.setConstant(
      std::numeric_limits<double>::infinity());
  min_translational_jerk.setConstant(-std::numeric_limits<double>::infinity());
  max_translational_jerk.setConstant(std::numeric_limits<double>::infinity());
  max_rotational_velocity = std::numeric_limits<double>::infinity();
  max_rotational_acceleration = std::numeric_limits<double>::infinity();
  max_rotational_jerk = std::numeric_limits<double>::infinity();
}

bool CartesianLimits::IsValid() const {
  return (min_translational_position.array() <=
          max_translational_position.array())
             .all() &&
         (min_translational_velocity.array() <=
          max_translational_velocity.array())
             .all() &&
         (min_translational_acceleration.array() <=
          max_translational_acceleration.array())
             .all() &&
         (min_translational_jerk.array() <= max_translational_jerk.array())
             .all() &&
         (min_translational_velocity.array() <= 0).all() &&
         (max_translational_velocity.array() >= 0).all() &&
         (min_translational_acceleration.array() <= 0).all() &&
         (max_translational_acceleration.array() >= 0).all() &&
         (min_translational_jerk.array() <= 0).all() &&
         (max_translational_jerk.array() >= 0).all() &&
         max_rotational_velocity >= 0 && max_rotational_acceleration >= 0 &&
         max_rotational_jerk >= 0;
}

CartesianLimits CreateSimpleCartesianLimits(
    double max_translational_position, double max_translational_velocity,
    double max_translational_acceleration, double max_translational_jerk,
    double max_rotational_velocity, double max_rotational_acceleration,
    double max_rotational_jerk) {
  CartesianLimits limits;
  for (int i = 0; i < 3; ++i) {
    limits.min_translational_position[i] = -max_translational_position;
    limits.max_translational_position[i] = max_translational_position;
    limits.min_translational_velocity[i] = -max_translational_velocity;
    limits.max_translational_velocity[i] = max_translational_velocity;
    limits.min_translational_acceleration[i] = -max_translational_acceleration;
    limits.max_translational_acceleration[i] = max_translational_acceleration;
    limits.min_translational_jerk[i] = -max_translational_jerk;
    limits.max_translational_jerk[i] = max_translational_jerk;
  }
  limits.max_rotational_velocity = max_rotational_velocity;
  limits.max_rotational_acceleration = max_rotational_acceleration;
  limits.max_rotational_jerk = max_rotational_jerk;
  return limits;
}

namespace {

bool CompareDoubles(const double lhs, const double rhs) {
  if (std::isinf(lhs) && std::isinf(rhs)) return true;
  if (std::isnan(lhs) && std::isnan(rhs)) return true;
  return lhs == rhs;
}

bool CompareLimits(const eigenmath::Vector3d& lhs,
                   const eigenmath::Vector3d& rhs) {
  for (int i = 0; i < 3; ++i) {
    if (!CompareDoubles(lhs[i], rhs[i])) {
      return false;
    }
  }

  return true;
}

}  // namespace

bool CartesianLimits::operator==(const CartesianLimits& other) const {
  if (!CompareLimits(min_translational_position,
                     other.min_translational_position)) {
    return false;
  }
  if (!CompareLimits(max_translational_position,
                     other.max_translational_position)) {
    return false;
  }
  if (!CompareLimits(min_translational_velocity,
                     other.min_translational_velocity)) {
    return false;
  }
  if (!CompareLimits(max_translational_velocity,
                     other.max_translational_velocity)) {
    return false;
  }
  if (!CompareLimits(min_translational_acceleration,
                     other.min_translational_acceleration)) {
    return false;
  }
  if (!CompareLimits(max_translational_acceleration,
                     other.max_translational_acceleration)) {
    return false;
  }
  if (!CompareLimits(min_translational_jerk, other.min_translational_jerk)) {
    return false;
  }
  if (!CompareLimits(max_translational_jerk, other.max_translational_jerk)) {
    return false;
  }
  if (!CompareDoubles(max_rotational_velocity, other.max_rotational_velocity)) {
    return false;
  }
  if (!CompareDoubles(max_rotational_acceleration,
                      other.max_rotational_acceleration)) {
    return false;
  }
  if (!CompareDoubles(max_rotational_jerk, other.max_rotational_jerk)) {
    return false;
  }

  return true;
}

bool CartesianLimits::operator!=(const CartesianLimits& other) const {
  return !(*this == other);
}

}  // namespace intrinsic
