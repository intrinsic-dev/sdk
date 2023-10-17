// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_DEFAULT_PARAMETERS_H_
#define INTRINSIC_SKILLS_INTERNAL_DEFAULT_PARAMETERS_H_

#include <memory>

#include "absl/status/statusor.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic::skills {

// Extracts the parameters, then applies defaults to parameters.
absl::StatusOr<std::unique_ptr<google::protobuf::Message>> ApplyDefaults(
    const google::protobuf::Any& defaults,
    const google::protobuf::Message& params);

// Packs the parameters that may have defaults into Any.
absl::StatusOr<google::protobuf::Any> PackParametersWithDefaults(
    const intrinsic_proto::skills::SkillInstance& instance,
    const google::protobuf::Message& params);

}  // namespace intrinsic::skills

#endif  // INTRINSIC_SKILLS_INTERNAL_DEFAULT_PARAMETERS_H_
