// Copyright 2023 Intrinsic Innovation LLC


#ifndef INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_COPY_H_
#define INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_COPY_H_

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/control_types_view.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/icon/flatbuffers/transform_types.h"
#include "intrinsic/icon/flatbuffers/transform_view.h"
#include "intrinsic/math/pose3.h"

namespace intrinsic_fbs {

// Copies the raw data memory from Pose3d to memory in
// Transform.
void CopyTo(Transform *transform, const intrinsic::Pose3d &pose);

// Copies the raw data memory from Transform to memory in Pose3d.
void CopyTo(intrinsic::Pose3d *pose, const Transform &transform);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_FLATBUFFERS_CONTROL_TYPES_COPY_H_
