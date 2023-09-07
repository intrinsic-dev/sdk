// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/interfaces/joint_limits_utils.h"

#include <vector>

#include "absl/status/status.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/vector.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/interfaces/joint_limits_generated.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/kinematics/types/joint_limits.pb.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildJointLimits(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto min_pos = builder.CreateVector(zeros);
  auto max_pos = builder.CreateVector(zeros);
  auto max_vel = builder.CreateVector(zeros);
  auto max_acc = builder.CreateVector(zeros);
  auto max_jerk = builder.CreateVector(zeros);
  auto max_effort = builder.CreateVector(zeros);
  auto joint_limits =
      CreateJointLimits(builder, min_pos, max_pos, false, max_vel, false,
                        max_acc, false, max_jerk, false, max_effort);
  builder.Finish(joint_limits);
  return builder.Release();
}

}  // namespace intrinsic_fbs

namespace intrinsic::icon {

// Checks that a RepeatedField<double> of a protobuf and a Vector<double> from a
// flatbuffer have the same size. The field name is only used for the error
// message if sizes are not equal. Returns InvalidArgumentError otherwise.
absl::Status CheckSizeEqual(
    const ::google::protobuf::RepeatedField<double>& pb_field,
    const flatbuffers::Vector<double>& fb_field, absl::string_view field_name) {
  int fb_num_joints = fb_field.size();
  int pb_num_joints = pb_field.size();
  if (fb_num_joints != pb_num_joints) {
    return absl::InvalidArgumentError(
        absl::StrFormat("JointLimits Flatbuffer expects %i joints but "
                        "the field '%s' of the protobuf contains %i values",
                        fb_num_joints, field_name, pb_num_joints));
  }
  return absl::OkStatus();
}

absl::Status ToFlatbufferWithSizeCheck(
    const ::google::protobuf::RepeatedField<double>& pb_field,
    flatbuffers::Vector<double>& fb_field, absl::string_view field_name) {
  INTRINSIC_RETURN_IF_ERROR(CheckSizeEqual(pb_field, fb_field, field_name));
  for (int i = 0; i < fb_field.size(); i++) {
    fb_field.Mutate(i, pb_field.Get(i));
  }
  return absl::OkStatus();
}

absl::Status ParseProtoJointLimits(
    const intrinsic_proto::JointLimits& pb_limits,
    icon::MutableHardwareInterfaceHandle<intrinsic_fbs::JointLimits>&
        fb_limits) {
  fb_limits->mutate_has_velocity_limits(pb_limits.has_max_velocity());
  fb_limits->mutate_has_acceleration_limits(pb_limits.has_max_acceleration());
  fb_limits->mutate_has_jerk_limits(pb_limits.has_max_jerk());
  fb_limits->mutate_has_effort_limits(pb_limits.has_max_effort());

  if (pb_limits.min_position().values_size() !=
          pb_limits.max_position().values_size() ||
      (pb_limits.has_max_velocity() &&
       pb_limits.min_position().values_size() !=
           pb_limits.max_velocity().values_size()) ||
      (pb_limits.has_max_acceleration() &&
       pb_limits.min_position().values_size() !=
           pb_limits.max_acceleration().values_size()) ||
      (pb_limits.has_max_jerk() && pb_limits.min_position().values_size() !=
                                       pb_limits.max_jerk().values_size()) ||
      (pb_limits.has_max_effort() &&
       pb_limits.min_position().values_size() !=
           pb_limits.max_effort().values_size())) {
    return absl::InvalidArgumentError(
        absl::StrFormat("All non-empty fields in JointLimits proto must have "
                        "the same size. Sizes are: "
                        "min_position:%d, max_position:%d, max_velocity:%d, "
                        "max_acceleration:%d, max_jerk:%d, max_effort:%d. ",
                        pb_limits.min_position().values_size(),
                        pb_limits.max_position().values_size(),
                        pb_limits.max_velocity().values_size(),
                        pb_limits.max_acceleration().values_size(),
                        pb_limits.max_jerk().values_size(),
                        pb_limits.max_effort().values_size()));
  }

  INTRINSIC_RETURN_IF_ERROR(ToFlatbufferWithSizeCheck(
      pb_limits.min_position().values(), *fb_limits->mutable_min_position(),
      "min_position"));
  INTRINSIC_RETURN_IF_ERROR(ToFlatbufferWithSizeCheck(
      pb_limits.max_position().values(), *fb_limits->mutable_max_position(),
      "max_position"));
  if (pb_limits.has_max_velocity()) {
    INTRINSIC_RETURN_IF_ERROR(ToFlatbufferWithSizeCheck(
        pb_limits.max_velocity().values(), *fb_limits->mutable_max_velocity(),
        "max_velocity"));
  }
  if (pb_limits.has_max_acceleration()) {
    INTRINSIC_RETURN_IF_ERROR(ToFlatbufferWithSizeCheck(
        pb_limits.max_acceleration().values(),
        *fb_limits->mutable_max_acceleration(), "max_acceleration"));
  }
  if (pb_limits.has_max_jerk()) {
    INTRINSIC_RETURN_IF_ERROR(
        ToFlatbufferWithSizeCheck(pb_limits.max_jerk().values(),
                                  *fb_limits->mutable_max_jerk(), "max_jerk"));
  }
  if (pb_limits.has_max_effort()) {
    INTRINSIC_RETURN_IF_ERROR(ToFlatbufferWithSizeCheck(
        pb_limits.max_effort().values(), *fb_limits->mutable_max_effort(),
        "max_effort"));
  }

  return absl::OkStatus();
}

}  // namespace intrinsic::icon
