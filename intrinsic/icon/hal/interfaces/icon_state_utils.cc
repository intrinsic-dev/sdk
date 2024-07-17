// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/icon_state_utils.h"

#include <cstdint>
#include <limits>

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/icon_state_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildIconState() {
  flatbuffers::FlatBufferBuilder builder;
  // Initializes with `max`, because NaN is not supported for integers, so that
  // the IconState flatbuffer is invalid/inconsistent until it receives its
  // first update. Requires initializing to a different value than
  // intrinsic/icon/interprocess/shared_memory_manager/segment_header.h.
  builder.Finish(builder.CreateStruct(
      IconState(/*current_cycle=*/std::numeric_limits<uint64_t>::max())));
  return builder.Release();
}
}  // namespace intrinsic_fbs
