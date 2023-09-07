// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_COMMON_ID_TYPES_H_
#define INTRINSIC_ICON_COMMON_ID_TYPES_H_

#include <cstdint>

#include "absl/strings/string_view.h"
#include "intrinsic/util/int_id.h"  // IWYU pragma: export // ID operators

namespace intrinsic {
namespace icon {

// Identifier for an Action Instance.
INTRINSIC_DEFINE_INT_ID_TYPE(ActionInstanceId, int64_t);

// Identifier for a Reaction.
INTRINSIC_DEFINE_INT_ID_TYPE(ReactionId, int64_t);

// Identifier for a Session.
INTRINSIC_DEFINE_INT_ID_TYPE(SessionId, int64_t);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_COMMON_ID_TYPES_H_
