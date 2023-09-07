// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_KINEMATICS_TYPES_JOINT_LIMITS_XD_H_
#define INTRINSIC_KINEMATICS_TYPES_JOINT_LIMITS_XD_H_

#include <string>

#include "absl/status/statusor.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_limits.pb.h"

namespace intrinsic {

// Version of the JointLimits that has dynamically allocated size. This allows
// it to represent limits for arbitrarily large structures.
//
// Note that when using realtime control, you will need to convert this object
// back into a restricted size JointLimits object. This conversion might fail if
// the limits are larger than the size supported.
struct JointLimitsXd {
  // Makes JointLimits with each limit range set to (-infinity, infinity).
  //
  // `size` is the number of elements each limit vector should have,
  // corresponding to the number of joints.
  static JointLimitsXd Unlimited(size_t size) INTRINSIC_NON_REALTIME_ONLY;

  // Constructs JointLimitsXd from JointLimits.
  static JointLimitsXd Create(const JointLimits& joint_limits)
      INTRINSIC_NON_REALTIME_ONLY;

  // Returns the number of elements the `min_position` vector has, corresponding
  // to the number of joints. When `IsSizeConsistent()` is true, this equals the
  // size of each limit vector.
  eigenmath::VectorXd::Index size() const INTRINSIC_NON_REALTIME_ONLY;

  // Returns true if all limit vectors have the same size.
  bool IsSizeConsistent() const INTRINSIC_NON_REALTIME_ONLY;

  // Sets the size of all limit vectors to `size`. Clears all limit values to 0.
  void SetSize(eigenmath::VectorXd::Index size) INTRINSIC_NON_REALTIME_ONLY;

  // Sets each limit range to (-infinity, infinity).
  void SetUnlimited() INTRINSIC_NON_REALTIME_ONLY;

  bool IsValid() const INTRINSIC_NON_REALTIME_ONLY;

  // Limit vectors.
  eigenmath::VectorXd min_position;
  eigenmath::VectorXd max_position;
  eigenmath::VectorXd max_velocity;
  eigenmath::VectorXd max_acceleration;
  eigenmath::VectorXd max_jerk;
  eigenmath::VectorXd max_torque;
};

// Updates `base` with the populated fields of `update`.
//
// This function exists so that users can overwrite certain fields in base
// without needing to provide all of them again.
//
// Fails if `update` provides a field that does not have the same size as the
// corresponding field in base.
//
// Note: we do this merging on the proto level since it is easier to test the
// presence of fields.
absl::StatusOr<JointLimitsXd> UpdateJointLimits(
    const JointLimitsXd& base,
    const intrinsic_proto::JointLimitsUpdate& update);

intrinsic_proto::JointLimits ToProto(const JointLimitsXd& limits);

absl::StatusOr<JointLimitsXd> ToJointLimitsXd(
    const intrinsic_proto::JointLimits& limits_proto);

intrinsic_proto::JointLimitsUpdate ToJointLimitsUpdate(
    const JointLimitsXd& limits);

// Constructs JointLimits from JointLimitsXd. It will fail if the input limits
// exceed the maximum supported size.
absl::StatusOr<JointLimits> ToJointLimits(const JointLimitsXd& limits);

std::string ToString(const JointLimitsXd& limits);

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_JOINT_LIMITS_XD_H_
