// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/examples/adio_lib.h"

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
#include "intrinsic/icon/actions/adio.pb.h"
#include "intrinsic/icon/actions/adio_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/session.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/part_status.pb.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

using ::intrinsic::icon::ADIOActionInfo;
using ::xfa::icon::actions::proto::DigitalBlock;

absl::Status PrintADIOStatus(absl::string_view part_name,
                             intrinsic::icon::Client& icon_client) {
  INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartStatus status,
                             icon_client.GetSinglePartStatus(part_name));

  std::cout << "Status for Part '" << part_name << "'" << std::endl
            << absl::StrCat(status) << std::endl;
  return absl::OkStatus();
}

ADIOActionInfo::FixedParams CreateActionParameters(
    size_t num_values, bool value, absl::string_view output_block_name) {
  ADIOActionInfo::FixedParams params;
  DigitalBlock block;
  // Set the lowest `num_values` outputs of the block to the requested value.
  for (size_t i = 0; i < num_values; ++i) {
    (*block.mutable_values_by_index())[i] = value;
  }
  // Set the output block.
  (*params.mutable_outputs()->mutable_digital_outputs())[output_block_name] =
      block;
  return params;
}

absl::Status SendDigitalOutput(
    absl::string_view part_name,
    const ADIOActionInfo::FixedParams& action_parameters,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::unique_ptr<intrinsic::icon::Session> session,
      intrinsic::icon::Session::Start(icon_channel, {std::string(part_name)}));

  constexpr ReactionHandle kOutputsSetHandle(0);

  intrinsic::icon::ActionDescriptor adio_action =
      intrinsic::icon::ActionDescriptor(
          intrinsic::icon::ADIOActionInfo::kActionTypeName,
          intrinsic::icon::ActionInstanceId(1), part_name)
          .WithFixedParams(action_parameters)
          .WithReaction(intrinsic::icon::ReactionDescriptor(
                            intrinsic::icon::IsTrue(
                                intrinsic::icon::ADIOActionInfo::kOutputsSet))
                            .WithHandle(kOutputsSetHandle));

  INTRINSIC_ASSIGN_OR_RETURN(intrinsic::icon::Action action,
                             session->AddAction(adio_action));
  LOG(INFO) << "Sending output command to part: " << part_name;
  INTRINSIC_RETURN_IF_ERROR(session->StartAction(action));
  INTRINSIC_RETURN_IF_ERROR(
      session->RunWatcherLoopUntilReaction(kOutputsSetHandle));
  LOG(INFO) << "Successfully executed output command on part: " << part_name;
  return absl::OkStatus();
}

absl::Status ExampleSetDigitalOutput(
    absl::string_view part_name, absl::string_view output_block_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  if (part_name.empty()) {
    return absl::FailedPreconditionError("No part name provided.");
  }

  intrinsic::icon::Client client(icon_channel);

  // Create a command to set the lowest two bits to `true`;
  ADIOActionInfo::FixedParams set_bits = CreateActionParameters(
      /*num_values=*/2, /*value=*/true, output_block_name);
  // Create a command to set the lowest two bits to `false`;
  ADIOActionInfo::FixedParams clear_bits = CreateActionParameters(
      /*num_values=*/2, /*value=*/false, output_block_name);

  INTRINSIC_RETURN_IF_ERROR(
      SendDigitalOutput(part_name, set_bits, icon_channel));
  LOG(INFO) << "The lowest two bits are set.";
  INTRINSIC_RETURN_IF_ERROR(PrintADIOStatus(part_name, client));
  LOG(INFO) << "Waiting 10s before clearing the lowest two bits.";
  absl::SleepFor(absl::Seconds(10));
  INTRINSIC_RETURN_IF_ERROR(
      SendDigitalOutput(part_name, clear_bits, icon_channel));
  return PrintADIOStatus(part_name, client);
}

}  // namespace intrinsic::icon::examples
