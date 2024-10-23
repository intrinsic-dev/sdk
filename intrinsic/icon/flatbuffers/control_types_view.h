// Copyright 2023 Intrinsic Innovation LLC


#ifndef INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_VIEW_H_
#define INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_VIEW_H_

#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/math/twist.h"

namespace intrinsic_fbs {

// Utility helper function that allows to interpret intrinsic_fbs::Wrench as
// Wrench type.
const ::intrinsic::Wrench *FromSchema(const ::intrinsic_fbs::Wrench &wrench);
::intrinsic::Wrench *FromSchema(::intrinsic_fbs::Wrench *wrench);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_VIEW_H_
