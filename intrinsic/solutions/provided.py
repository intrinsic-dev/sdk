# Copyright 2023 Intrinsic Innovation LLC

"""Base classes for everything provided by skill and resource providers."""

from __future__ import annotations

import abc
from typing import Any, Dict, Iterator, List, Set, Type, Union

from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import cel
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions

# Union of types that can be used to set a skill parameter dynamically from the
# blackboard. This type alias is useful to keep the signatures of skill and
# message wrapper classes concise.
ParamAssignment = Union[blackboard_value.BlackboardValue, cel.CelExpression]


class ResourceHandle:
  """Lightweight wrapper for ResourceHandle proto.

  A resource handle describes a resource in the solution with which a skill can
  be executed, e.g., a robot. It consists of a name and capabilities. A skill
  defines the required capabilities via selectors. A matching resource's
  capabilities must be a superset of the required capabilities.
  """

  _proto: resource_handle_pb2.ResourceHandle

  def __init__(self, proto: resource_handle_pb2.ResourceHandle):
    """Constructs a ResourceHandle.

    Args:
      proto: ResourceHandle proto to wrap.
    """
    self._proto = proto

  @classmethod
  def create(cls, name: str, capabilities: list[str]) -> "ResourceHandle":
    """Creates a new ResourceHandle.

    Args:
      name: Name of the resource.
      capabilities: Capabilities of the resources.

    Returns:
      Resource handle initialized according to the given arguments.
    """
    proto = resource_handle_pb2.ResourceHandle(name=name)
    for c in capabilities:
      proto.resource_data[c].CopyFrom(
          resource_handle_pb2.ResourceHandle.ResourceData()
      )
    return ResourceHandle(proto)

  @property
  def name(self) -> str:
    return self._proto.name

  @property
  def types(self) -> list[str]:
    return list(self._proto.resource_data.keys())

  @property
  def proto(self) -> resource_handle_pb2.ResourceHandle:
    return self._proto

  def __repr__(self) -> str:
    types_str = ", ".join(['"%s"' % t for t in sorted(self.types)])
    return f'ResourceHandle.create(name="{self.name}", types=[{types_str}])'


class ResourceList(abc.ABC):
  """A dict-like container for resource handles."""

  @abc.abstractmethod
  def append(self, handle: ResourceHandle) -> None:
    """Appends the given resource handle to this list.

    If the name of the given handle is not a valid Python identifier, it will be
    stored under it's real name and a simplified name which is a valid Pyhon
    identifier.

    Args:
      handle: The resource handle to append.
    """
    ...

  @abc.abstractmethod
  def __getitem__(self, name: str) -> ResourceHandle:
    """Returns the resource handle for the given name."""
    ...

  @abc.abstractmethod
  def __setitem__(self, name: str, handle: ResourceHandle) -> None:
    """Sets the resource handle for the given name."""
    ...

  @abc.abstractmethod
  def __getattr__(self, name: str) -> ResourceHandle:
    """Returns the resource handle for the given name."""
    ...

  @abc.abstractmethod
  def __dir__(self) -> list[str]:
    """Returns the names of the stored resource handles in sorted order.

    Only returns names which are valid Python identifiers.
    """
    ...

  @abc.abstractmethod
  def __len__(self) -> int:
    """Returns the number of stored resource handles.

    Only counts resource handles whose names are valid Python identifiers.
    """
    ...

  @abc.abstractmethod
  def __iter__(self) -> Iterator[ResourceHandle]:
    """Returns an iterator to the stored resource handles.

    The iterator only returns resource handles whose names are valid Python
    identifiers.
    """
    ...

  @abc.abstractmethod
  def __str__(self) -> str:
    ...


