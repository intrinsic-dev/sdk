# Copyright 2023 Intrinsic Innovation LLC

"""ExecuteContext implementation provided by the skill service."""

from typing import Mapping

from intrinsic.motion_planning import motion_planner_client
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.python import execute_context
from intrinsic.skills.python import skill_canceller
from intrinsic.skills.python import skill_logging_context
from intrinsic.world.python import object_world_client


class ExecuteContextImpl(execute_context.ExecuteContext):
  """ExecuteContext implementation provided by the skill service.

  Attributes:
    canceller: Supports cooperative cancellation of the skill.
    logging_context: The logging context of the execution.
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
    resource_handles: A map of resource names to handles.
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
  def resource_handles(
      self,
  ) -> Mapping[str, resource_handle_pb2.ResourceHandle]:
    return self._resource_handles

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
