// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/flatbuffers/matrix_types_utils.h"

#include "flatbuffers/base.h"
#include "flatbuffers/stl_emulation.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/matrix_types.fbs.h"

namespace intrinsic_fbs {

namespace {
constexpr int kNumMatrixElements = 9;
constexpr int kNumRows = 3;
constexpr int kNumCols = 3;
}  // namespace

// Copies the raw data memory from eigenmath::Matrix3d to memory in
// Matrix3d.
void CopyTo(const intrinsic::eigenmath::Matrix3d& matrix,
            Matrix3d& matrix_fbs) {
  matrix_fbs.mutable_values()->CopyFromSpan(
      flatbuffers::span<const double, kNumMatrixElements>(matrix.data(),
                                                          matrix.size()));
}

template <>
Eigen::Map<const intrinsic::eigenmath::Matrix3d> ViewAs(
    const Matrix3d& matrix) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  return Eigen::Map<const intrinsic::eigenmath::Matrix3d>(
      matrix.values()->data(), kNumRows, kNumCols);
}

}  // namespace intrinsic_fbs
