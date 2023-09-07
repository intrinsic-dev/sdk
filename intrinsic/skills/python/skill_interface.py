# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Skills Python APIs and definitions."""
import abc
import dataclasses
import threading
from typing import Any, Callable, Generic, List, Mapping, Optional, TypeVar

from google.protobuf import any_pb2
from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.motion_planning import motion_planner_client
from intrinsic.motion_planning.proto import motion_planner_service_pb2_grpc
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import footprint_pb2
from intrinsic.skills.proto import skill_service_pb2
from intrinsic.world.proto import object_world_service_pb2_grpc
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources

TParamsType = TypeVar('TParamsType', bound=message.Message)

DEFAULT_READY_FOR_CANCELLATION_TIMEOUT = 30.0


class CallbackAlreadyRegisteredError(RuntimeError):
  """A callback was registered after a callback had already been registered."""


class SkillAlreadyCancelledError(RuntimeError):
  """A cancelled skill was cancelled again."""


class SkillReadyForCancellationError(RuntimeError):
  """An invalid action occurred on a skill that is ready for cancellation."""


class SkillCancelledError(RuntimeError):
  """A skill was aborted due to a cancellation request."""


class ProjectionContext:
  """Contains additional metadata and functionality for a skill projection.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use. Python sub-skills are not currently
  used; however, it would also allow skills to invoke subskills (see full
  functionality in skill_interface.h).
  """

  def __init__(
      self,
      world_id: Optional[str] = None,
      object_world_service: Optional[
          object_world_service_pb2_grpc.ObjectWorldServiceStub
      ] = None,
      motion_planner_service: Optional[
          motion_planner_service_pb2_grpc.MotionPlannerServiceStub
      ] = None,
      equipment_handles: Optional[
          Mapping[str, equipment_pb2.EquipmentHandle]
      ] = None,
  ):
    """Initializes this object.

    Args:
      world_id: Id of the current world.
      object_world_service: Stub to object world service.
      motion_planner_service: Stub to motion planner service.
      equipment_handles: Handles for the required equipment for this skill
    """
    self._world_id = world_id
    self._object_world_service = object_world_service
    self._motion_planner_service = motion_planner_service
    self._equipment_handles = equipment_handles

  def get_object_world(self) -> object_world_client.ObjectWorldClient:
    return object_world_client.ObjectWorldClient(
        self._world_id, self._object_world_service
    )

  def get_world_id(self) -> Optional[str]:
    """Returns the world id used to create the ProjectionContext."""
    return self._world_id

  def get_kinematic_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.KinematicObject:
    """Returns the kinematic object that corresponds to this equipment.

    The kinematic object is sourced from the same world that's available in
    the get_object_world call.

    Args:
      equipment_name: The name of the expected equipment.

    Returns:
      A kinematic object from the world associated with this context.
    """
    return self.get_object_world().get_kinematic_object(
        self._equipment_handles[equipment_name]
    )

  def get_object_for_equipment(
      self, equipment_name: str
  ) -> object_world_resources.WorldObject:
    """Returns the world object that corresponds to this equipment.

    The world object is sourced from the same world that's available in
    the get_object_world call.

    Args:
      equipment_name: The name of the expected equipment.

    Returns:
      A world object from the world associated with this context.
    """
    return self.get_object_world().get_object(
        self._equipment_handles[equipment_name]
    )

  def get_frame_for_equipment(
      self, equipment_name: str, frame_name: object_world_ids.FrameName
  ) -> object_world_resources.Frame:
    """Returns the frame by name for an object corresponding to some equipment.

    The frame is sourced from the same world that's available in
    the get_object_world call.

    Args:
      equipment_name: The name of the expected equipment.
      frame_name: The name of the frame within the equipment's object.

    Returns:
      A frame from the world associated with this context.
    """
    return self.get_object_world().get_frame(
        frame_name, self._equipment_handles[equipment_name]
    )

  def get_motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    return motion_planner_client.MotionPlannerClient(
        self._world_id, self._motion_planner_service
    )


