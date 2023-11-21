# Copyright 2023 Intrinsic Innovation LLC

"""SkillLoggingContext for storing skill information useful in logs."""

import dataclasses

from intrinsic.logging.proto import context_pb2


@dataclasses.dataclass(frozen=True)
class SkillLoggingContext:
  """Provides logging information for a skill.

  Attributes:
    data_logger_context: The logging context of the execution.
    skill_id: The id of the skill.
  """

  data_logger_context: context_pb2.Context
  skill_id: str
