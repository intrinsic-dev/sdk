// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_ICON_STATE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_ICON_STATE_UTILS_H_

#include "flatbuffers/detached_buffer.h"

namespace intrinsic_fbs {

// Initializes `current_cycle` with `std::numeric_limits<uint64_t>::max()`, so
// that the IconState flatbuffer is invalid/inconsistent until it receives its
// first update.
flatbuffers::DetachedBuffer BuildIconState();

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_ICON_STATE_UTILS_H_
