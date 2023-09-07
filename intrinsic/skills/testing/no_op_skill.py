# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""A skill that always returns OK and has an empty equipment set."""

from typing import Mapping, Optional

from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import skill_service_pb2
from intrinsic.skills.python import skill_interface as skl
from intrinsic.skills.testing import no_op_skill_pb2
from intrinsic.util.decorators import overrides


class NoOpSkill(skl.Skill):
  """Skill that always returns OK and has an empty equipment set."""

  @classmethod
  @overrides(skl.Skill)
  def required_equipment(cls) -> Mapping[str, equipment_pb2.EquipmentSelector]:
    """See base class."""
    return {}

  @classmethod
  @overrides(skl.Skill)
  def name(cls) -> str:
    """See base class."""
    return "no_op"

  @classmethod
  @overrides(skl.Skill)
  def package(cls) -> str:
    """See base class."""
    return "ai.intrinsic"

  @overrides(skl.Skill)
  def get_parameter_descriptor(self) -> descriptor.Descriptor:
    """See base class."""
    return no_op_skill_pb2.NoOpSkillParams.DESCRIPTOR

  @classmethod
  @overrides(skl.Skill)
  def default_parameters(cls) -> Optional[message.Message]:
    """See base class."""
    return no_op_skill_pb2.NoOpSkillParams(foo="foo")

  @overrides(skl.Skill)
  def execute(
      self,
      request: skl.ExecuteRequest[no_op_skill_pb2.NoOpSkillParams],
      context: skl.ExecutionContext,
  ) -> skill_service_pb2.ExecuteResult:
    """See base class."""
    return skill_service_pb2.ExecuteResult()

  @overrides(skl.Skill)
  def get_footprint(
      self, params: skl.Skill.ProjectParams, context: skl.ProjectionContext
  ) -> skill_service_pb2.ProjectResult:
    """See base class."""
    return skill_service_pb2.ProjectResult()
