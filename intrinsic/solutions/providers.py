# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Skill provider base class.

This provides the generic abstract base class (ABC) for such providers.
"""

import abc
from typing import Any, Dict, List, Set, Type

from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import equipment as equipment_mod
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions


class SkillInfo(abc.ABC):
  """Containes information about a Skill.

  Attributes:
    id: Skill ID.
    skill_proto: proto with skill information that this instance represents.
    field_names: names of top-level fields in parameter proto.
    message_classes: mapping from type names to default messages for that type.
  """

  @property
  @abc.abstractmethod
  def id(self) -> str:
    raise NotImplementedError("Abstract method not implemented")

  @property
  @abc.abstractmethod
  def skill_proto(self) -> skills_pb2.Skill:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def create_param_message(self) -> message.Message:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def create_result_message(self) -> message.Message:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def get_result_message_type(self) -> Type[message.Message]:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def parameter_descriptor(self) -> descriptor.Descriptor:
    raise NotImplementedError("Abstract method not implemented")

  @property
  @abc.abstractmethod
  def field_names(self) -> Set[str]:
    raise NotImplementedError("Abstract method not implemented")

  @property
  @abc.abstractmethod
  def message_classes(self) -> Dict[str, Type[message.Message]]:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def get_message_class(self, msg_descriptor: descriptor.Descriptor):
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def get_parameter_field_comments(self, full_field_name: str) -> str:
    """Returns the leading_comments associated with the field in the proto.

    Args:
      full_field_name: The full name of the field.

    Raises:
      status.StatusNotOk if the field does not exist or there is no
      source_code_info in the associated FileDescriptor.
    """
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def get_result_field_comments(self, full_field_name: str) -> str:
    """Returns the leading_comments associated with the field in the proto.

    Args:
      full_field_name: The full name of the field.

    Raises:
      status.StatusNotOk if the field does not exist or there is no
      source_code_info in the associated FileDescriptor.
    """
    raise NotImplementedError("Abstract method not implemented")


class SkillCompatibleEquipmentMap:
  """Map from equipment slot name to equipment list.

  Used for convenient auto-completion.
  """

  def __init__(self, equipment: Dict[str, equipment_mod.EquipmentList]):
    self._equipment: Dict[str, equipment_mod.EquipmentList] = equipment

  def __dir__(self) -> List[str]:
    return [str(k) for k in self._equipment.keys()]

  def __contains__(self, equipment_slot: str) -> bool:
    return equipment_slot in self._equipment

  def __getitem__(self, equipment_slot: str) -> equipment_mod.EquipmentList:
    if equipment_slot not in self._equipment:
      raise AttributeError(
          f"Equipment {equipment_slot} not compatible or unknown"
      )
    return self._equipment[equipment_slot]

  def __getattr__(self, equipment_slot: str) -> equipment_mod.EquipmentList:
    if equipment_slot not in self._equipment:
      raise AttributeError(
          f"Equipment {equipment_slot} not compatible or unknown"
      )
    return self._equipment[equipment_slot]


class SkillBase(actions.ActionBase):
  """Base class for skills provided by SkillProvider below."""

  @property
  @abc.abstractmethod
  def result_key(self) -> str:
    """Returns the key with which the result can be accessed on the blackboard.

    Returns:
      Result key on blackboard.
    """
    raise NotImplementedError("Abstract method not implemented")

  @property
  @abc.abstractmethod
  def result(self) -> blackboard_value.BlackboardValue:
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def set_plan_param(self, param_name: str, param_value: str) -> None:
    """Sets planning-specific parameter for skill.

    This sets planning specific parameters based on operators associated with
    this skill. Consider the following operator
    (:action pick-up
     :parameters (?b - block)
     ...)

    Here you can set the parameter ?b (pass "b" as param_name) to the name of
    an object of type block.

    Args:
      param_name: name of operator parameter (see domain operators)
      param_value: symbol to be set as value (see domain objects)
    """
    raise NotImplementedError("Abstract method not implemented")

  @abc.abstractmethod
  def __repr__(self) -> str:
    """Converts SkillBase to Python (pseudocode) representation."""
    raise NotImplementedError("Abstract method not implemented")

  @utils.classproperty
  @abc.abstractmethod
  def info(cls) -> skills_pb2.Skill:  # pylint:disable=no-self-argument
    """Get skill signature information.

    Returns:
      Skill proto with structured information.
    """
    # @classproperty requires an error-free default implementation.
    return skills_pb2.Skill()

  @utils.classproperty
  @abc.abstractmethod
  def compatible_equipment(cls) -> SkillCompatibleEquipmentMap:  # pylint:disable=no-self-argument
    """Access equipment compatible with this skill.

    Keys in the returned map are the same as the parameters to the constructor.

    Returns:
      Map from equipment slot name to equipment list.
    """
    # @classproperty requires an error-free default implementation.
    return SkillCompatibleEquipmentMap({})

  @utils.classproperty
  @abc.abstractmethod
  def skill_info(cls) -> SkillInfo:  # pylint:disable=no-self-argument
    """Access skill info for this skill.

    Returns:
      SkillInfo object associated with this skill.
    """
    # @classproperty requires an error-free default implementation.
    return None

  @utils.classproperty
  @abc.abstractmethod
  def message_classes(cls) -> Dict[str, Type[message.Message]]:  # pylint:disable=no-self-argument
    """Exposes available message classes for this skill.

    This dictionary contains a mapping of type names to the message classes
    bases on the hermetic descriptor pool for this skill.

    Returns:
      A dictionary mapping proto names to the message classes.
    """
    # @classproperty requires an error-free default implementation.
    return {}


class SkillProvider(abc.ABC):
  """Abstract base class for generators that provide skills.

  Skill providers are directly user-facing in Jupyter. Hence `__dir__` and
  `__getattr__` are used by auto-completion and must adhere to the standard
  interface, which this abstract base class enforces.
  """

  @abc.abstractmethod
  def update(self) -> None:
    """Refreshes the set of skills for the provider.

    This causes the provider to regenerate its set of skills. This should be
    called whenever a skill is added, deleted, or modified in a workcell."
    """

  @abc.abstractmethod
  def __dir__(self) -> List[str]:
    """Returns the names of available skills."""
    return []

  # We would like to use Type[SkillBase] instead, but Python then checks
  # the constructor parameters explicitly against SkillBase, which we don't
  # want and which is rather odd. Therefore, just state that it's a type.
  @abc.abstractmethod
  def __getattr__(self, name: str) -> Type[Any]:
    """Returns the action skill class."""
    raise NotImplementedError("Skill provider did not implement __getattr__")

  @abc.abstractmethod
  def __getitem__(self, skill_name: str) -> Type[Any]:
    raise NotImplementedError("Skill provider did not implement __getitem__")
