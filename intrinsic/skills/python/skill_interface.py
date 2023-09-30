# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Skills Python APIs and definitions."""
import abc
import dataclasses
from typing import Generic, List, Mapping, Optional, TypeVar

from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.logging.proto import context_pb2
from intrinsic.motion_planning import motion_planner_client
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import footprint_pb2
from intrinsic.skills.proto import skill_service_pb2
from intrinsic.skills.python import skill_canceller
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources

# Imported for convenience of skill implementations.
SkillCancelledError = skill_canceller.SkillCancelledError


class InvalidSkillParametersError(ValueError):
  """Invalid arguments were passed to the skill parameters."""


TParamsType = TypeVar('TParamsType', bound=message.Message)


@dataclasses.dataclass(frozen=True)
class GetFootprintRequest(Generic[TParamsType]):
  """A request for a call to Skill.get_footprint.

  Attributes:
    params: The skill parameters proto. For static typing, GetFootprintRequest
      can be parameterized with the required type of this message.
  """

  params: TParamsType


class GetFootprintContext:
  """Contains additional context for computing a skill footprint.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use.

  Attributes:
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
  """

  @property
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    motion_planner = self._motion_planner
    if motion_planner is None:
      raise ValueError(
          'The GetFootprintContext does not have a motion planner client.'
      )

    return motion_planner

  @property
  def object_world(self) -> object_world_client.ObjectWorldClient:
    object_world = self._object_world
    if object_world is None:
      raise ValueError(
          'The GetFootprintContext does not have an object world client.'
      )

    return object_world

  def __init__(
      self,
      equipment_handles: dict[str, equipment_pb2.EquipmentHandle],
      motion_planner: motion_planner_client.MotionPlannerClient,
      object_world: object_world_client.ObjectWorldClient,
  ):
    """Initializes this object.

    Args:
      equipment_handles: Handles for the required equipment for this skill.
      motion_planner: The motion planner client to provide.
      object_world: The object world client to provide.
    """
    self._equipment_handles = equipment_handles
    self._motion_planner = motion_planner
    self._object_world = object_world

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
    return self.object_world.get_kinematic_object(
        self._equipment_handles[equipment_name]
    )

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
    return self.object_world.get_object(self._equipment_handles[equipment_name])

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
    return self.object_world.get_frame(
        frame_name, self._equipment_handles[equipment_name]
    )


@dataclasses.dataclass(frozen=True)
class ExecuteRequest(Generic[TParamsType]):
  """A request for a call to Skill.execute.

  Attributes:
    params: The skill parameters proto. For static typing, ExecuteRequest can be
      parameterized with the required type of this message.
  """

  params: TParamsType


class ExecuteContext:
  """Contains additional metadata and functionality for a skill execution.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use. Python sub-skills are not currently
  used; however, it would also allow skills to invoke subskills (see full
  functionality in skill_interface.h).

  ExecuteContext helps support cooperative skill cancellation via `canceller`.
  When a cancellation request is received, the skill should:
  1) stop as soon as possible and leave resources in a safe and recoverable
     state;
  2) raise SkillCancelledError.

  Attributes:
    canceller: Supports cooperative cancellation of the skill.
    equipment_handles: A map of equipment names to handles.
    logging_context: The logging context of the execution.
    motion_planner: A client for the motion planning service.
    object_world: A client for interacting with the object world.
  """

  @property
  def canceller(self) -> skill_canceller.SkillCanceller:
    return self._canceller

  @property
  def equipment_handles(self) -> Mapping[str, equipment_pb2.EquipmentHandle]:
    return self._equipment_handles

  @property
  def logging_context(self) -> context_pb2.Context:
    return self._logging_context

  @property
  def motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    return self._motion_planner

  @property
  def object_world(self) -> object_world_client.ObjectWorldClient:
    return self._object_world

  def __init__(
      self,
      canceller: skill_canceller.SkillCanceller,
      equipment_handles: dict[str, equipment_pb2.EquipmentHandle],
      logging_context: context_pb2.Context,
      motion_planner: motion_planner_client.MotionPlannerClient,
      object_world: object_world_client.ObjectWorldClient,
  ):
    """Initializes this object.

    Args:
      canceller: Supports cooperative cancellation of the skill.
      equipment_handles: A map of equipment names to handles.
      logging_context: The logging context of the execution.
      motion_planner: The motion planner client to provide.
      object_world: The object world client to provide.
    """
    self._canceller = canceller
    self._equipment_handles = equipment_handles
    self._logging_context = logging_context
    self._motion_planner = motion_planner
    self._object_world = object_world


