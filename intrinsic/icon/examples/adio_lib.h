// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_EXAMPLES_ADIO_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_ADIO_LIB_H_

#include <cstddef>
#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/actions/adio_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// Requests the status for `part_name` and prints it to std::cout.
// Returns NotFoundError if no status for that part is returned.
absl::Status PrintADIOStatus(absl::string_view part_name,
                             intrinsic::icon::Client& icon_client);

// Creates ADIO Action parameters to set the lowest `num_values` bits to `value`
// for the output block named `output_block_name`.
ADIOActionInfo::FixedParams CreateActionParameters(
    size_t num_values, bool value, absl::string_view output_block_name);

// Opens a session for `part_name`, sends the command defined by
// `action_parameters` and waits for the condition ADIOActionInfo::kOutputsSet.
absl::Status SendDigitalOutput(
    absl::string_view part_name,
    const ADIOActionInfo::FixedParams& action_parameters,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);

// Sets the two lowest bits of 'output_block' of `part_name` to high, prints
// the part status to std::cout, then waits 10s, clears the output bits and
// prints the part status to std::cout.
absl::Status ExampleSetDigitalOutput(
    absl::string_view part_name, absl::string_view output_block_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_ADIO_LIB_H_
