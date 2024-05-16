// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_KINEMATICS_TYPES_TO_FIXED_STRING_H_
#define INTRINSIC_KINEMATICS_TYPES_TO_FIXED_STRING_H_

#include <ostream>

#include "absl/strings/string_view.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/utils/fixed_string.h"
#include "intrinsic/kinematics/types/cartesian_limits.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/state_rn.h"
#include "intrinsic/math/pose3.h"

namespace intrinsic {

// absl::AlphaNum formats double in a "%.6g". So we need 9 character for each
// numbers: 7 digits (when whole number is 0, we have 6 decimals), dot and
// negative sign. We need N-1 commas.
constexpr size_t kDoubleStrSize = 9;

constexpr size_t kVectorNdStrSize =
    kDoubleStrSize * eigenmath::MAX_EIGEN_VECTOR_SIZE +
    (eigenmath::MAX_EIGEN_VECTOR_SIZE - 1);

// We need to had the prefix to the vector.
constexpr size_t kStateStrSize = 3 + kVectorNdStrSize;

// We need 10 fields that include min_,max_ in from fo the prefix.
constexpr size_t kLimitStrSize = 10 * (7 + kVectorNdStrSize);

// A pose is 3 position values and 4 quaternions values.
constexpr size_t kPose3dStrSize = kDoubleStrSize * (3 + 4);

// We have 8 Vector3d and their prefix and 3 doubles and their prefix.
constexpr size_t kCartLimitStrSize =
    8 * ((3 * kDoubleStrSize) + 7) + 3 * (kDoubleStrSize + 10);

namespace eigenmath {

icon::FixedString<kVectorNdStrSize> ToFixedString(
    const eigenmath::VectorNd& vec);

icon::FixedString<kPose3dStrSize> ToFixedString(const Pose3d& pose);

}  // namespace eigenmath

icon::FixedString<kStateStrSize> ToFixedString(const StateRnP& state);

icon::FixedString<kStateStrSize> ToFixedString(const StateRnV& state);

icon::FixedString<kStateStrSize> ToFixedString(const StateRnA& state);

icon::FixedString<kStateStrSize> ToFixedString(const StateRnJ& state);

icon::FixedString<kStateStrSize> ToFixedString(const StateRnT& state);

icon::FixedString<2 * kStateStrSize> ToFixedString(const StateRnPV& state);

icon::FixedString<3 * kStateStrSize> ToFixedString(const StateRnPVA& state);

icon::FixedString<3 * kStateStrSize> ToFixedString(const StateRnPVT& state);

icon::FixedString<4 * kStateStrSize> ToFixedString(const StateRnPVAJ& state);

icon::FixedString<4 * kStateStrSize> ToFixedString(const StateRnPVAT& state);

icon::FixedString<2 * kStateStrSize> ToFixedString(const StateRnVA& state);

icon::FixedString<3 * kStateStrSize> ToFixedString(const StateRnVAJ& state);

icon::FixedString<kLimitStrSize> ToFixedString(const JointLimits& limits);

icon::FixedString<kCartLimitStrSize> ToFixedString(
    const CartesianLimits& limits);

// These 'PrintTo()' functions exist in order to print output values in gtest
// matchers. Use 'PrintTo()' instead of << operators in order to guard RT
// safety. See also
// go/gunitadvanced#teaching-googletest-how-to-print-your-values
void PrintTo(const JointLimits& joint_limits, std::ostream* os);

void PrintTo(const StateRnP& state, std::ostream* os);
void PrintTo(const StateRnV& state, std::ostream* os);
void PrintTo(const StateRnA& state, std::ostream* os);
void PrintTo(const StateRnJ& state, std::ostream* os);
void PrintTo(const StateRnT& state, std::ostream* os);
void PrintTo(const StateRnPV& state, std::ostream* os);
void PrintTo(const StateRnPVA& state, std::ostream* os);
void PrintTo(const StateRnPVT& state, std::ostream* os);
void PrintTo(const StateRnPVAJ& state, std::ostream* os);
void PrintTo(const StateRnPVAT& state, std::ostream* os);
void PrintTo(const StateRnVA& state, std::ostream* os);
void PrintTo(const StateRnVAJ& state, std::ostream* os);

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_TO_FIXED_STRING_H_
