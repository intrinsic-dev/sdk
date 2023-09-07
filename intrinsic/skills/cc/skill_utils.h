// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_CC_SKILL_UTILS_H_
#define INTRINSIC_SKILLS_CC_SKILL_UTILS_H_

#include <memory>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/proto/any.h"

namespace intrinsic {
namespace skills {

// Unpacks parameters from the request (execute or project), into a message of
// the type Params. Returns an INVALID_ARGUMENT error if the type of the
// `parameters` does not match `Params`.
template <typename Params>
absl::StatusOr<Params> UnpackParams(
    const intrinsic_proto::skills::ExecuteRequest& execute_request) {
  return UnpackAny<Params>(execute_request.parameters());
}

template <typename Params>
absl::StatusOr<Params> UnpackParams(
    const intrinsic_proto::skills::ProjectRequest& project_request) {
  return UnpackAny<Params>(project_request.parameters());
}

absl::StatusOr<ConnectionParams> GetConnectionParamsFromHandle(
    const intrinsic_proto::skills::EquipmentHandle& handle);

// Creates client channel for communicating with equipment.
absl::StatusOr<std::shared_ptr<intrinsic::Channel>> CreateChannelFromHandle(
    const intrinsic_proto::skills::EquipmentHandle& handle);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_UTILS_H_
