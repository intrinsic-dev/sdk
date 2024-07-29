# Copyright 2023 Intrinsic Innovation LLC

"""BasicComputeContextImpl implementation provided by the code execution service."""

from intrinsic.skills.python import basic_compute_context
from intrinsic.world.python import object_world_client


class BasicComputeContextImpl(basic_compute_context.BasicComputeContext):
  """BasicComputeContext implementation provided by the code execution service.

  Attributes:
    object_world: A client for interacting with the object world.
  """

  @property
  def object_world(self) -> object_world_client.ObjectWorldClient:
    return self._object_world

  def __init__(
      self,
      object_world: object_world_client.ObjectWorldClient,
  ):
    self._object_world = object_world
