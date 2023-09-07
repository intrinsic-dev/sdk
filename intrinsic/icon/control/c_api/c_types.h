// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_TYPES_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_TYPES_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

constexpr size_t kXfaIconMaxNumberOfJoints = 25;

// C API type to convey joint position commands with optional feedforwards.
// The arrays are fixed-size so they can live on the stack, but only the given
// number of elements is valid to read.
//
// It is the responsibility of the creator to ensure that the arrays (if
// present) all have `size` *valid* elements.
struct XfaIconJointPositionCommand {
  size_t size;
  // Array of position setpoints.
  double position_setpoints[kXfaIconMaxNumberOfJoints];
  // Array of velocity feedforwards. Set velocity_feedforwards_size to zero if
  // there are no velocity feedforwards.
  double velocity_feedforwards[kXfaIconMaxNumberOfJoints];
  bool has_velocity_feedforwards;
  // Array of acceleration feedforwards. Set acceleration_feedforwards_size to
  // zero if there are no acceleration feedforwards.
  double acceleration_feedforwards[kXfaIconMaxNumberOfJoints];
  bool has_acceleration_feedforwards;
};

// C API type to convey joint limits.
// The arrays are fixed-size so they can live on the stack, but only the given
// number of elements is valid to read.
//
// It is the responsibility of the creator to ensure that the arrays (if
// present) all have `size` *valid* elements.
struct XfaIconJointLimits {
  size_t size;
  // Array of minimum position values.
  double min_position[kXfaIconMaxNumberOfJoints];
  // Array of maximum position values.
  double max_position[kXfaIconMaxNumberOfJoints];
  // Array of maximum velocity values.
  double max_velocity[kXfaIconMaxNumberOfJoints];
  // Array of maximum acceleration values.
  double max_acceleration[kXfaIconMaxNumberOfJoints];
  // Array of maximum jerk values.
  double max_jerk[kXfaIconMaxNumberOfJoints];
  // Array of maximum torque values.
  double max_torque[kXfaIconMaxNumberOfJoints];
};

// C API type to convey positional joint state.
struct XfaIconJointStateP {
  size_t size;
  double positions[kXfaIconMaxNumberOfJoints];
};

// C API type to convey velocity joint state.
struct XfaIconJointStateV {
  size_t size;
  double velocities[kXfaIconMaxNumberOfJoints];
};

// C API type to convey acceleration joint state.
struct XfaIconJointStateA {
  size_t size;
  double accelerations[kXfaIconMaxNumberOfJoints];
};

struct XfaIconQuaternion {
  double w;
  double x;
  double y;
  double z;
};

struct XfaIconPoint {
  double x;
  double y;
  double z;
};

struct XfaIconPose3d {
  XfaIconQuaternion rotation;
  XfaIconPoint translation;
};

struct XfaIconWrench {
  double x;
  double y;
  double z;
  double rx;
  double ry;
  double rz;
};

// Note that this is *not* zero-terminated, so dereferencing `data + size` is an
// error.
struct XfaIconString {
  char* data;
  size_t size;
};

typedef void (*XfaIconStringDestroy)(XfaIconString* str);

// Same as above, not zero-terminated. In addition, this is a pure view whose
// storage is not valid outside of its original scope (i.e. functions that take
// XfaIconStringView must not hold references after they finish).
struct XfaIconStringView {
  const char* data;
  const size_t size;
};

// C API type for 6 x N matrices of double values,
// with N <= kXfaIconMaxNumberOfJoints.
struct XfaIconMatrix6Nd {
  // The number of columns in the matrix. Must not be greater than
  // kXfaIconMaxNumberOfJoints.
  size_t num_cols;
  // Matrix values, in column-major order (to match Eigen's default order).
  // Indices >= 6 * num_cols are invalid and contain unspecified data!
  double data[6 * kXfaIconMaxNumberOfJoints];
};

#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_TYPES_H_
