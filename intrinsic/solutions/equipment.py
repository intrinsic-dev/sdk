# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Equipment access.

Typical usage example:
  from intrinsic.solutions import deployments

  solution = deployments.connect()
  equipment = solution.equipment
  say = solution.skills.say(
      text='Hello World',
      device=equipment.some_speaker
  )
  solution.executive.run(say)
"""

import re
from typing import Dict, Iterator, List, Optional, Union

from intrinsic.skills.proto import equipment_pb2
from intrinsic.solutions import equipment_registry as equipment_registry_mod

_REGEX_INVALID_PYTHON_VAR_CHARS = r"\W|^(?=\d)"


def equipment_to_python_name(handle_name: str):
  # Replace characters which are not valid in Python names
  # This is to enable equipment.TypeOfEquipment.EquipmentName for any,
  # equipment, in particular ICON robot names contain "::"
  return re.sub(_REGEX_INVALID_PYTHON_VAR_CHARS, "_", handle_name)


class EquipmentHandle:
  """Lightweight wrapper for EquipmentHandle proto.

  An equipment handle describes a piece of equipment in the solution, e.g.,
  a robot. It consists of a name and types. An equipment satisfies every
  listed type requirement. A skill defines the required types via selectors.
  A matching equipment's types must be a subset of the required types.
  """

  def __init__(self, proto: equipment_pb2.EquipmentHandle):
    """Constructs an EquipmentHandle.

    Args:
      proto: EquipmentHandle proto to wrap.
    """
    self._proto: equipment_pb2.EquipmentHandle = proto

  @classmethod
  def create(cls, name: str, types: List[str]) -> "EquipmentHandle":
    """Creates a new EquipmentHandle.

    Args:
      name: Name of equipment.
      types: Types of the equipment.

    Returns:
      Equipment handle initialized according to the given arguments.
    """
    proto = equipment_pb2.EquipmentHandle(name=name)
    for t in types:
      proto.equipment_data[t].CopyFrom(
          equipment_pb2.EquipmentHandle.EquipmentData()
      )
    return EquipmentHandle(proto)

  @property
  def name(self) -> str:
    return self._proto.name

  @property
  def types(self) -> List[str]:
    return list(self._proto.equipment_data.keys())

  @property
  def proto(self) -> equipment_pb2.EquipmentHandle:
    return self._proto

  def __repr__(self) -> str:
    types_str = ", ".join(['"%s"' % t for t in sorted(self.types)])
    return f'EquipmentHandle.create(name="{self.name}", types=[{types_str}])'


class EquipmentList:
  """List container for equipment handles."""

  def __init__(self, equipment: List[EquipmentHandle]):
    """Constructs new EquipmentList.

    Args:
      equipment: Initial equipment to add.
    """
    self._equipment: Dict[str, EquipmentHandle] = {}
    for e in equipment:
      self.append(e)

  def append(self, handle: EquipmentHandle) -> None:
    """Append a handle."""
    self._equipment[handle.name] = handle

    clean_name = equipment_to_python_name(handle.name)
    if clean_name != handle.name:
      self._equipment[clean_name] = handle

  def __getitem__(self, name: str) -> EquipmentHandle:
    if name not in self._equipment:
      raise AttributeError(f"Equipment {name} not registered")
    return self._equipment[name]

  def __setitem__(self, name: str, handle: EquipmentHandle) -> None:
    self._equipment[name] = handle

  def __getattr__(self, name: str) -> EquipmentHandle:
    if name not in self._equipment:
      raise AttributeError(f"Equipment {name} not registered")
    return self._equipment[name]

  def __dir__(self) -> List[str]:
    return sorted(
        filter(
            lambda x: not re.search(_REGEX_INVALID_PYTHON_VAR_CHARS, x),
            self._equipment.keys(),
        )
    )

  def __len__(self) -> int:
    # self._equipment may contain an equipment twice if the name had to be
    # mangled to make it compatible with attr access. Therefore, call __dir__,
    # to get the unique elements and count them.
    return len(self.__dir__())

  def __iter__(self) -> Iterator[EquipmentHandle]:
    for name in self.__dir__():
      yield self.__getattr__(name)

  def __str__(self) -> str:
    return f"EquipmentList[{', '.join(self._equipment.keys())}]"


class Equipment:
  """Wrapper to easily access equipment from a solution."""

  def __init__(
      self,
      equipment_registry: Optional[
          equipment_registry_mod.EquipmentRegistry
      ] = None,
  ):
    """Constructs new Equipment.

    Args:
      equipment_registry: Equipment registry to fetch equipment from. This is
        optional, if not given, no equipment will be retrieved from the
        registry. You may then use append() to add equipment manually.

    Raises:
      grpc.RpcError: If gRPC call to equipment registry fails.
    """
    self._equipment_registry: equipment_registry_mod.EquipmentRegistry = (
        equipment_registry  # pytype: disable=annotation-type-mismatch  # attribute-variable-annotations
    )
    self._equipment: EquipmentList = EquipmentList([])
    self.update()

  def update(self) -> None:
    """Fetches current equipment from registry.

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    if self._equipment_registry is None:
      return

    equipment = self._equipment_registry.list_equipment()
    self._equipment = EquipmentList([])
    for e in equipment:
      self._equipment.append(EquipmentHandle(e))

  def append(
      self,
      handle_or_proto: Union[EquipmentHandle, equipment_pb2.EquipmentHandle],
  ) -> None:
    """Append a handle to the equipment.

    If an item is appended with special characters not allowed in Python
    field names, it generates a sanitized version replacing special
    characters by underscores. Consider a handle called "special:name". It
    will be accessible through:
    list.special_name
    list["special_name"]
    list["special:name"]
    The handle's proto will always contain special:name as its name.

    This may be used to create a local equipment registry not backed by an
    equipment registry. This can be useful for testing.

    Args:
      handle_or_proto: Equipment handle to add, either wrapper or proto
    """
    handle: EquipmentHandle = None
    if isinstance(handle_or_proto, EquipmentHandle):
      handle = handle_or_proto
    elif isinstance(handle_or_proto, equipment_pb2.EquipmentHandle):
      handle = EquipmentHandle(proto=handle_or_proto)
    else:
      raise TypeError("Invalid argument type")

    self._equipment.append(handle)

  def __getitem__(self, name: str) -> EquipmentHandle:
    return self._equipment[name]

  def __getattr__(self, name: str) -> EquipmentHandle:
    return self._equipment[name]

  def __dir__(self) -> List[str]:
    return dir(self._equipment)

  def __str__(self) -> str:
    return str(self._equipment)
