// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/examples/blended_cartesian_move_lib.h"

#include <memory>
#include <string>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/types/span.h"
#include "intrinsic/eigenmath/rotation_utils.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/actions/blended_move_action_info.h"
#include "intrinsic/icon/actions/point_to_point_move_info.h"
#include "intrinsic/icon/cc_client/client_utils.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/builtins.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/blended_cartesian_move.pb.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/proto_conversion.h"
#include "intrinsic/motion_planning/trajectory_planning/blended_joint_move.pb.h"
#include "intrinsic/util/proto_time.h"

namespace intrinsic::icon::examples {

namespace {
constexpr size_t kNDof = 6;

// Creates an `intrinsic_proto::BlendedCartesianMove` problem, going from
// `initial_position` over `waypoint_poses` with `blending_radius_rotational`
// and `blending_radius_translational` to `target_pose`. Boundary velocities at
// initial and target state are set to zero.
intrinsic_proto::BlendedCartesianMove CreateBlendedCartesianMoveProblem(
    const eigenmath::VectorNd& initial_position,
    const std::vector<Pose3d>& waypoint_poses, const Pose3d& target_pose,
    double blending_radius_rotational, double blending_radius_translational) {
  intrinsic_proto::BlendedCartesianMove proto;

  // Set initial position and zero initial velocity.
  *proto.mutable_initial_joint_state()->mutable_position() = {
      initial_position.begin(), initial_position.end()};
  eigenmath::VectorNd zero_vec = eigenmath::VectorNd::Constant(kNDof, 0.0);
  *proto.mutable_initial_joint_state()->mutable_velocity() = {zero_vec.begin(),
                                                              zero_vec.end()};
  *proto.mutable_initial_joint_state()->mutable_acceleration() = {
      zero_vec.begin(), zero_vec.end()};

  // Add waypoints.
  for (const auto& waypoint_pose : waypoint_poses) {
    auto* waypoint_proto = proto.add_waypoints();
    *waypoint_proto->mutable_waypoint_pose() =
        ::intrinsic::ToProto(waypoint_pose);
  }

  // Set target pose and zero target velocity.
  *proto.mutable_target_pose() = ::intrinsic::ToProto(target_pose);

  proto.set_rotational_rounding_rad(blending_radius_rotational);
  proto.set_translational_rounding_m(blending_radius_translational);

  return proto;
}

}  // namespace

absl::Status RunBlendedCartesianMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::unique_ptr<intrinsic::icon::Session> session,
      intrinsic::icon::Session::Start(icon_channel, {std::string(part_name)}));

  Client icon_client(icon_channel);
  INTRINSIC_RETURN_IF_ERROR(icon_client.Enable());
  INTRINSIC_ASSIGN_OR_RETURN(auto robot_config, icon_client.GetConfig());
  INTRINSIC_ASSIGN_OR_RETURN(
      ::intrinsic_proto::icon::GenericPartConfig part_config,
      robot_config.GetGenericPartConfig(part_name));

  // Forward declare the ActionInstanceIds to simplify reasoning about
  // Reactions.
  const intrinsic::icon::ActionInstanceId kJointMoveToStartId(0);
  const intrinsic::icon::ActionInstanceId kBlendedCartMoveId(1);
  const intrinsic::icon::ActionInstanceId kStopId(2);

  JointStatePVA init_joint_state;
  INTRINSIC_RETURN_IF_ERROR(init_joint_state.SetSize(kNDof));

  // Hard-coded initial joint configuration.
  init_joint_state.position << -0.5, -0.26, 0.0, 0.0, 1.27, 0.0;
  init_joint_state.velocity.setZero();
  init_joint_state.acceleration.setZero();
  intrinsic::icon::ActionDescriptor move_to_start =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          kJointMoveToStartId, part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              init_joint_state.position, init_joint_state.velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(kBlendedCartMoveId));

  // Define Cartesian waypoints, drawing a cube in task space.
  eigenmath::Quaterniond base_q_ee =
      eigenmath::QuaternionFromRPY(M_PI / 8, 0.0, 0.);
  Pose3d waypoint1(base_q_ee, eigenmath::Vector3d(0.2, -0.15, 0.4));
  Pose3d waypoint2(base_q_ee, eigenmath::Vector3d(0.2, 0.15, 0.4));
  Pose3d waypoint3(base_q_ee, eigenmath::Vector3d(0.4, 0.15, 0.4));
  Pose3d waypoint4(base_q_ee, eigenmath::Vector3d(0.4, 0.15, 0.6));
  Pose3d waypoint5(base_q_ee, eigenmath::Vector3d(0.2, 0.15, 0.6));
  Pose3d waypoint6(base_q_ee, eigenmath::Vector3d(0.2, -0.15, 0.6));
  Pose3d waypoint7(base_q_ee, eigenmath::Vector3d(0.4, -0.15, 0.6));
  Pose3d waypoint8(base_q_ee, eigenmath::Vector3d(0.4, -0.15, 0.4));

  std::vector<Pose3d> waypoints{waypoint1, waypoint2, waypoint3, waypoint4,
                                waypoint5, waypoint6, waypoint7};

  BlendedMoveActionInfo::FixedParams params;
  *params.mutable_blended_cartesian_move() = CreateBlendedCartesianMoveProblem(
      init_joint_state.position, waypoints, waypoint8, 0.06, 0.06);

  intrinsic::icon::ActionDescriptor move =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::BlendedMoveActionInfo::kActionTypeName,
          kBlendedCartMoveId, part_name)
          .WithFixedParams(
              intrinsic::icon::BlendedMoveActionInfo::FixedParams(params))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(kStopId));

  intrinsic::icon::ActionDescriptor stop =
      intrinsic::icon::ActionDescriptor(intrinsic::icon::kStopAction, kStopId,
                                        part_name)
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithWatcherOnCondition(
                      [&session]() { session->QuitWatcherLoop(); }));

  INTRINSIC_ASSIGN_OR_RETURN(auto actions,
                             session->AddActions({move_to_start, move, stop}));
  LOG(INFO) << "Retrieving planned trajectory via ICON session";
  INTRINSIC_ASSIGN_OR_RETURN(
      intrinsic_proto::icon::JointTrajectoryPVA planned_trajectory,
      session->GetPlannedTrajectory(kBlendedCartMoveId));

  // Some minimal introspection on the planned trajectory
  LOG(INFO) << "Planned trajectory holds " << planned_trajectory.state_size()
            << " data points and lasts "
            << intrinsic::FromProto(planned_trajectory.time_since_start(
                   planned_trajectory.time_since_start_size() - 1));

  LOG(INFO) << "Starting to execute motion";
  INTRINSIC_RETURN_IF_ERROR(session->StartAction(actions.front()));
  INTRINSIC_RETURN_IF_ERROR(session->RunWatcherLoop());
  LOG(INFO) << "Finished motion";

  return absl::OkStatus();
}

}  // namespace intrinsic::icon::examples
