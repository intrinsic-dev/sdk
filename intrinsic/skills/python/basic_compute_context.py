# Copyright 2023 Intrinsic Innovation LLC

"""Defines a context for basic compute methods."""

import abc

from intrinsic.world.python import object_world_client


class BasicComputeContext(abc.ABC):
  """Provides extra metadata and functionality to a basic compute method.

  It is provided by the code execution service to the compute function of a
  Python code execution task in a task node and allows, e.g., access to the
  world.

  Attributes:
    object_world: A client for interacting with the object world.
  """

  @property
  @abc.abstractmethod
  def object_world(self) -> object_world_client.ObjectWorldClient:
    pass
