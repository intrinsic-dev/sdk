// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_CC_CLIENT_COMMON_H_
#define INTRINSIC_SKILLS_CC_CLIENT_COMMON_H_

#include "absl/time/time.h"

namespace intrinsic {
namespace skills {

// Constant `kClientDefaultTimeout` is the default timeout for GRPC requests
// made by client libraries.
constexpr absl::Duration kClientDefaultTimeout = absl::Seconds(180);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_CLIENT_COMMON_H_
