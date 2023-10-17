# Copyright 2023 Intrinsic Innovation LLC

"""GetFootprintContext for calls to Skill.get_footprint."""

import abc

from intrinsic.motion_planning import motion_planner_client
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources


class GetFootprintContext(abc.ABC):
  """Provides extra metadata and functionality for a Skill.get_footprint call.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use.

  Attributes:
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
  """

  @property
  @abc.abstractmethod
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    pass

  @property
  @abc.abstractmethod
  def object_world(self) -> object_world_client.ObjectWorldClient:
    pass

  @abc.abstractmethod
  def get_frame_for_equipment(
      self, equipment_name: str, frame_name: object_world_ids.FrameName
  ) -> object_world_resources.Frame:
    """Returns the frame by name for an object corresponding to some equipment.

    The frame is sourced from the same world that's available via
    `object_world`.

    Args:
      equipment_name: The name of the expected equipment.
      frame_name: The name of the frame within the equipment's object.

    Returns:
      A frame from the world associated with this context.
    """

  @abc.abstractmethod
  def get_kinematic_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.KinematicObject:
    """Returns the kinematic object that corresponds to this equipment.

    The kinematic object is sourced from the same world that's available via
    `object_world`.

    Args:
      equipment_name: The name of the expected equipment.

    Returns:
      A kinematic object from the world associated with this context.
    """

  @abc.abstractmethod
  def get_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.WorldObject:
    """Returns the world object that corresponds to this equipment.

    The world object is sourced from the same world that's available via
    `object_world`.

    Args:
      equipment_name: The name of the expected equipment.

    Returns:
      A world object from the world associated with this context.
    """
