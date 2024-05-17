// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_
#define INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::kinematics {

// Validates that the link mass is positive.
icon::RealtimeStatus ValidateMass(double mass_kg);
// Validates that the link inertia expressed at the center of gravity is
// positive definite (symmetric and with positive eigenvalues) and that its
// eigenvalues fulfill the triangle inequalities.
icon::RealtimeStatus ValidateInertia(const eigenmath::Matrix3d& inertia);

}  // namespace intrinsic::kinematics

#endif  // INTRINSIC_KINEMATICS_VALIDATE_LINK_PARAMETERS_H_
