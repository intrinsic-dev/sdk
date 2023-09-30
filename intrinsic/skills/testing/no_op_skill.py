# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""A skill that always returns OK and has an empty equipment set."""

from intrinsic.skills.proto import footprint_pb2
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
  ) -> None:
    """See base class."""
    return None

  @overrides(skl.Skill)
  def get_footprint(
      self,
      params: skl.GetFootprintRequest[no_op_skill_pb2.NoOpSkillParams],
      context: skl.GetFootprintContext,
  ) -> footprint_pb2.Footprint:
    """See base class."""
    return footprint_pb2.Footprint()
