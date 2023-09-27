# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""A skill that always returns OK and has an empty equipment set."""

from intrinsic.skills.proto import skill_service_pb2
from intrinsic.skills.python import skill_interface as skl
from intrinsic.skills.testing import no_op_skill_pb2
from intrinsic.util.decorators import overrides


class NoOpSkill(skl.Skill):
  """Skill that always returns OK and has an empty equipment set."""

  @overrides(skl.Skill)
  def execute(
      self,
      request: skl.ExecuteRequest[no_op_skill_pb2.NoOpSkillParams],
      context: skl.ExecuteContext,
  ) -> skill_service_pb2.ExecuteResult:
    """See base class."""
    return skill_service_pb2.ExecuteResult()

  @overrides(skl.Skill)
  def get_footprint(
      self,
      params: skl.GetFootprintRequest[no_op_skill_pb2.NoOpSkillParams],
      context: skl.ProjectionContext,
  ) -> skill_service_pb2.GetFootprintResult:
    """See base class."""
    return skill_service_pb2.GetFootprintResult()
