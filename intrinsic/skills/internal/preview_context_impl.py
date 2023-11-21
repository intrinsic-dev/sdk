# Copyright 2023 Intrinsic Innovation LLC

"""PreviewContext implementation provided by the skill service."""

import datetime

from google.protobuf import duration_pb2
from google.protobuf import timestamp_pb2
from intrinsic.motion_planning import motion_planner_client
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.proto import prediction_pb2
from intrinsic.skills.python import preview_context
from intrinsic.skills.python import skill_canceller
from intrinsic.skills.python import skill_logging_context
from intrinsic.world.proto import object_world_updates_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources


class PreviewContextImpl(preview_context.PreviewContext):
  """PreviewContext implementation provided by the skill service.

  Attributes:
    canceller: Supports cooperative cancellation of the skill.
    logging_context: The logging context of the execution.
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
      NOTE: Any updates to this world will be ignored by the skill service. Use
        `record_world_update` to record any effects that executing the skill is
        expected to have on the world.
    world_updates: A list of updates that have been recorded by
      `record_world_update`.
      NOTE: NOT part of the `PreviewContext` interface.
  """

  @property
  def canceller(self) -> skill_canceller.SkillCanceller:
    return self._canceller

  @property
  def logging_context(self) -> skill_logging_context.SkillLoggingContext:
    return self._logging_context

  @property
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    return self._motion_planner

  @property
  def object_world(self) -> object_world_client.ObjectWorldClient:
    return self._object_world

  @property
  def world_updates(self) -> list[prediction_pb2.TimedWorldUpdate]:
    return self._world_updates

  def __init__(
      self,
      canceller: skill_canceller.SkillCanceller,
      logging_context: skill_logging_context.SkillLoggingContext,
      motion_planner: motion_planner_client.MotionPlannerClient,
      object_world: object_world_client.ObjectWorldClient,
      resource_handles: dict[str, resource_handle_pb2.ResourceHandle],
  ):
    self._canceller = canceller
    self._logging_context = logging_context
    self._motion_planner = motion_planner
    self._object_world = object_world
    self._resource_handles = resource_handles

    self._world_updates: list[prediction_pb2.TimedWorldUpdate] = []

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

  def record_world_update(
      self,
      update: object_world_updates_pb2.ObjectWorldUpdate,
      elapsed: float,
      duration: float,
  ) -> None:
    if elapsed < 0:
      raise ValueError("`elapsed` must be non-negative.")
    if duration < 0:
      raise ValueError("`duration` must be non-negative.")

    base_time = (
        self._world_updates[-1].start_time
        if self._world_updates
        else timestamp_pb2.Timestamp()
    )

    start_time = timestamp_pb2.Timestamp()
    start_time.FromDatetime(
        base_time.ToDatetime() + datetime.timedelta(seconds=elapsed)
    )
    time_until_update = duration_pb2.Duration()
    time_until_update.FromTimedelta(datetime.timedelta(seconds=duration))

    timed_update = prediction_pb2.TimedWorldUpdate(
        start_time=start_time,
        time_until_update=time_until_update,
        world_updates=object_world_updates_pb2.ObjectWorldUpdates(
            updates=[update]
        ),
    )
    self._world_updates.append(timed_update)
