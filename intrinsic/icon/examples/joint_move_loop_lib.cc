// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/examples/joint_move_loop_lib.h"

#include <memory>
#include <optional>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/actions/point_to_point_move_info.h"
#include "intrinsic/icon/cc_client/client_utils.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/examples/joint_move_positions.pb.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/eigen.h"

namespace intrinsic::icon::examples {

absl::Status RunJointMoveLoop(
    absl::string_view part_name, absl::Duration duration,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel,
    std::optional<intrinsic_proto::icon::JointMovePositions>
        joint_move_positions) {
  intrinsic::icon::Client client(icon_channel);
  INTRINSIC_ASSIGN_OR_RETURN(auto robot_config, client.GetConfig());
  INTRINSIC_ASSIGN_OR_RETURN(auto part_config,
                             robot_config.GetGenericPartConfig(part_name));
  INTRINSIC_ASSIGN_OR_RETURN(
      JointLimits joint_limits,
      intrinsic::FromProto(
          part_config.joint_limits_config().application_limits()));

  std::vector<double> jpos_1;
  std::vector<double> jpos_2;
  std::vector<double> zero_velocity(joint_limits.size(), 0.0);

  if (!joint_move_positions.has_value()) {
    // Compute two feasible joint configurations based on the joint limits.
    {
      eigenmath::VectorNd joint_range =
          joint_limits.max_position - joint_limits.min_position;
      eigenmath::VectorNd center_pos =
          joint_limits.min_position + (joint_range / 2.0);

      // The offset from the joint range center is proportional to the joint
      // range to avoid going outside the range in case it is very small.
      jpos_1 = intrinsic::VectorNdToVector(center_pos +
                                           (joint_range / 5.0).cwiseMin(0.5));
      jpos_2 = intrinsic::VectorNdToVector(center_pos);
    }
  } else {
    if (joint_move_positions->joint_positions_1_size() !=
        joint_move_positions->joint_positions_2_size()) {
      return absl::InvalidArgumentError(
          "Specified joint values must be equal in size.");
    }
    if (joint_move_positions->joint_positions_1_size() != joint_limits.size()) {
      return absl::InvalidArgumentError(absl::StrCat(
          "Specified joint values must be of size ", joint_limits.size()));
    }
    jpos_1 =
        std::vector<double>(joint_move_positions->joint_positions_1().begin(),
                            joint_move_positions->joint_positions_1().end());
    jpos_2 =
        std::vector<double>(joint_move_positions->joint_positions_2().begin(),
                            joint_move_positions->joint_positions_2().end());
  }

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
  intrinsic::icon::ActionDescriptor jmove2 =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::PointToPointMoveInfo::kActionTypeName,
          intrinsic::icon::ActionInstanceId(2), part_name)
          .WithFixedParams(intrinsic::icon::CreatePointToPointMoveFixedParams(
              jpos_2, zero_velocity))
          .WithReaction(
              intrinsic::icon::ReactionDescriptor(intrinsic::icon::IsDone())
                  .WithRealtimeActionOnCondition(
                      intrinsic::icon::ActionInstanceId(1)));
  INTRINSIC_ASSIGN_OR_RETURN(auto actions,
                             session->AddActions({jmove1, jmove2}));
  LOG(INFO) << "Starting motion";
  INTRINSIC_RETURN_IF_ERROR(session->StartAction(actions.front()));

  // As the actions above form a loop, RunWatcherLoop is started with a
  // deadline. Once the deadline is reached, the session is closed and ICON
  // switches to the default action (stop) for the part. The default action
  // smoothly stops the part, as the switch is likely to happen while a
  // joint_move action is active.
  const auto& loop_status = session->RunWatcherLoop(absl::Now() + duration);
  // Ignore the expected DeadlineExceeded error.
  if (loop_status.code() != absl::StatusCode::kDeadlineExceeded) {
    return loop_status;
  }

  return absl::OkStatus();
}

}  // namespace intrinsic::icon::examples
