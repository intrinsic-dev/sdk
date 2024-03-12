// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_KINEMATICS_TYPES_TO_STRING_H_
#define INTRINSIC_KINEMATICS_TYPES_TO_STRING_H_
#include <string>

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {
namespace eigenmath {

std::string ToString(const VectorNd& vec);

}  // namespace eigenmath
}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_TO_STRING_H_
