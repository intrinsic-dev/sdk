# Copyright 2023 Intrinsic Innovation LLC

"""Abstract base classes for skill and resource providers."""

import abc
from typing import Any, List, Type, Union

from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.solutions import provided


class ResourceProvider(abc.ABC):
  """Provides access resources from a solution."""

  @abc.abstractmethod
  def update(self) -> None:
    """Fetches current resources from registry.

    Raises:
      grpc.RpcError: When gRPC call to resource registry fails.
    """
    ...

  @abc.abstractmethod
  def append(
      self,
      handle_or_proto: Union[
          provided.ResourceHandle, resource_handle_pb2.ResourceHandle
      ],
  ) -> None:
    """Appends a handle to the resources.

    If an item is appended with special characters not allowed in Python
    field names, it generates a sanitized version replacing special
    characters by underscores. Consider a handle called "special:name". It
    will be accessible through:
    list.special_name
    list["special_name"]
    list["special:name"]
    The handle's proto will always contain special:name as its name.

    Args:
      handle_or_proto: Resource handle to add, either wrapper or proto
    """
    ...

  @abc.abstractmethod
  def __getitem__(self, name: str) -> provided.ResourceHandle:
    """Returns the resource handle for the given name."""
    ...

  @abc.abstractmethod
  def __getattr__(self, name: str) -> provided.ResourceHandle:
    """Returns the resource handle for the given name."""
    ...

  @abc.abstractmethod
  def __dir__(self) -> list[str]:
    """Returns the names of the available resources in sorted order.

    Only returns names which are valid Python identifiers.
    """
    ...

  @abc.abstractmethod
  def __str__(self) -> str:
    ...


class SkillProvider(abc.ABC):
  """A container that provides access to the skills of a solution.

  Skill providers are directly user-facing. Hence `__dir__` and `__getattr__`
  may be used by auto-completion and must adhere to the standard interface,
  which this abstract base class enforces.
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
  def __getattr__(self, name: str) -> Union[Type[Any], provided.SkillPackage]:
    """Returns the global skill class or skill package with the given name."""
    raise NotImplementedError("Skill provider did not implement __getattr__")

  @abc.abstractmethod
  def __getitem__(self, skill_name: str) -> Type[Any]:
    """Returns the skill class or with the given skill id."""
    raise NotImplementedError("Skill provider did not implement __getitem__")