class SkillInfo(abc.ABC):
  """Containes information about a Skill.

  Attributes:
    id: Skill ID (e.g. 'ai.intrinsic.move_robot').
    skill_name: Skill name (e.g. 'move_robot').
    package_name: Skill package name (e.g. 'ai.intrinsic').
    skill_proto: proto with skill information that this instance represents.
    field_names: names of top-level fields in parameter proto.
    message_classes: mapping from type names to default messages for that type.
  """

  @property
  @abc.abstractmethod
  def id(self) -> str:
    ...

  @property
  @abc.abstractmethod
  def skill_name(self) -> str:
    ...

  @property
  @abc.abstractmethod
  def package_name(self) -> str:
    ...

  @property
  @abc.abstractmethod
  def skill_proto(self) -> skills_pb2.Skill:
    ...

  @abc.abstractmethod
  def create_param_message(self) -> message.Message:
    ...

  @abc.abstractmethod
  def create_result_message(self) -> message.Message:
    ...

  @abc.abstractmethod
  def get_result_message_type(self) -> Type[message.Message]:
    ...

  @abc.abstractmethod
  def parameter_descriptor(self) -> descriptor.Descriptor:
    ...

  @property
  @abc.abstractmethod
  def field_names(self) -> Set[str]:
    ...

  @property
  @abc.abstractmethod
  def message_classes(self) -> Dict[str, Type[message.Message]]:
    ...

  @abc.abstractmethod
  def get_message_class(self, msg_descriptor: descriptor.Descriptor):
    ...

  @abc.abstractmethod
  def get_parameter_field_comments(self, full_field_name: str) -> str:
    """Returns the leading_comments associated with the field in the proto.

    Args:
      full_field_name: The full name of the field.

    Raises:
      status.StatusNotOk if the field does not exist or there is no
      source_code_info in the associated FileDescriptor.
    """
    ...

  @abc.abstractmethod
  def get_result_field_comments(self, full_field_name: str) -> str:
    """Returns the leading_comments associated with the field in the proto.

    Args:
      full_field_name: The full name of the field.

    Raises:
      status.StatusNotOk if the field does not exist or there is no
      source_code_info in the associated FileDescriptor.
    """
    ...


class SkillCompatibleResourcesMap:
  """Map from resource slot name to resources list.

  Used for convenient auto-completion.
  """

  def __init__(self, resources: Dict[str, ResourceList]):
    self._resources: Dict[str, ResourceList] = resources

  def __dir__(self) -> List[str]:
    return [str(k) for k in self._resources.keys()]

  def __contains__(self, resource_slot: str) -> bool:
    return resource_slot in self._resources

  def __getitem__(self, resource_slot: str) -> ResourceList:
    if resource_slot not in self._resources:
      raise AttributeError(
          f"Resource {resource_slot} not compatible or unknown"
      )
    return self._resources[resource_slot]

  def __getattr__(self, resource_slot: str) -> ResourceList:
    if resource_slot not in self._resources:
      raise AttributeError(
          f"Resource {resource_slot} not compatible or unknown"
      )
    return self._resources[resource_slot]


class SkillBase(actions.ActionBase):
  """Base class for skills provided by SkillProvider below."""

  @property
  @abc.abstractmethod
  def result_key(self) -> str:
    """Returns the key with which the result can be accessed on the blackboard.

    Returns:
      Result key on blackboard.
    """
    ...

  @property
  @abc.abstractmethod
  def result(self) -> blackboard_value.BlackboardValue:
    ...

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
    ...

  @abc.abstractmethod
  def __repr__(self) -> str:
    """Converts SkillBase to Python (pseudocode) representation."""
    ...

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
  def compatible_resources(cls) -> SkillCompatibleResourcesMap:  # pylint:disable=no-self-argument
    """Access resources compatible with this skill.

    Keys in the returned map are the same as the parameters to the constructor.

    Returns:
      Map from resource slot name to resource list.
    """
    # @classproperty requires an error-free default implementation.
    return SkillCompatibleResourcesMap({})

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


class SkillPackage(abc.ABC):
  """A container that provides access a skill package.

  A skill package may contain skills as well as further child skill packages.
  E.g.:
    - The SkillPackage for 'foo' will contain the skill 'foo_skill' if the
      skill 'foo.foo_skill' is available in the solution."
    - The SkillPackage for 'foo' will contain the child skill package 'bar' if
      the skill 'foo.bar.bar_skill' is available in the solution.
  """

  @property
  @abc.abstractmethod
  def package_name(self) -> str:
    """Returns the full name of the skill package (e.g. 'ai.intrinsic')."""
    ...

  @property
  @abc.abstractmethod
  def relative_package_name(self) -> str:
    """Returns the name of the skill package relative to its parent package.

    For example, the package with the full package name
    "ai.intrinsic.experimental" would return "experimental".
    """
    ...

  # We would like to use Type[SkillBase] instead, but Python then checks
  # the constructor parameters explicitly against SkillBase, which we don't
  # want and which is rather odd. Therefore, just state that it's a type.
  @abc.abstractmethod
  def __getattr__(self, name: str) -> Union[Type[Any], SkillPackage]:
    """Returns the skill class or child skill package with the given name."""
    ...

  @abc.abstractmethod
  def __dir__(self) -> list[str]:
    """Returns the list of available skill classes or child skill packages."""
    ...
