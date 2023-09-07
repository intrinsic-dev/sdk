# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Lightweight Python wrapper around the intrinsic equipment registry."""

from __future__ import annotations

from typing import Dict, List, cast

import grpc
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import equipment_registry_pb2
from intrinsic.skills.proto import equipment_registry_pb2_grpc
from intrinsic.util.grpc import error_handling


# This is a dict mapping slot names (key in equipment_handles map in
# SkillInstance) to equipment names (passed to GetEquipmentByName).
EquipmentRequirements = Dict[str, str]
# Dict mapping from slot name to equipment handle (verbatim input to
# handles in skill_registry_pb2_grpc.GetInstanceRequest.
EquipmentHandles = Dict[str, equipment_pb2.EquipmentHandle]


class EquipmentRegistry:
  """Wrapper for the equipment registry gRPC service."""

  def __init__(self, stub: equipment_registry_pb2_grpc.EquipmentRegistryStub):
    """Constructs a new EquipmentRegistry object.

    Args:
      stub: The gRPC stub to be used for communication with the equipment
        registry service.
    """
    self._stub: equipment_registry_pb2_grpc.EquipmentRegistryStub = stub

  @classmethod
  def connect(cls, grpc_channel: grpc.Channel) -> EquipmentRegistry:
    """Connect to a running equipment registry.

    Args:
      grpc_channel: Channel to the skill registry gRPC service.

    Returns:
      A newly created instance of the Skill registry wrapper class.

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    stub = equipment_registry_pb2_grpc.EquipmentRegistryStub(grpc_channel)
    return cls(stub)

  @error_handling.retry_on_grpc_unavailable
  def get_equipment_by_name(self, name: str) -> equipment_pb2.EquipmentHandle:
    """Retrieves an equipment handle for the named equipment.

    Args:
      name: name of the equipment to retrieve from registry.

    Returns:
      An equipment handle for the named equipment.

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    request = equipment_registry_pb2.EquipmentByNameRequest()
    request.equipment_name = name
    try:
      response = self._stub.GetEquipmentByName(request)
      return response.handle
    except grpc.RpcError as e:
      # If a NotFound error was returned by the server, then return an empty
      # EquipmentHandle to maintain the current semantics.
      if cast(grpc.Call, e).code() == grpc.StatusCode.NOT_FOUND:
        return equipment_pb2.EquipmentHandle()
      else:
        raise

  @error_handling.retry_on_grpc_unavailable
  def list_equipment(self) -> List[equipment_pb2.EquipmentHandle]:
    """Get all equipment from registry.

    Returns:
      List of equipment handles

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    request = equipment_registry_pb2.ListEquipmentRequest()
    response = self._stub.ListEquipment(request)
    return response.handles

  @error_handling.retry_on_grpc_unavailable
  def find_equipments(
      self, selectors: List[equipment_pb2.EquipmentSelector]
  ) -> List[List[equipment_pb2.EquipmentHandle]]:
    """Get equipments compatible to one or more selectors from the registry.

    Args:
      selectors: The equipment selectors with which returned handles must be
        compatible.

    Returns:
      Returns a list of the same length as the 'selectors' input list. Each
      entry in the return value is a list of equipment handles that corresponds
      to the selector with the same index in the input list. Each list of
      handles may be empty if no compatible handles are found.

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    if not selectors:
      return []
    request = equipment_registry_pb2.EquipmentBySelectorBatchRequest(
        requests=[
            equipment_registry_pb2.EquipmentBySelectorRequest(selector=sel)
            for sel in selectors
        ]
    )
    response = self._stub.BatchGetEquipmentBySelector(request)
    return [resp.handles for resp in response.responses]

  @error_handling.retry_on_grpc_unavailable
  def get_equipment(self, equipment: EquipmentRequirements) -> EquipmentHandles:
    """Get a set of equipment from registry.

    Args:
      equipment: a requirements map from equipment slot to equipment name.

    Returns:
      Map from slot name to equipment handle for equipment.

    Raises:
      grpc.RpcError: When gRPC call to equipment registry fails.
    """
    equipment_handles = {}
    for slot, name in equipment.items():
      try:
        equipment_handles[slot] = self.get_equipment_by_name(name)
      except grpc.RpcError as e:
        # If a NotFound error was returned by the server, then return an empty
        # EquipmentHandle to maintain the current semantics.
        if cast(grpc.Call, e).code() == grpc.StatusCode.NOT_FOUND:
          equipment_handles[slot] = equipment_pb2.EquipmentHandle()
        else:
          raise
    return equipment_handles
