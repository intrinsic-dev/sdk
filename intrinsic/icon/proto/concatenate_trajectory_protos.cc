// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/proto/concatenate_trajectory_protos.h"

#include <algorithm>
#include <vector>

#include "absl/status/status.h"
#include "google/protobuf/duration.pb.h"

namespace intrinsic {

absl::StatusOr<std::vector<intrinsic_proto::icon::JointTrajectoryPVA>>
SplitTrajectoryProto(const intrinsic_proto::icon::JointTrajectoryPVA& proto,
                     int max_subtrajectory_length) {
  if (proto.time_since_start_size() == 0) {
    return absl::FailedPreconditionError(
        "Empty trajectory proto cannot be split up");
  }
  if (max_subtrajectory_length < 1) {
    return absl::FailedPreconditionError(absl::StrCat(
        "max_subtrajectory_length must be greater than 0, but got ",
        max_subtrajectory_length));
  }
  const int traj_length = proto.time_since_start_size();
  int num_sub_elements = traj_length / max_subtrajectory_length;
  if (traj_length % max_subtrajectory_length != 0) {
    num_sub_elements++;
  }

  std::vector<intrinsic_proto::icon::JointTrajectoryPVA> split_trajectories(
      num_sub_elements);

  for (int subel = 0; subel < num_sub_elements; subel++) {
    for (int i = subel * max_subtrajectory_length;
         i < std::min(traj_length, (subel + 1) * max_subtrajectory_length);
         i++) {
      *split_trajectories[subel].add_time_since_start() =
          proto.time_since_start(i);
      *split_trajectories[subel].add_state() = proto.state(i);
    }
    split_trajectories[subel].set_joint_dynamic_limits_check_mode(
        proto.joint_dynamic_limits_check_mode());
  }
  return split_trajectories;
}

absl::StatusOr<intrinsic_proto::icon::JointTrajectoryPVA>
ConcatenateTrajectoryProtos(
    const std::vector<intrinsic_proto::icon::JointTrajectoryPVA>&
        trajectory_segments) {
  if (trajectory_segments.empty())
    return absl::FailedPreconditionError(
        "Vector of trajectory protos is empty.");

  intrinsic_proto::icon::JointTrajectoryPVA trajectory = trajectory_segments[0];
  for (int subel = 1; subel < trajectory_segments.size(); subel++) {
    if (trajectory_segments[subel].joint_dynamic_limits_check_mode() !=
        trajectory.joint_dynamic_limits_check_mode()) {
      return absl::InvalidArgumentError(
          "All trajectory segments should have the same "
          "dynamic_limits_check_mode.");
    }
    for (int i = 0; i < trajectory_segments[subel].time_since_start_size();
         i++) {
      *trajectory.add_time_since_start() =
          trajectory_segments[subel].time_since_start(i);
      *trajectory.add_state() = trajectory_segments[subel].state(i);
    }
  }

  return trajectory;
}

}  // namespace intrinsic
