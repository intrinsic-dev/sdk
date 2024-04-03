# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrapper around the BehaviorTreeRegistry."""

from __future__ import annotations

import uuid

import grpc
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.skills.proto import behavior_tree_registry_pb2
from intrinsic.skills.proto import behavior_tree_registry_pb2_grpc
from intrinsic.skills.proto import skill_registry_config_pb2
from intrinsic.util.grpc import error_handling


class BehaviorTreeRegistry:
  """Wrapper for the proto builder gRPC service."""

  def __init__(
      self, stub: behavior_tree_registry_pb2_grpc.BehaviorTreeRegistryStub
  ):
    """Constructs a new BehaviorTreeRegistry object.

    Args:
      stub: The gRPC stub to be used for communication with the service.
    """
    self._stub: behavior_tree_registry_pb2_grpc.BehaviorTreeRegistryStub = stub

  @classmethod
  def connect(cls, grpc_channel: grpc.Channel) -> BehaviorTreeRegistry:
    """Connect to a running proto builder.

    Args:
      grpc_channel: Channel to the gRPC service.

    Returns:
      A newly created instance of the wrapper class.

    Raises:
      grpc.RpcError: When gRPC call to service fails.
    """
    stub = behavior_tree_registry_pb2_grpc.BehaviorTreeRegistryStub(
        grpc_channel
    )
    return cls(stub)

  @error_handling.retry_on_grpc_unavailable
  def _register_or_update_behavior_tree(
      self, tree_proto: behavior_tree_pb2.BehaviorTree
  ):
    """Register a PBT.

    Args:
      tree_proto: The PBT to register.

    Raises:
      grpc.RpcError: When gRPC call fails.
    """
    reg = skill_registry_config_pb2.BehaviorTreeRegistration()
    reg.behavior_tree.CopyFrom(tree_proto)
    request = behavior_tree_registry_pb2.RegisterOrUpdateBehaviorTreeRequest()
    request.registration.CopyFrom(reg)

    self._stub.RegisterOrUpdateBehaviorTree(request)

  def sideload_behavior_tree(self, tree_proto: behavior_tree_pb2.BehaviorTree):
    """Sideload a PBT.

    This will automatically generate a random version for the PBT's id version,
    so that the sideloaded PBT is registered as a new version in the registry.

    Args:
      tree_proto: The PBT to sideload.

    Raises:
      grpc.RpcError: When gRPC call fails.
    """
    assert tree_proto.description
    skill_id = tree_proto.description.id
    version = str(uuid.uuid4()).replace('-', '_')
    tree_proto.description.id_version = skill_id + '.0.0.1sideload' + version
    self._register_or_update_behavior_tree(tree_proto)
