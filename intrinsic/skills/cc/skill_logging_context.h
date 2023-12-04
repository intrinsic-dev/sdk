// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_SKILL_LOGGING_CONTEXT_H_
#define INTRINSIC_SKILLS_CC_SKILL_LOGGING_CONTEXT_H_

#include "absl/strings/string_view.h"
#include "intrinsic/logging/proto/context.pb.h"

namespace intrinsic {
namespace skills {

// Provides logging information for a skill.
struct SkillLoggingContext {
  // The skill logging context.
  const intrinsic_proto::data_logger::Context data_logger_context;

  // The skill id.
  const absl::string_view skill_id;
};
}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_LOGGING_CONTEXT_H_