class SkillSignatureInterface(metaclass=abc.ABCMeta):
  """Signature interface for skills.

  The signature interface presents metadata about skill, which is associated the
  skill class implementation.
  """

  @classmethod
  def default_parameters(cls) -> Optional[message.Message]:
    """Returns the default parameters for the Skill.

    Returns None if there are no defaults. Fields with default values must be
    marked as `optional` in the proto schema.
    """
    return None

  @classmethod
  def required_equipment(cls) -> Mapping[str, equipment_pb2.EquipmentSelector]:
    """Returns the signature of the skill's required equipment.

    The return map includes the name of the equipment as the key and its
    selector type as value.
    """
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def name(cls) -> str:
    """Returns the name of the skill."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def package(cls) -> str:
    """Returns the package of the skill."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def get_parameter_descriptor(cls) -> descriptor.Descriptor:
    """Returns the descriptor for the parameter that this skill expects."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def get_return_value_descriptor(cls) -> Optional[descriptor.Descriptor]:
    """Returns the descriptor for the value that this skill may output."""

    # By default, assume the skill has no value to return.
    return None

  @classmethod
  def supports_cancellation(cls) -> bool:
    """Returns True if the skill supports cancellation."""
    return False

  @classmethod
  def get_ready_for_cancellation_timeout(cls) -> float:
    """Returns the skill's ready for cancellation timeout, in seconds.

    If the skill is cancelled, its ExecuteContext's SkillCanceller waits for
    at most this timeout duration for the skill to have called `ready` before
    raising a timeout error.
    """
    return 30.0


class SkillExecuteInterface(metaclass=abc.ABCMeta):
  """Interface for skill executors.

  Implementations of the SkillExecuteInterface define how a skill behaves when
  it is executed.
  """

  @abc.abstractmethod
  def execute(
      self, request: ExecuteRequest, context: ExecuteContext
  ) -> message.Message | None:
    """Executes the skill.

    Skill authors should override this method with their implementation.

    If the skill raises an error, it will cause the Process to fail immediately,
    unless the skill is part of a `FallbackNode` in the Process tree. Currently,
    there is no way to distinguish between potentially recoverable failures that
    should lead to fallback handling via that node (e.g., failure to achieve the
    skill's objective) and other failures that should abort the entire process
    (e.g., failure to connect to a gRPC service).

    Args:
      request: The execute request.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      The skill's result message, or None if it does not return a result.

    Raises:
      SkillCancelledError: If the skill is aborted due to a cancellation
        request.
      InvalidSkillParametersError: If the arguments provided to skill parameters
        are invalid.
    """
    raise NotImplementedError('Method not implemented!')


class SkillProjectInterface(metaclass=abc.ABCMeta):
  """Interface for skill projectors.

  Implementations of the SkillProjectInterface define how predictive information
  about how a skill might behave during execution. The methods of this interface
  should be invokable prior to execution to allow a skill to, eg.:
  * precompute information that can be passed to the skill at execution time
  * predict its behavior given the current known information about the world,
    and any parameters that the skill depends on
  * provide an understanding of what the footprint of the skill on the workcell
    will be when it is executed
  """

  def get_footprint(
      self, request: GetFootprintRequest, context: GetFootprintContext
  ) -> footprint_pb2.Footprint:
    """Returns the required resources for running this skill.

    Skill authors should override this method with their implementation.

    Args:
      request: The get footprint request.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      The skill's footprint.
    """
    del request  # Unused in this default implementation.
    del context  # Unused in this default implementation.
    return footprint_pb2.Footprint(lock_the_universe=True)


class Skill(
    SkillSignatureInterface, SkillExecuteInterface, SkillProjectInterface
):
  """Interface for skills.

  Notes on skill implementations:

  If a skill implementation supports cancellation, it should:
  1) Stop as soon as possible and leave resources in a safe and recoverable
     state when a cancellation request is received (via its ExecuteContext).
     Cancelled skill executions should end by raising SkillCancelledError.
  2) Override `supports_cancellation` to return True.
  """