@dataclasses.dataclass(frozen=True)
class ExecuteRequest(Generic[TParamsType]):
  """A request for executing a skill.

  (This class temporarily proxies an ExecuteRequest proto: b/298436484.)

  TODO: Make this a dataclass with needed fields.
  TODO: Refactor existing skills to access dataclass fields.
  TODO: Stop proxying the proto.

  Attributes:
    params: The skill parameters proto. For static typing, ExecuteRequest can be
      parameterized with the required type of this message.
  """

  params: TParamsType
  _proto: skill_service_pb2.ExecuteRequest = dataclasses.field(
      default_factory=skill_service_pb2.ExecuteRequest
  )

  def __getattr__(self, name: str) -> Any:
    if name == 'parameters':
      raise AttributeError("Use 'params' instead.")
    return getattr(self._proto, name)


class ExecutionContext:
  """Contains additional metadata and functionality for a skill execution.

  It is provided by the skill service to a skill and allows access to the world
  and other services that a skill may use. Python sub-skills are not currently
  used; however, it would also allow skills to invoke subskills (see full
  functionality in skill_interface.h).

  ExecutionContext helps support cooperative skill cancellation. When a
  cancellation request is received, the skill should stop as soon as possible
  and leave resources in a safe and recoverable state.

  If a skill supports cancellation, it must notify its ExecutionContext via
  `notify_ready_for_cancellation` once it is ready to be cancelled.

  A skill can implement cancellation in one of two ways:
  1) Poll `cancelled`, and safely cancel operation if and when it becomes true.
  2) Register a cancellation callback via `register_cancellation_callback`. This
     callback will be invoked when the skill receives a cancellation request.

  Attributes:
    cancelled: True if the skill framework has received a cancellation request.
    equipment_handles: A map of equipment names to handles.
  """

  def __init__(
      self,
      equipment_handles: Mapping[str, equipment_pb2.EquipmentHandle],
      world_id: str,
      object_world_service: object_world_service_pb2_grpc.ObjectWorldServiceStub,
      motion_planner_service: motion_planner_service_pb2_grpc.MotionPlannerServiceStub,
      ready_for_cancellation_timeout: float = 30.0,
  ):
    """Initializes this object.

    Args:
      world_id: Id of the current world.
      equipment_handles: A map of equipment names to handles.
      object_world_service: Stub to object world service.
      motion_planner_service: Stub to motion planner service.
      ready_for_cancellation_timeout: When cancelling, the maximum number of
        seconds to wait for the skill to be ready to cancel before timing out.
    """
    self._equipment_handles = equipment_handles
    self._world_id = world_id
    self._object_world_service = object_world_service
    self._motion_planner_service = motion_planner_service
    self._ready_for_cancellation_timeout = ready_for_cancellation_timeout

    self._cancel_lock = threading.Lock()
    self._ready_for_cancellation = threading.Event()
    self._cancelled = threading.Event()
    self._cancellation_cb = None

  @property
  def cancelled(self) -> bool:
    return self._cancelled.is_set()

  @property
  def equipment_handles(self) -> Mapping[str, equipment_pb2.EquipmentHandle]:
    return self._equipment_handles

  def world_id(self) -> Optional[str]:
    return self._world_id

  def get_object_world(self) -> object_world_client.ObjectWorldClient:
    return object_world_client.ObjectWorldClient(
        self._world_id, self._object_world_service
    )

  def get_motion_planner(self) -> motion_planner_client.MotionPlannerClient:
    return motion_planner_client.MotionPlannerClient(
        self._world_id, self._motion_planner_service
    )

  def notify_ready_for_cancellation(self) -> None:
    """Notifies the context that the skill is ready to be cancelled."""
    self._ready_for_cancellation.set()

  def register_cancellation_callback(self, cb: Callable[[], None]):
    """Sets a callback that will be invoked when a cancellation is requested.

    If a callback will be used, it must be registered before calling
    `notify_ready_for_cancellation`. Only one callback may be registered, and
    the callback will be called at most once.

    Args:
      cb: The cancellation callback. Will be called at most once.

    Raises:
      Exception: Any exception raised when calling the cancellation callback.
      CallbackAlreadyRegisteredError: If a callback was already registered.
      SkillReadyForCancellationError: If the skill is already ready for
        cancellation.
    """
    with self._cancel_lock:
      if self._ready_for_cancellation.is_set():
        raise SkillReadyForCancellationError(
            'A cancellation callback cannot be registered after the skill is'
            ' ready for cancellation.'
        )
      if self._cancellation_cb is not None:
        raise CallbackAlreadyRegisteredError(
            'A cancellation callback was already registered.'
        )

      self._cancellation_cb = cb

  def _cancel(self) -> None:
    """Sets the cancelled flag and calls the cancellation callback (if set).

    May be called by the owner of this object (e.g., SkillExecutorServicer).

    Raises:
      Exception: Any exception raised when calling the cancellation callback.
      SkillAlreadyCancelledError: If the skill was already cancelled.
      TimeoutError: If we timeout while waiting for the skill to be ready to
        cancel.
    """
    if not self._ready_for_cancellation.wait(
        self._ready_for_cancellation_timeout
    ):
      raise TimeoutError(
          'Timed out waiting for the skill to be ready for cancellation.'
      )

    with self._cancel_lock:
      if self.cancelled:
        raise SkillAlreadyCancelledError('The skill was already cancelled.')
      self._cancelled.set()

      cb = self._cancellation_cb

    if cb is not None:
      cb()


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

    If the skill is cancelled, its ExecutionContext waits for at most this
    timeout duration for the skill to have called
    `notify_ready_for_cancellation` before raising a timeout error.
    """
    return 30.0


class SkillExecuteInterface(metaclass=abc.ABCMeta):
  """Interface for skill executors.

  Implementations of the SkillExecuteInterface define how a skill behaves when
  it is executed.
  """

  @abc.abstractmethod
  def execute(
      self, request: ExecuteRequest, context: ExecutionContext
  ) -> skill_service_pb2.ExecuteResult:
    """Executes the skill.

    Skill authors should override this method with their implementation.

    Implementations that support cancellation should raise SkillCancelledError
    if the skill is aborted due to a cancellation request.

    Args:
      request: The execute request.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      The execute result proto.

    Raises:
      SkillCancelledError: If the skill is aborted due to a cancellation
        request.
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

  class ProjectParams:
    """Parameters passed to the skill's project/predict methods.

    This class filters the parameters available to the skill implementation by
    removing those that are only used to manage the RPC call (e.g., logging).
    """

    def __init__(self, skill_parameters: any_pb2.Any, internal_data: bytes):
      self._skill_parameters = skill_parameters
      self._internal_data = internal_data

    def skill_parameters(self) -> any_pb2.Any:
      """Provides the skill-specific parameters passed to the skill."""
      return self._skill_parameters

    def internal_data(self) -> bytes:
      """Provides any internal data generated during previous calls."""
      return self._internal_data

  def get_footprint(
      self, params: ProjectParams, context: ProjectionContext
  ) -> skill_service_pb2.ProjectResult:
    """Returns the required resources for running this skill.

    Skill authors should override this method with their implementation.

    Args:
      params: The parameters expected to be passed to the skill.
      context: Always provided when the skill is invoked within a skill service
        server. It contains the current world state, which can be used to
        analyze the expected behavior of the skill.

    Returns:
      The project result proto containing the footprint.
    """
    del params  # Unused in this default implementation.
    del context  # Unused in this default implementation.
    return skill_service_pb2.ProjectResult(
        footprint=footprint_pb2.Footprint(lock_the_universe=True)
    )

  def predict(
      self,
      params: ProjectParams,
      context: ProjectionContext,
  ) -> skill_service_pb2.PredictResult:
    """Predicts a distribution of possible outcomes when running the skill.

    Skill authors should override this method with their implementation.

    Args:
      params: The parameters expected to be passed to the skill.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      A list of prediction protos containing the possible outcomes.
    """
    del params  # Unused in this default implementation.
    del context  # Unused in this default implementation.
    raise NotImplementedError('No user-defined call for Predict()')


class Skill(
    SkillSignatureInterface, SkillExecuteInterface, SkillProjectInterface
):
  """Interface for skills.

  Notes on skill implementations:

  If a skill implementation supports cancellation, it should:
  1) Stop as soon as possible and leave resources in a safe and recoverable
     state when a cancellation request is received (via its ExecutionContext).
     Cancelled skill executions should end by raising SkillCancelledError.
  2) Override `supports_cancellation` to return True.
  """
