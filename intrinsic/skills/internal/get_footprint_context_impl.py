# Copyright 2023 Intrinsic Innovation LLC

"""GetFootprintContext implementation provided by the skill service."""

from intrinsic.motion_planning import motion_planner_client
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.python import get_footprint_context
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources


class GetFootprintContextImpl(get_footprint_context.GetFootprintContext):
  """GetFootprintContext implementation provided by the skill service.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use.

  Attributes:
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
  """

  @property
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    return self._motion_planner

  @property
  def object_world(self) -> object_world_client.ObjectWorldClient:
    return self._object_world

  def __init__(
      self,
      motion_planner: motion_planner_client.MotionPlannerClient,
      object_world: object_world_client.ObjectWorldClient,
      resource_handles: dict[str, equipment_pb2.ResourceHandle],
  ):
    self._motion_planner = motion_planner
    self._object_world = object_world
    self._resource_handles = resource_handles

  def get_frame_for_equipment(
      self, equipment_name: str, frame_name: object_world_ids.FrameName
  ) -> object_world_resources.Frame:
    return self.object_world.get_frame(
        frame_name, self._resource_handles[equipment_name]
    )

  def get_kinematic_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.KinematicObject:
    return self.object_world.get_kinematic_object(
        self._resource_handles[equipment_name]
    )

  def get_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.WorldObject:
    return self.object_world.get_object(self._resource_handles[equipment_name])
