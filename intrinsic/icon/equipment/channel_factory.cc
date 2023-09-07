// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/equipment/channel_factory.h"

#include <memory>
#include <utility>

#include "absl/status/statusor.h"
#include "absl/time/time.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/grpc/connection_params.h"

namespace intrinsic {
namespace icon {

absl::StatusOr<std::shared_ptr<ChannelInterface>> ChannelFactory::MakeChannel(
    const ConnectionParams& params) const {
  return MakeChannel(params, kGrpcClientConnectDefaultTimeout);
}

absl::StatusOr<std::shared_ptr<ChannelInterface>>
DefaultChannelFactory::MakeChannel(const ConnectionParams& params,
                                   absl::Duration timeout) const {
  return Channel::Make(params, timeout);
}

}  // namespace icon
}  // namespace intrinsic
