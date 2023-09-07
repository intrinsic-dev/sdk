// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_PROTO_CONCATENATE_TRAJECTORY_PROTOS_H_
#define INTRINSIC_ICON_PROTO_CONCATENATE_TRAJECTORY_PROTOS_H_

#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/icon/proto/joint_space.pb.h"

namespace intrinsic {

// Splits a trajectory `proto` into a vector of sequential sub-trajectories with
// `max_subtrajectory_length`. Time stamps remain untouched in the different
// trajectory segments. Returns kFailedPrecondition in case of invalid
// `max_subtrajectory_length` or in case of an empty `proto`.
absl::StatusOr<std::vector<intrinsic_proto::icon::JointTrajectoryPVA>>
SplitTrajectoryProto(const intrinsic_proto::icon::JointTrajectoryPVA& proto,
                     int max_subtrajectory_length);

// Concatenates `trajectory_segments` to a single trajectory in a first-in-first
// out fashion. It is assumed that time stamps throughout the
// `trajectory_segments` are monotonically increasing, and that the first time
// stamp of a segment is greater than the last time stamp of the preceding
// segment. Returns kFailedPrecondition if `trajectories` is empty.
absl::StatusOr<intrinsic_proto::icon::JointTrajectoryPVA>
ConcatenateTrajectoryProtos(
    const std::vector<intrinsic_proto::icon::JointTrajectoryPVA>&
        trajectory_segments);

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_PROTO_CONCATENATE_TRAJECTORY_PROTOS_H_
