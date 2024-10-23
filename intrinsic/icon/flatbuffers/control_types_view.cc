// Copyright 2023 Intrinsic Innovation LLC


#include "intrinsic/icon/flatbuffers/control_types_view.h"

#include "flatbuffers/base.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/math/twist.h"

namespace intrinsic_fbs {

const ::intrinsic::Wrench *FromSchema(const intrinsic_fbs::Wrench &wrench) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  return reinterpret_cast<const ::intrinsic::Wrench *>(&wrench);
}

::intrinsic::Wrench *FromSchema(intrinsic_fbs::Wrench *wrench) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  return reinterpret_cast<::intrinsic::Wrench *>(wrench);
}

}  // namespace intrinsic_fbs
