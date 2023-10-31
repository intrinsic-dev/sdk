# Copyright 2023 Intrinsic Innovation LLC

"""PreviewContext for calls to Skill.preview."""

import abc

from intrinsic.logging.proto import context_pb2
from intrinsic.motion_planning import motion_planner_client
from intrinsic.skills.python import skill_canceller
from intrinsic.world.proto import object_world_updates_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources


class PreviewContext(abc.ABC):
  """Provides extra metadata and functionality for a Skill.preview call.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use.

  Attributes:
    canceller: Supports cooperative cancellation of the skill.
    logging_context: The logging context of the execution.
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world. NOTE: This
      client should be treated as read-only. Any effect the skill is expected to
      have on the physical world should be recorded using `record_world_update`.
      (See further explanation in Skill.preview.)
  """

  @property
  @abc.abstractmethod
  def canceller(self) -> skill_canceller.SkillCanceller:
    pass

  @property
  @abc.abstractmethod
  def logging_context(self) -> context_pb2.Context:
    pass

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

  @abc.abstractmethod
  def record_world_update(
      self,
      update: object_world_updates_pb2.ObjectWorldUpdate,
      elapsed: float,
      duration: float,
  ) -> None:
    """Records a world update that the skill is expected to make.

    Args:
      update: The expected update.
      elapsed: The expected amount of (non-negative) elapsed time since the
        start of the previous update (NOT since the start of skill execution),
        in seconds.
      duration: The expected duration of the update, in seconds.
    """
