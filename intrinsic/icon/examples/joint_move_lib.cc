// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/examples/joint_move_lib.h"

#include <memory>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/actions/point_to_point_move_info.h"
#include "intrinsic/icon/cc_client/client_utils.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/builtins.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/release/status_helpers.h"

constexpr int kNDof = 6;

namespace intrinsic::icon::examples {

absl::Status RunJointMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  // Compute two feasible joint configurations based on the joint limits.
  eigenmath::VectorNd jpos_1, jpos_2;
  {
    intrinsic::icon::Client client(icon_channel);
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

    // The offset from the joint range center is proportional to the joint range
    // to avoid going outside the range in case it is very small.
    jpos_1 = center_pos + (joint_range / 5.0).cwiseMin(0.5);
    jpos_2 = center_pos;
  }

  std::vector<double> zero_velocity(kNDof, 0.0);

  INTRINSIC_ASSIGN_OR_RETURN(
      std::unique_ptr<intrinsic::icon::Session> session,
      intrinsic::icon::Session::Start(icon_channel, {std::string(part_name)}));

  intrinsic::icon::ActionDescriptor jmove1 =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          intrinsic::icon::ActionInstanceId(1), part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              jpos_1, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(
                      intrinsic::icon::ActionInstanceId(2)));
  intrinsic::icon::ActionDescriptor jstop =
      intrinsic::icon::ActionDescriptor(intrinsic::icon::kStopAction,
                                        intrinsic::icon::ActionInstanceId(2),
                                        part_name)
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(
                      intrinsic::icon::ActionInstanceId(3)));
  intrinsic::icon::ActionDescriptor jmove2 =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          intrinsic::icon::ActionInstanceId(3), part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              jpos_2, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithWatcherOnCondition(
                      [&session]() { session->QuitWatcherLoop(); }));
  INTRINSIC_ASSIGN_OR_RETURN(auto actions,
                             session->AddActions({jmove1, jstop, jmove2}));
  LOG(INFO) << "Starting motion";
  INTRINSIC_RETURN_IF_ERROR(session->StartAction(actions.front()));
  INTRINSIC_RETURN_IF_ERROR(session->RunWatcherLoop());
  LOG(INFO) << "Finished motion";
  return absl::OkStatus();
}

}  // namespace intrinsic::icon::examples
