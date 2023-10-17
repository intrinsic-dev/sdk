// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MATH_TRANSFORM_UTILS_H_
#define INTRINSIC_MATH_TRANSFORM_UTILS_H_

#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic {

/**
 * Transforms a wrench from frame B to frame A.
 *
 * @param a_T_b the position and orientation of B relative to A
 * @param b_W   wrench (fx,fy,fz,tx,ty,tz) at the origin of frame B and
 *              expressed in B coordinates.
 *
 * @return a_W the same wrench sitting at the origin of A and is expressed in A
 * coordinates.
 */
Wrench TransformWrench(const Pose3d& a_T_b, const Wrench& b_W);

}  // namespace intrinsic

#endif  // INTRINSIC_MATH_TRANSFORM_UTILS_H_
