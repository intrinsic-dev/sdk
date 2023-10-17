// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_INIT_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_INIT_H_

#include <cstdint>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/skills/internal/skill_repository.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"

namespace intrinsic::skills {

// Starts the skill services on a gRPC server at port `skill_service_port`. This
// server hosts services required for serving a skill including:
// * SkillProjectorService
// * SkillExecutorService
// * SkillInformationService
//
// Establishes connections to common clients of skills.
// The `connection_timeout` applies to the establishment of each connection, not
// the cumulative connection time.
//
// The skills services are configured using the proto data contained in the
// service_config.
//
// If setup passes, this method does not return until the gRPC skill server is
// shutdown. This normally occurs when the process is killed.
//
// Returns early on error.
absl::Status SkillInit(
    const intrinsic_proto::skills::SkillServiceConfig& service_config,
    absl::string_view data_logger_grpc_service_address,
    absl::string_view world_service_address,
    absl::string_view geometry_service_address,
    absl::string_view motion_planner_service_address,
    absl::string_view skill_registry_service_address,
    int32_t skill_service_port, absl::Duration connection_timeout,
    SkillRepository& skill_repository);

// Returns the SkillServiceConfig at `skill_service_config_filename`.
//
// Reads the proto binary file at `skill_service_config_filename` and returns
// the contents. This file must contain a proto binary
// intrinsic_proto.skills.SkillServiceConfig message.
absl::StatusOr<intrinsic_proto::skills::SkillServiceConfig>
GetSkillServiceConfig(absl::string_view skill_service_config_filename);

}  // namespace intrinsic::skills

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_INIT_H_
