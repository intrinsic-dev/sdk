// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/examples/joint_then_cart_move_lib.h"

#include <iostream>
#include <memory>
#include <ostream>
#include <string>
#include <vector>

#include "absl/status/status.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/actions/cartesian_position_info.h"
#include "intrinsic/icon/actions/point_to_point_move_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/client_utils.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/builtins.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/icon/proto/part_status.pb.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic::icon::examples {

constexpr int kNDof = 6;

constexpr double kSettlingTimeoutSeconds = 1;

namespace {

// Prints the Joint Position for every DoF, or n/a if it's missing.
void PrintJointPosition(const intrinsic_proto::icon::PartStatus& part_status) {
  for (int i = 0; i < part_status.joint_states_size(); ++i) {
    const intrinsic_proto::icon::PartJointState& joint_state =
        part_status.joint_states(i);

    if (!joint_state.has_position_sensed()) {
      std::cout << "  J" << i << ": n/a" << std::endl;
    } else {
      std::cout << "  J" << i << ": "
                << absl::StrFormat("%6.3f", joint_state.position_sensed())
                << std::endl;
    }
  }
}

absl::Status PrintBaseTTipSensed(
    const intrinsic_proto::icon::PartStatus& part_status) {
  if (!part_status.has_base_t_tip_sensed()) {
    return absl::InvalidArgumentError(
        "PartStatus is missing base_t_tip_sensed");
  }

  const intrinsic_proto::icon::Transform& base_t_tip =
      part_status.base_t_tip_sensed();

  std::cout << "  x: " << absl::StrFormat("%6.3f", base_t_tip.pos().x())
            << std::endl
            << "  y: " << absl::StrFormat("%6.3f", base_t_tip.pos().y())
            << std::endl
            << "  z: " << absl::StrFormat("%6.3f", base_t_tip.pos().z())
            << std::endl
            << " qw: " << absl::StrFormat("%6.3f", base_t_tip.rot().qw())
            << std::endl
            << " qx: " << absl::StrFormat("%6.3f", base_t_tip.rot().qx())
            << std::endl
            << " qy: " << absl::StrFormat("%6.3f", base_t_tip.rot().qy())
            << std::endl
            << " qz: " << absl::StrFormat("%6.3f", base_t_tip.rot().qz())
            << std::endl;
  return absl::OkStatus();
}

}  // namespace

