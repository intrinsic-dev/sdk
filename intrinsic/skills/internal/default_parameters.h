// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_DEFAULT_PARAMETERS_H_
#define INTRINSIC_SKILLS_INTERNAL_DEFAULT_PARAMETERS_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/message.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic::skills {

// For any field set in `from` that isn't set in `to`, copies the field from
// `from` to `to`, except for unknown fields. For fields that are submessages,
// presence of the submessage is checked, and if copied, copies the entire
// submessage from `from`, does not check for presence of fields in submessage.
//
// Singular fields are only considered set if
// google::protobuf::Reflection::HasField(field) would return true, and repeated
// fields will only be listed if google::protobuf::Reflection::FieldSize(field)
// would return non-zero.
absl::Status MergeUnset(const google::protobuf::Message& from,
                        google::protobuf::Message& to);

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
