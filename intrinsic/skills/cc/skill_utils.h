// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_CC_SKILL_UTILS_H_
#define INTRINSIC_SKILLS_CC_SKILL_UTILS_H_

#include <memory>

#include "absl/status/statusor.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"

namespace intrinsic {
namespace skills {

absl::StatusOr<ConnectionParams> GetConnectionParamsFromHandle(
    const intrinsic_proto::skills::ResourceHandle& handle);

// Creates client channel for communicating with equipment.
absl::StatusOr<std::shared_ptr<intrinsic::Channel>> CreateChannelFromHandle(
    const intrinsic_proto::skills::ResourceHandle& handle);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_UTILS_H_