absl::Status JointThenCartMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  if (part_name.empty()) {
    return absl::InvalidArgumentError("`part_name` must not be empty.");
  }
  intrinsic::icon::Client client(icon_channel);

  INTRINSIC_ASSIGN_OR_RETURN(
      std::unique_ptr<intrinsic::icon::Session> session,
      intrinsic::icon::Session::Start(icon_channel, {std::string(part_name)}));

  // Compute two feasible joint configurations based on the joint limits.
  eigenmath::VectorNd jpos_1, jpos_2;
  {
    INTRINSIC_ASSIGN_OR_RETURN(auto robot_config, client.GetConfig());
    INTRINSIC_ASSIGN_OR_RETURN(auto part_config,
                               robot_config.GetGenericPartConfig(part_name));
    INTRINSIC_ASSIGN_OR_RETURN(
        JointLimits joint_limits,
        intrinsic::FromProto(
            part_config.joint_limits_config().application_limits()));

    eigenmath::VectorNd joint_range =
        joint_limits.max_position - joint_limits.min_position;
    eigenmath::VectorNd center_pos =
        joint_limits.min_position + (joint_range / 2.0);

    // Add an offset from the center of the joint range to avoid a "zero" joint
    // configuration to avoid side-effects due to kinematic singularities during
    // Cartesian positioning. The offset is proportional to the joint range to
    // avoid going outside the range in case it is very small.
    jpos_1 = center_pos + (joint_range / 10.0).cwiseMin(0.5);
    // use a larger offset from the center of the joint range, proportional to
    // the joint range but bounded.
    jpos_2 = center_pos + (joint_range / 5.0).cwiseMin(0.9);
  }

  std::vector<double> zero_velocity(kNDof, 0.0);

  // Forward declare the ActionInstanceIds to simplify reasoning about
  // Reactions.
  const intrinsic::icon::ActionInstanceId kJointMoveToStartId(0);
  const intrinsic::icon::ActionInstanceId kStopId(1);
  const intrinsic::icon::ActionInstanceId kJointMoveId(2);
  const intrinsic::icon::ActionInstanceId kCartesianMoveId(3);

  intrinsic::icon::ActionDescriptor move_to_start =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          kJointMoveToStartId, part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              jpos_1, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(
                  intrinsic::icon::AllOf(
                      {intrinsic::icon::IsGreaterThanOrEqual(
                           intrinsic::icon::PointToPointMoveInfo::
                               kSetpointDoneForSeconds,
                           0.0),
                       intrinsic::icon::IsLessThan(
                           intrinsic::icon::PointToPointMoveInfo::
                               kSetpointDoneForSeconds,
                           kSettlingTimeoutSeconds),
                       intrinsic::icon::IsLessThan(
                           intrinsic::icon::PointToPointMoveInfo::
                               kDistanceToSensed,
                           1e-3)}))
                  // This registers a callback that will be called once the
                  // condition becomes true. The callback runs in a separate,
                  // non-realtime thread.
                  // It's important to have a callback that invokes the
                  // QuitWatcherLoop() method, because otherwise the main thread
                  // will block on RunWatcherLoop() forever.
                  .WithWatcherOnCondition([&session]() {
                    std::cout << "Reached Start Position." << std::endl;
                    session->QuitWatcherLoop();
                  })
                  .WithRealtimeActionOnCondition(
                      // Note that this is a "forward reference" that instructs
                      // ICON to switch to the `stop` Action in the same
                      // realtime cycle as the condition above becomes true.
                      // Otherwise the `move_to_start` Action would remain
                      // active until the Session is closed, or another Action
                      // is started.
                      kStopId))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(
                  intrinsic::icon::AllOf(
                      {intrinsic::icon::IsDone(),
                       intrinsic::icon::IsGreaterThanOrEqual(
                           intrinsic::icon::PointToPointMoveInfo::
                               kSetpointDoneForSeconds,
                           kSettlingTimeoutSeconds)}))
                  // Another non-realtime callback. You will see this print a
                  // message when the joint motion fails to reach the joint goal
                  // within 'kSettlingTimeoutSeconds' of the trajectory
                  // generator reporting 'done'. It is important to call
                  // 'RunWatcherLoop' with a timeout, or call 'QuitWatcherLoop'
                  // for every possible execution path.
                  .WithWatcherOnCondition([&session]() {
                    std::cout << "Failed to reach Start Position." << std::endl;
                    session->QuitWatcherLoop();
                  })
                  .WithRealtimeActionOnCondition(
                      // Note that this is a "forward reference" that instructs
                      // ICON to switch to the `stop` Action in the same
                      // realtime cycle as the condition above becomes true.
                      // Otherwise the `move_to_start` Action would remain
                      // active until the Session is closed, or another Action
                      // is started.
                      kStopId));

  // Stops all motion of the part while respecting joint limits. Is normally
  // used as the `default` Action that is used when no Session is active.
  intrinsic::icon::ActionDescriptor stop = intrinsic::icon::ActionDescriptor(
      intrinsic::icon::kStopAction, kStopId, part_name);

  {
    // Add the Action. This only validates the command and prepares the realtime
    // system, to actually execute the Action one needs to call StartAction()
    // (see below).
    INTRINSIC_ASSIGN_OR_RETURN(auto actions,
                               session->AddActions({move_to_start, stop}));

    std::cout << "Moving robot to known Start Position." << std::endl;
    // Actually start the Action.
    INTRINSIC_RETURN_IF_ERROR(session->StartAction(actions.front()));

    // Start handling non-realtime Reaction callbacks. This blocks until
    // QuitWatcherLoop() is called, or until an error occurs in the realtime
    // system.
    INTRINSIC_RETURN_IF_ERROR(session->RunWatcherLoop());
  }

  // We're at the starting position, save the Cartesian pose to use as a
  // goal later.
  intrinsic::icon::CartesianPositionInfo::FixedParams cgoal;
  {
    // Get the current robot status, and extract the status for the Part we are
    // interested in.
    INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartStatus part_status,
                               client.GetSinglePartStatus(part_name));

    std::cout << "Initial Joint Position:" << std::endl;
    PrintJointPosition(part_status);

    const intrinsic_proto::icon::Transform& base_t_tip =
        part_status.base_t_tip_sensed();

    std::cout << "Saved End Effector Goal Pose:" << std::endl;
    INTRINSIC_RETURN_IF_ERROR(PrintBaseTTipSensed(part_status));

    // Set the current Cartesian pose as the goal for the Cartesian move
    // Action.
    *cgoal.mutable_goal_pose() = base_t_tip;
  }

  intrinsic::icon::ActionDescriptor jmove =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName, kJointMoveId,
          part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              jpos_2, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(
                  intrinsic::icon::AllOf(
                      {intrinsic::icon::IsDone(),
                       intrinsic::icon::IsLessThan(
                           intrinsic::icon::PointToPointMoveInfo::
                               kDistanceToSensed,
                           1e-3)}))
                  // Another non-realtime callback. You will see this print a
                  // message when the joint motion finishes. This does not call
                  // 'QuitWatcherLoop()', because we expect more Actions to be
                  // executed.
                  .WithWatcherOnCondition([]() {
                    std::cout << "Reached Joint Goal. Cartesian motion has "
                                 "already started on the RTPC."
                              << std::endl;
                  })
                  // This instructs ICON to switch to the Action with
                  // the given ID in the same realtime cycle as the condition
                  // (kDistanceToSensed < 1e-3 ) above becomes true.
                  .WithRealtimeActionOnCondition(
                      // Note that this is a "forward reference" to
                      // the ID of cmove below.
                      kCartesianMoveId))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(
                  intrinsic::icon::AllOf(
                      {intrinsic::icon::IsDone(),
                       intrinsic::icon::IsGreaterThanOrEqual(
                           intrinsic::icon::PointToPointMoveInfo::
                               kSetpointDoneForSeconds,
                           kSettlingTimeoutSeconds)}))
                  // Another non-realtime callback. You will see this print a
                  // message when the joint motion fails to reach the joint goal
                  // within 'kSettlingTimeoutSeconds' of the trajectory
                  // generator reporting 'done'. This does not call
                  // 'QuitWatcherLoop()', because we expect more Actions to be
                  // executed.
                  .WithWatcherOnCondition([]() {
                    std::cout
                        << "Failed to reach Joint Goal. Cartesian motion has "
                           "already started on the RTPC."
                        << std::endl;
                  })
                  // This instructs ICON to switch to the Action with
                  // the given ID in the same realtime cycle as the condition
                  // above becomes true.
                  .WithRealtimeActionOnCondition(
                      // Note that this is a "forward reference" to
                      // the ID of cmove below.
                      kCartesianMoveId));

  intrinsic::icon::ActionDescriptor cmove =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::CartesianPositionInfo::kActionTypeName,
          kCartesianMoveId, part_name)
          .WithFixedParams(cgoal)
          .WithReaction(intrinsic::icon::ReactionDescriptor(
                            intrinsic::icon::AllOf(
                                {intrinsic::icon::IsDone(),
                                 intrinsic::icon::IsLessThan(
                                     intrinsic::icon::CartesianPositionInfo::
                                         kLinearDistanceToGoal,
                                     1e-3),
                                 intrinsic::icon::IsLessThan(
                                     intrinsic::icon::CartesianPositionInfo::
                                         kAngularDistanceToGoal,
                                     1e-2)}))
                            .WithWatcherOnCondition(
                                [&session]() { session->QuitWatcherLoop(); }))
          .WithReaction(intrinsic::icon::ReactionDescriptor(
                            intrinsic::icon::AllOf(
                                {intrinsic::icon::IsDone(),
                                 intrinsic::icon::IsGreaterThanOrEqual(
                                     intrinsic::icon::CartesianPositionInfo::
                                         kLinearDistanceToGoal,
                                     1e-3),
                                 intrinsic::icon::IsGreaterThanOrEqual(
                                     intrinsic::icon::CartesianPositionInfo::
                                         kAngularDistanceToGoal,
                                     1e-2)}))
                            .WithWatcherOnCondition([&session]() {
                              std::cout << "Failed to reach Cartesian goal."
                                        << std::endl;
                              session->QuitWatcherLoop();
                            }));
  {
    INTRINSIC_ASSIGN_OR_RETURN(auto actions,
                               session->AddActions({jmove, cmove}));

    std::cout << "Starting Joint Position motion." << std::endl;

    INTRINSIC_RETURN_IF_ERROR(session->StartAction(actions.front()));
    INTRINSIC_RETURN_IF_ERROR(session->RunWatcherLoop());
  }

  std::cout << "Finished Cartesian Position motion." << std::endl;

  {
    // Read the final status to verify that the Cartesian motion arrived back at
    // the starting pose.
    INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartStatus part_status,
                               client.GetSinglePartStatus(part_name));

    std::cout << "Joint Position after Cartesian move:" << std::endl;
    PrintJointPosition(part_status);

    std::cout << "End effector pose after Cartesian move:" << std::endl;
    INTRINSIC_RETURN_IF_ERROR(PrintBaseTTipSensed(part_status));
  }

  // The Session is automatically closed when the object goes out of scope. ICON
  // then automatically switches to the `default` (stop) Action to safely stop
  // the robot and hold its position.
  return absl::OkStatus();
}

}  // namespace intrinsic::icon::examples
