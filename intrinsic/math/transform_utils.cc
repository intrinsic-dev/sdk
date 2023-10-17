// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/math/transform_utils.h"

#include "intrinsic/math/pose3.h"

namespace intrinsic {

Wrench TransformWrench(const Pose3d& a_T_b, const Wrench& b_W) {
  Wrench a_W;
  a_W.head<3>() = a_T_b.so3() * b_W.head<3>();
  a_W.tail<3>() =
      a_T_b.so3() * b_W.tail<3>() + a_T_b.translation().cross(a_W.head<3>());
  return Wrench(a_W);
}

}  // namespace intrinsic
