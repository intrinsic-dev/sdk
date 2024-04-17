// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/examples/blended_joint_move_lib.h"

#include <iostream>
#include <memory>
#include <optional>
#include <ostream>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/actions/blended_move_action_info.h"
#include "intrinsic/icon/actions/point_to_point_move_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/client_utils.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/builtins.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/generic_part_config.pb.h"
#include "intrinsic/icon/proto/joint_space.pb.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/motion_planning/trajectory_planning/blended_joint_move.pb.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon::examples {

namespace {
constexpr size_t kNDof = 6;

// Creates an `intrinsic_proto::BlendedJointMove` problem, going from
// `initial_position` over `waypoint_positions` with `tightness_rad` to
// `target_position` subject to `limits`. Boundary velocities at initial and
// target state are set to zero.
intrinsic_proto::BlendedJointMove CreateBlendedJointMoveProblem(
    const eigenmath::VectorNd& initial_position,
    const std::vector<eigenmath::VectorNd>& waypoint_positions,
    const eigenmath::VectorNd& target_position, double tightness_rad,
    std::optional<JointLimits> limits = std::nullopt) {
  intrinsic_proto::BlendedJointMove proto;

  // Set initial position and zero initial velocity.
  *proto.mutable_initial_joint_state()->mutable_joints() = {
      initial_position.begin(), initial_position.end()};

  // Add waypoints.
  for (const auto& waypoint_position : waypoint_positions) {
    intrinsic_proto::BlendedJointMove_JointWaypoint* waypoint_proto =
        proto.add_waypoints();
    *waypoint_proto->mutable_waypoint_position_rad()->mutable_joints() = {
        waypoint_position.begin(), waypoint_position.end()};
    waypoint_proto->set_desired_tightness_rad(tightness_rad);
  }

  // Set target position and zero target velocity.
  *proto.mutable_target_joint_state()->mutable_joints() = {
      target_position.begin(), target_position.end()};

  if (limits.has_value()) {
    *proto.mutable_joint_limits() = ToProto(*limits);
  }

  return proto;
}

}  // namespace

absl::Status RunBlendedJointMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  INTR_ASSIGN_OR_RETURN(
      std::unique_ptr<intrinsic::icon::Session> session,
      intrinsic::icon::Session::Start(icon_channel, {std::string(part_name)}));

  // Forward declare the ActionInstanceIds to simplify reasoning about
  // Reactions.
  const intrinsic::icon::ActionInstanceId kJointMoveToStartId(0);
  const intrinsic::icon::ActionInstanceId kBlendedJointMoveId(1);
  const intrinsic::icon::ActionInstanceId kStopId(2);

  eigenmath::VectorNd initial_joint_pos =
      eigenmath::VectorNd::Constant(kNDof, 0.0);
  eigenmath::VectorNd zero_velocity = eigenmath::VectorNd::Constant(kNDof, 0.0);
  intrinsic::icon::ActionDescriptor move_to_start =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          kJointMoveToStartId, part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              initial_joint_pos, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(kBlendedJointMoveId));

  // Define a few waypoints.
  eigenmath::VectorNd waypoint1 = eigenmath::VectorNd::Zero(kNDof);
  waypoint1 << 0.6, 0, -0.5, 0, -0.5, 0;
  eigenmath::VectorNd waypoint2 = eigenmath::VectorNd::Zero(kNDof);
  waypoint2 << -0.6, 0.5, -0.5, 0.5, 0.5, 0.5;
  eigenmath::VectorNd waypoint3 = eigenmath::VectorNd::Zero(kNDof);
  waypoint3 << -0.6, 0.0, 0, 0.5, 0, 0.5;
  const eigenmath::VectorNd& target_joint_pos = initial_joint_pos;

  Client icon_client(icon_channel);
  INTR_RETURN_IF_ERROR(icon_client.Enable());

  // Extract number of actuated joints.
  INTR_ASSIGN_OR_RETURN(auto robot_config, icon_client.GetConfig());
  INTR_ASSIGN_OR_RETURN(::intrinsic_proto::icon::GenericPartConfig part_config,
                        robot_config.GetGenericPartConfig(part_name));
  INTR_ASSIGN_OR_RETURN(
      auto limits, intrinsic::FromProto(
                       part_config.joint_limits_config().application_limits()));

  BlendedMoveActionInfo::FixedParams params;
  *params.mutable_blended_joint_move() = CreateBlendedJointMoveProblem(
      initial_joint_pos,
      {waypoint1, waypoint2, waypoint3, waypoint1, waypoint2, waypoint3},
      target_joint_pos,
      /*tightness_rad=*/0.2, limits);
  intrinsic::icon::ActionDescriptor jmove =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::BlendedMoveActionInfo::kActionTypeName,
          kBlendedJointMoveId, part_name)
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
                  .WithWatcherOnCondition([&session]() {
                    std::cout << "Reached stop action." << std::endl;
                    session->QuitWatcherLoop();
                  }));

  INTR_ASSIGN_OR_RETURN(auto actions,
                        session->AddActions({move_to_start, jmove, stop}));
  LOG(INFO) << "Retrieving planned trajectory via ICON session";
  INTR_ASSIGN_OR_RETURN(
      intrinsic_proto::icon::JointTrajectoryPVA planned_trajectory,
      session->GetPlannedTrajectory(kBlendedJointMoveId));

  // Some minimal introspection on the planned trajectory
  LOG(INFO) << "Planned trajectory holds " << planned_trajectory.state_size()
            << " data points and lasts "
            << intrinsic::FromProto(planned_trajectory.time_since_start(
                   planned_trajectory.time_since_start_size() - 1));

  LOG(INFO) << "Starting to execute motion";
  INTR_RETURN_IF_ERROR(session->StartAction(actions.front()));
  INTR_RETURN_IF_ERROR(session->RunWatcherLoop());
  LOG(INFO) << "Finished motion";

  return absl::OkStatus();
}

}  // namespace intrinsic::icon::examples
