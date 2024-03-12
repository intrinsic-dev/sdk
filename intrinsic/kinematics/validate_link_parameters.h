// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_
#define INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_

#include "absl/status/status.h"
#include "intrinsic/eigenmath/types.h"

namespace intrinsic::kinematics {

// Validates that the link mass is positive.
absl::Status ValidateMass(double mass_kg);
// Validates that the link inertia expressed at the center of gravity is
// positive definite (symmetric and with positive eigenvalues) and that its
// eigenvalues fulfill the triangle inequalities.
absl::Status ValidateInertia(const eigenmath::Matrix3d& inertia);

}  // namespace intrinsic::kinematics

#endif  // INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_
