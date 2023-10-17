// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_SKILL_REGISTRATION_H_
#define INTRINSIC_SKILLS_CC_SKILL_REGISTRATION_H_

#include <functional>
#include <memory>
#include <string>

#include "intrinsic/skills/internal/registerer_skill_repository.h"

// This macro should be used to register your skill so that it can be served by
// name by a skill service.
#define REGISTER_SKILL(name, alias, fn) \
  int kUnusedRegistrationResult_##name = RegisterSkill(#name, alias, fn)

#endif  // INTRINSIC_SKILLS_CC_SKILL_REGISTRATION_H_
