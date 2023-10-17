// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_CONSTANTS_H_
#define INTRINSIC_ICON_UTILS_CONSTANTS_H_

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {

constexpr double kDefaultGravity = 9.81;  // [kg /(m*s^2)]

// Expresses the default gravity constant as vector in a Cartesian coordinate
// system in which the z-axis points upwards. The gravity vector points
// downwards.
// Note: keep the 'inline'. According to the C++17 standard, inlined variables
// and functions will default to external linkage, and an inline variable with
// external linkage will have the same address in all translation units.
inline const eigenmath::Vector3d kDefaultGravityVector{0.0, 0.0,
                                                       -kDefaultGravity};

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_UTILS_CONSTANTS_H_
