// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_COMMON_ID_TYPES_H_
#define INTRINSIC_ICON_COMMON_ID_TYPES_H_

#include <cstdint>

#include "intrinsic/third_party/intops/strong_int.h"

namespace intrinsic {
namespace icon {

// Identifier for an Action Instance.
DEFINE_STRONG_INT_TYPE(ActionInstanceId, int64_t);

// Identifier for a Reaction.
DEFINE_STRONG_INT_TYPE(ReactionId, int64_t);

// Identifier for a Session.
DEFINE_STRONG_INT_TYPE(SessionId, int64_t);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_COMMON_ID_TYPES_H_
