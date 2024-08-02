// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/examples/adio_lib.h"

#include <stddef.h>

#include <cstdint>
#include <iostream>
#include <memory>
#include <ostream>
#include <string>
#include <vector>

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
#include "intrinsic/icon/proto/io_block.pb.h"
#include "intrinsic/icon/proto/part_status.pb.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon::examples {

using ::intrinsic::icon::ADIOActionInfo;
using ::xfa::icon::actions::proto::DigitalBlock;

absl::StatusOr<intrinsic_proto::icon::PartStatus> GetPartStatus(
    absl::string_view part_name, intrinsic::icon::Client& icon_client) {
  return icon_client.GetSinglePartStatus(part_name);
}

absl::StatusOr<uint64_t> GetBlockSize(
    absl::string_view part_name, absl::string_view block_name,
    const intrinsic_proto::icon::PartStatus& part_status) {
  if (!part_status.has_adio_state()) {
    return absl::NotFoundError(absl::StrCat("PartStatus for part '", part_name,
                                            "' is missing ADIO state."));
  }
  const auto& adio_state = part_status.adio_state();
  if (!adio_state.digital_outputs().contains(block_name)) {
    return absl::NotFoundError(absl::StrCat(
        "PartStatus for part '", part_name,
        "' is missing digital output block with name '", block_name, "'."));
  }

  return adio_state.digital_outputs().at(block_name).signals().size();
}

absl::Status PrintADIOStatus(absl::string_view part_name,
                             intrinsic::icon::Client& icon_client) {
  auto status = GetPartStatus(part_name, icon_client);
  if (!status.ok()) {
    return status.status();
  }

  std::cout << "Status for Part '" << part_name << "'" << std::endl
            << absl::StrCat(status.value()) << std::endl;
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

absl::StatusOr<std::vector<ADIOActionInfo::FixedParams>>
CreateAnimationParameterSequence(
    absl::string_view part_name, absl::string_view block_name,
    const intrinsic_proto::icon::PartStatus& part_status) {
  std::vector<ADIOActionInfo::FixedParams> params;

  // Try to get the block size. Use a size of 2 if we fail.
  uint64_t block_size =
      GetBlockSize(part_name, block_name, part_status).value_or(2);
  params.reserve(block_size + 1);
  // Turn on one bit at a time until all bits are on.
  for (size_t i = 0; i < block_size; ++i) {
    params.push_back(CreateActionParameters(/*num_values=*/i + 1,
                                            /*value=*/true, block_name));
  }
  // Turn all bits off again.
  params.push_back(CreateActionParameters(/*num_values=*/block_size,
                                          /*value=*/false, block_name));
  return params;
}

absl::Status SendDigitalOutput(
    absl::string_view part_name,
    const ADIOActionInfo::FixedParams& action_parameters,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel) {
  INTR_ASSIGN_OR_RETURN(
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

  INTR_ASSIGN_OR_RETURN(intrinsic::icon::Action action,
                        session->AddAction(adio_action));
  LOG(INFO) << "Sending output command to part: " << part_name;
  INTR_RETURN_IF_ERROR(session->StartAction(action));
  INTR_RETURN_IF_ERROR(session->RunWatcherLoopUntilReaction(kOutputsSetHandle));
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

  INTR_ASSIGN_OR_RETURN(auto part_status, GetPartStatus(part_name, client));

  INTR_ASSIGN_OR_RETURN(auto animation_params,
                        CreateAnimationParameterSequence(
                            part_name, output_block_name, part_status));

  for (const auto& params : animation_params) {
    INTR_RETURN_IF_ERROR(SendDigitalOutput(part_name, params, icon_channel));
    absl::SleepFor(absl::Seconds(0.5));
  }

  return PrintADIOStatus(part_name, client);
}

}  // namespace intrinsic::icon::examples
