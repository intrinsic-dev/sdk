// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/examples/simple_gripper_lib.h"

#include <stddef.h>

#include <iostream>
#include <memory>
#include <ostream>
#include <string>
#include <type_traits>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "absl/types/span.h"
#include "intrinsic/icon/actions/simple_gripper.pb.h"
#include "intrinsic/icon/actions/simple_gripper_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/part_status.pb.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon::examples {

absl::Status PrintPartStatus(absl::string_view part_name,
                             intrinsic::icon::Client& icon_client) {
  INTR_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartStatus status,
                        icon_client.GetSinglePartStatus(part_name));

  std::cout << "Status for Part '" << part_name << "'" << std::endl
            << absl::StrCat(status) << std::endl;
  return absl::OkStatus();
}

absl::Status SendGripperCommand(
    absl::string_view part_name,
    const SimpleGripperActionInfo::FixedParams& action_parameters,
    std::shared_ptr<ChannelInterface> icon_channel) {
  INTR_ASSIGN_OR_RETURN(std::unique_ptr<Session> session,
                        Session::Start(icon_channel, {std::string(part_name)}));

  constexpr ReactionHandle kSentCommandHandle(0);
  ActionDescriptor gripper_action =
      ActionDescriptor(SimpleGripperActionInfo::kActionTypeName,
                       ActionInstanceId(1), part_name)
          .WithFixedParams(action_parameters)
          .WithReaction(
              ReactionDescriptor(IsTrue(SimpleGripperActionInfo::kSentCommand))
                  .WithHandle(kSentCommandHandle));

  INTR_ASSIGN_OR_RETURN(Action action, session->AddAction(gripper_action));
  LOG(INFO) << "Sending command to part: " << part_name;
  INTR_RETURN_IF_ERROR(session->StartAction(action));
  INTR_RETURN_IF_ERROR(
      session->RunWatcherLoopUntilReaction(kSentCommandHandle));
  LOG(INFO) << "Successfully executed command on part: " << part_name;
  return absl::OkStatus();
}

absl::Status ExampleGraspAndRelease(
    absl::string_view part_name,
    std::shared_ptr<ChannelInterface> icon_channel) {
  if (part_name.empty()) {
    return absl::FailedPreconditionError("No part name provided.");
  }

  Client client(icon_channel);

  SimpleGripperActionInfo::FixedParams grasp;
  grasp.set_command(icon::SimpleGripperActionInfo::FixedParams::GRASP);
  INTR_RETURN_IF_ERROR(SendGripperCommand(part_name, grasp, icon_channel));
  LOG(INFO) << "Commanded GRASP";

  INTR_RETURN_IF_ERROR(PrintPartStatus(part_name, client));
  LOG(INFO) << "Waiting 10s before commanding RELEASE.";
  absl::SleepFor(absl::Seconds(10));

  SimpleGripperActionInfo::FixedParams release;
  release.set_command(icon::SimpleGripperActionInfo::FixedParams::RELEASE);
  INTR_RETURN_IF_ERROR(SendGripperCommand(part_name, release, icon_channel));
  LOG(INFO) << "Commanded RELEASE";
  return PrintPartStatus(part_name, client);
}

}  // namespace intrinsic::icon::examples
