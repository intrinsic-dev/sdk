// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_FLATBUFFERS_MATRIX_TYPES_UTILS_H_
#define INTRINSIC_ICON_FLATBUFFERS_MATRIX_TYPES_UTILS_H_

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/matrix_types.fbs.h"
namespace intrinsic_fbs {

// Copies the raw data memory from eigenmath::Matrix3d to memory in
// Matrix3d.
void CopyTo(const intrinsic::eigenmath::Matrix3d& matrix, Matrix3d& matrix_fbs);

// Returns a reference to the memory pointed at by a `intrinsic_fbs::Matrix3d`.
// The returned result is Eigen::Map<const eigenmath::Matrix3d>
template <typename T>
Eigen::Map<const T> ViewAs(const Matrix3d& matrix);
template <>
Eigen::Map<const intrinsic::eigenmath::Matrix3d> ViewAs(const Matrix3d& matrix);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_FLATBUFFERS_MATRIX_TYPES_UTILS_H_
