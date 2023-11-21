# Copyright 2023 Intrinsic Innovation LLC

"""ExecuteContext for calls to Skill.execute."""

import abc
from typing import Mapping

from intrinsic.motion_planning import motion_planner_client
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.python import skill_canceller
from intrinsic.skills.python import skill_logging_context
from intrinsic.world.python import object_world_client


class ExecuteContext(abc.ABC):
  """Provides extra metadata and functionality for a Skill.execute call.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use.

  ExecuteContext helps support cooperative skill cancellation via `canceller`.
  When a cancellation request is received, the skill should:
  1) stop as soon as possible and leave resources in a safe and recoverable
     state;
  2) raise SkillCancelledError.

  Attributes:
    canceller: Supports cooperative cancellation of the skill.
    logging_context: The skill's logging context.
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
    resource_handles: A map of resource names to handles.
  """

  @property
  @abc.abstractmethod
  def canceller(self) -> skill_canceller.SkillCanceller:
    pass

  @property
  @abc.abstractmethod
  def logging_context(self) -> skill_logging_context.SkillLoggingContext:
    pass

  @property
  @abc.abstractmethod
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    pass

  @property
  @abc.abstractmethod
  def object_world(self) -> object_world_client.ObjectWorldClient:
    pass

  @property
  @abc.abstractmethod
  def resource_handles(
      self,
  ) -> Mapping[str, resource_handle_pb2.ResourceHandle]:
    pass
