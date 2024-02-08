// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_
#define INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_

#include <memory>

#include "absl/status/status.h"
#include "google/protobuf/message.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
namespace skills {

// Calls a skill's Execute() method and optionally assigns its output to the
// specified result parameter.
template <typename TResult>
absl::Status ExecuteSkill(SkillExecuteInterface& skill,
                          const ExecuteRequest& request,
                          ExecuteContext& context, TResult* result) {
  INTR_ASSIGN_OR_RETURN(std::unique_ptr<::google::protobuf::Message> result_msg,
                        skill.Execute(request, context));

  if (result_msg->GetDescriptor()->full_name() !=
      TResult::descriptor()->full_name()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Skill returned result of type %s, but caller wants %s.",
        result_msg->GetDescriptor()->full_name(),
        TResult::descriptor()->full_name()));
  }
  if (result != nullptr &&
      !result->ParseFromString(result_msg->SerializeAsString())) {
    return absl::InternalError(
        "Could not parse result message as target type.");
  }

  return absl::OkStatus();
}
absl::Status ExecuteSkill(SkillExecuteInterface& skill,
                          const ExecuteRequest& request,
                          ExecuteContext& context);

// Calls a skill's Preview() method and optionally assigns its output to the
// specified result parameter.
template <typename TResult>
absl::Status PreviewSkill(SkillExecuteInterface& skill,
                          const PreviewRequest& request,
                          PreviewContext& context, TResult* result) {
  INTR_ASSIGN_OR_RETURN(std::unique_ptr<::google::protobuf::Message> result_msg,
                        skill.Preview(request, context));

  if (result_msg->GetDescriptor()->full_name() !=
      TResult::descriptor()->full_name()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Skill returned result of type %s, but caller wants %s.",
        result_msg->GetDescriptor()->full_name(),
        TResult::descriptor()->full_name()));
  }
  if (result != nullptr &&
      !result->ParseFromString(result_msg->SerializeAsString())) {
    return absl::InternalError(
        "Could not parse result message as target type.");
  }

  return absl::OkStatus();
}
absl::Status PreviewSkill(SkillExecuteInterface& skill,
                          const PreviewRequest& request,
                          PreviewContext& context);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_
