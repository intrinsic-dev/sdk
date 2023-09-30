# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Implementations of Skill project, execute, and info servicers."""
from __future__ import annotations

from concurrent import futures
import threading
import traceback
from typing import Dict, NoReturn, Optional

from absl import logging
from google.longrunning import operations_pb2
from google.protobuf import any_pb2
from google.protobuf import descriptor as proto_descriptor
from google.protobuf import empty_pb2
from google.protobuf import message as proto_message
from google.protobuf import message_factory
from google.rpc import status_pb2
import grpc
from intrinsic.assets import id_utils
from intrinsic.motion_planning import motion_planner_client
from intrinsic.motion_planning.proto import motion_planner_service_pb2_grpc
from intrinsic.skills.internal import default_parameters
from intrinsic.skills.internal import error_utils
from intrinsic.skills.internal import runtime_data as rd
from intrinsic.skills.internal import skill_repository as skill_repo
from intrinsic.skills.proto import error_pb2
from intrinsic.skills.proto import footprint_pb2
from intrinsic.skills.proto import prediction_pb2
from intrinsic.skills.proto import skill_service_pb2
from intrinsic.skills.proto import skill_service_pb2_grpc
from intrinsic.skills.proto import skills_pb2
from intrinsic.skills.python import proto_utils
from intrinsic.skills.python import skill_canceller
from intrinsic.skills.python import skill_interface as skl
from intrinsic.world.proto import object_world_service_pb2_grpc
from intrinsic.world.python import object_world_client
from pybind11_abseil import status

# Maximum number of operations to keep in a SkillExecutionOperations instance.
# This value places a hard upper limit on the number of one type of skill that
# can execute simultaneously.
MAX_NUM_OPERATIONS = 100


class _CannotConstructGetFootprintRequestError(Exception):
  """The service cannot construct a GetFootprintRequest for a skill."""


class _CannotConstructPredictRequestError(Exception):
  """The service cannot construct a PredictRequest for a skill."""


class _CannotConstructExecuteRequestError(Exception):
  """The service cannot construct an ExecuteRequest for a skill."""


class SkillProjectorServicer(skill_service_pb2_grpc.ProjectorServicer):
  """Implementation of the skill Projector servicer."""

  def __init__(
      self,
      skill_repository: skill_repo.SkillRepository,
      object_world_service: object_world_service_pb2_grpc.ObjectWorldServiceStub,
      motion_planner_service: motion_planner_service_pb2_grpc.MotionPlannerServiceStub,
  ):
    self._skill_repository = skill_repository
    self._object_world_service = object_world_service
    self._motion_planner_service = motion_planner_service

  def GetFootprint(
      self,
      footprint_request: skill_service_pb2.GetFootprintRequest,
      context: grpc.ServicerContext,
  ) -> skill_service_pb2.GetFootprintResult:
    """Runs Skill get_footprint operation with provided parameters.

    Args:
      footprint_request: GetFootprintRequest with skill instance to run
        get_footprint on.
      context: gRPC servicer context.

    Returns:
      GetFootprintResult containing results of the footprint calculation.

    Raises:
     grpc.RpcError:
      NOT_FOUND: If the skill is not found.
      INVALID_ARGUMENT: If unable to apply the default parameters.
      INTERNAL: If unable to get the skill's footprint.
      INVALID_ARGUMENT: When the required equipment does not match the
          requested.
    """
    skill_name = id_utils.name_from(footprint_request.instance.id_version)
    try:
      skill_project_instance = self._skill_repository.get_skill_project(
          skill_name
      )
    except skill_repo.InvalidSkillAliasError:
      _abort_with_status(
          context=context,
          code=status.StatusCode.NOT_FOUND,
          message=(
              f'Skill not found: {footprint_request.instance.id_version!r}.'
          ),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    # Apply default parameters if available.
    skill_runtime_data = self._skill_repository.get_skill_runtime_data(
        skill_name
    )
    defaults = skill_runtime_data.parameter_data.default_value
    if defaults is not None and footprint_request.HasField('parameters'):
      try:
        default_parameters.apply_defaults_to_parameters(
            skill_runtime_data.parameter_data.descriptor,
            defaults,
            footprint_request.parameters,
        )
      except status.StatusNotOk as e:
        _abort_with_status(
            context=context,
            code=e.status.code(),
            message=str(e),
            skill_error_info=error_pb2.SkillErrorInfo(
                error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
            ),
        )

    try:
      request = _proto_to_get_footprint_request(
          footprint_request, skill_runtime_data
      )
    except _CannotConstructGetFootprintRequestError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.INTERNAL,
          message=(
              'Could not construct get footprint request for skill'
              f' {footprint_request.instance.id_version}: {err}.'
          ),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
          ),
      )

    object_world = object_world_client.ObjectWorldClient(
        footprint_request.world_id, self._object_world_service
    )
    motion_planner = motion_planner_client.MotionPlannerClient(
        footprint_request.world_id, self._motion_planner_service
    )

    footprint_context = skl.GetFootprintContext(
        equipment_handles=dict(footprint_request.instance.equipment_handles),
        motion_planner=motion_planner,
        object_world=object_world,
    )

    try:
      skill_footprint = skill_project_instance.get_footprint(
          request, footprint_context
      )
    except Exception:  # pylint: disable=broad-except
      msg = traceback.format_exc()
      logging.error(
          'Skill returned an error during get_footprint. Exception:\n%s', msg
      )
      _abort_with_status(
          context=context,
          code=status.StatusCode.INTERNAL,
          message=f'Failure during get footprint of skill. Error: {msg}',
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
          ),
      )

    # Add required equipment to the footprint automatically
    required_equipment = skill_runtime_data.resource_data.required_resources
    for name, selector in required_equipment.items():
      if name in footprint_request.instance.equipment_handles:
        handle = footprint_request.instance.equipment_handles[name]
        skill_footprint.equipment_resource.append(
            footprint_pb2.EquipmentResource(
                type=selector.sharing_type, name=handle.name
            )
        )
      else:
        _abort_with_status(
            context=context,
            code=status.StatusCode.INVALID_ARGUMENT,
            message=(
                'Error when specifying equipment resources. Skill requires'
                f' {list(required_equipment)} but got'
                f' {list(footprint_request.instance.equipment_handles)}.'
            ),
            skill_error_info=error_pb2.SkillErrorInfo(
                error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
            ),
        )

    return skill_service_pb2.GetFootprintResult(footprint=skill_footprint)

  def Predict(
      self,
      predict_request: skill_service_pb2.PredictRequest,
      context: grpc.ServicerContext,
  ) -> skill_service_pb2.PredictResult:
    return skill_service_pb2.PredictResult(
        outcomes=[prediction_pb2.Prediction(probability=1.0)],
        internal_data=predict_request.internal_data,
    )


class SkillExecutorServicer(skill_service_pb2_grpc.ExecutorServicer):
  """Servicer implementation for the skill Executor service."""

  def __init__(
      self,
      skill_repository: skill_repo.SkillRepository,
      object_world_service: (
          object_world_service_pb2_grpc.ObjectWorldServiceStub
      ),
      motion_planner_service: (
          motion_planner_service_pb2_grpc.MotionPlannerServiceStub
      ),
  ):
    self._skill_repository = skill_repository
    self._object_world_service = object_world_service
    self._motion_planner_service = motion_planner_service

    self._operations = _SkillExecutionOperations()

  def StartExecute(
      self,
      request: skill_service_pb2.ExecuteRequest,
      context: grpc.ServicerContext,
  ) -> operations_pb2.Operation:
    """Starts executing the skill as a long-running operation.

    Args:
      request: Execute request with skill instance to execute.
      context: gRPC servicer context.

    Returns:
      Operation representing the skill execution operation.

    Raises:
      grpc.RpcError:
        NOT_FOUND: If the skill cannot be found.
        INTERNAL: If the default parameters cannot be applied.
        ALREADY_EXISTS: If a skill execution operation with the specified name
            (i.e., the skill instance name) already exists.
        FAILED_PRECONDITION: If the operation cache is already full of
            unfinished operations.
    """
    operation = self._prepare_execution_operation(request, context)
    try:
      self._operations.add(operation)
    except self._operations.OperationError as err:
      if isinstance(err, self._operations.OperationAlreadyExistsError):
        code = status.StatusCode.ALREADY_EXISTS
      elif isinstance(err, self._operations.OperationCacheFullError):
        code = status.StatusCode.FAILED_PRECONDITION
      else:
        code = status.StatusCode.INTERNAL

      _abort_with_status(
          context,
          code=code,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    operation.start_execution()

    return operation.operation

  def GetOperation(
      self,
      get_request: operations_pb2.GetOperationRequest,
      context: grpc.ServicerContext,
  ) -> operations_pb2.Operation:
    """Gets the current state of a skill execution operation.

    Args:
      get_request: Get request with skill execution operation name.
      context: gRPC servicer context.

    Returns:
      Operation representing the skill execution operation.

    Raises:
      grpc.RpcError:
        NOT_FOUND: If the operation cannot be found.
    """
    try:
      operation = self._operations.get(get_request.name)
    except self._operations.OperationNotFoundError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.NOT_FOUND,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    return operation.operation

  def CancelOperation(
      self,
      cancel_request: operations_pb2.CancelOperationRequest,
      context: grpc.ServicerContext,
  ) -> empty_pb2.Empty:
    """Requests cancellation of a skill execution operation.

    Args:
      cancel_request: Cancel request with skill operation name.
      context: gRPC servicer context.

    Returns:
      Empty.

    Raises:
      grpc.RpcError:
        NOT_FOUND: If the operation cannot be found.
        FAILED_PRECONDITION: If the operation was already cancelled.
        UNIMPLEMENTED: If the skill does not support cancellation.
        INTERNAL: If a skill cancellation callback raises an error.
    """
    try:
      operation = self._operations.get(cancel_request.name)
    except self._operations.OperationNotFoundError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.NOT_FOUND,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    try:
      operation.request_cancellation()
    except skill_canceller.SkillAlreadyCancelledError:
      _abort_with_status(
          context=context,
          code=status.StatusCode.FAILED_PRECONDITION,
          message=(
              'The operation has already been cancelled:'
              f' {cancel_request.name!r}.'
          ),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )
    except NotImplementedError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.UNIMPLEMENTED,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
          ),
      )
    # Catch any additional errors here, since cancelling the skill may entail
    # calling a user-provided cancellation callback.
    except Exception:  # pylint: disable=broad-except
      logging.exception('Skill cancellation raised an error.')
      _abort_with_status(
          context=context,
          code=status.StatusCode.INTERNAL,
          message=(
              'Failure during skill cancellation. Error:'
              f' {traceback.format_exc()}'
          ),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
          ),
      )

    return empty_pb2.Empty()

  def WaitOperation(
      self,
      wait_request: operations_pb2.WaitOperationRequest,
      context: grpc.ServicerContext,
  ) -> operations_pb2.Operation:
    """Waits for a skill execution operation to finish.

    Args:
      wait_request: Wait request with the skill operation name.
      context: gRPC servicer context.

    Returns:
      Operation representing the skill execution operation.

    Raises:
      grpc.RpcError:
        NOT_FOUND: If the operation is not found.
    """
    try:
      operation = self._operations.get(wait_request.name)
    except self._operations.OperationNotFoundError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.NOT_FOUND,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    return operation.wait(
        wait_request.timeout.ToNanoseconds() / 1e9
        if wait_request.HasField('timeout')
        else None
    )

  def ClearOperations(
      self, clear_request: empty_pb2.Empty, context: grpc.ServicerContext
  ) -> empty_pb2.Empty:
    """Clears the internal store of skill execution operations.

    Args:
      clear_request: Empty.
      context: gRPC servicer context.

    Returns:
      Empty.

    Raises:
      grpc.RpcError:
        FAILED_PRECONDITION: If any stored operation is not yet finished.
    """
    try:
      self._operations.clear()
    except self._operations.OperationNotFinishedError as err:
      _abort_with_status(
          context=context,
          code=status.StatusCode.FAILED_PRECONDITION,
          message=str(err),
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    return empty_pb2.Empty()

  def _prepare_execution_operation(
      self,
      request: skill_service_pb2.ExecuteRequest,
      context: grpc.ServicerContext,
  ) -> _SkillExecutionOperation:
    """Prepares a single skill execution operation.

    Args:
      request: Execute request with skill instance to execute.
      context: gRPC servicer context.

    Returns:
      A `_SkillExecutionOperation` for the execution operation.

    Raises:
      grpc.RpcError:
        NOT_FOUND: If the skill cannot be found.
        INTERNAL: If the default parameters cannot be applied.
    """
    skill_name = id_utils.name_from(request.instance.id_version)
    try:
      skill_execute = self._skill_repository.get_skill_execute(skill_name)
    except skill_repo.InvalidSkillAliasError:
      _abort_with_status(
          context=context,
          code=status.StatusCode.NOT_FOUND,
          message=f'Skill not found: {request.instance.id_version!r}.',
          skill_error_info=error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_GRPC
          ),
      )

    # Apply default parameters if available.
    skill_runtime_data = self._skill_repository.get_skill_runtime_data(
        skill_name
    )
    defaults = skill_runtime_data.parameter_data.default_value
    if defaults is not None and request.HasField('parameters'):
      try:
        default_parameters.apply_defaults_to_parameters(
            skill_runtime_data.parameter_data.descriptor,
            defaults,
            request.parameters,
        )
      except status.StatusNotOk as e:
        _abort_with_status(
            context=context,
            code=status.StatusCode.INTERNAL,
            message=(
                'Failure while applying default values to parameters.'
                f' Error: {e}'
            ),
            skill_error_info=error_pb2.SkillErrorInfo(
                error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
            ),
        )

    canceller = skill_canceller.SkillCancellationManager(
        ready_timeout=(
            skill_runtime_data.execution_options.cancellation_ready_timeout.total_seconds()
        )
    )
    motion_planner = motion_planner_client.MotionPlannerClient(
        request.world_id, self._motion_planner_service
    )
    object_world = object_world_client.ObjectWorldClient(
        request.world_id, self._object_world_service
    )

    execute_context = skl.ExecuteContext(
        canceller=canceller,
        equipment_handles=dict(request.instance.equipment_handles),
        logging_context=request.context,
        motion_planner=motion_planner,
        object_world=object_world,
    )

    return _SkillExecutionOperation(
        canceller=canceller,
        context=execute_context,
        operation=operations_pb2.Operation(
            name=request.instance.instance_name, done=False
        ),
        request=request,
        skill_execute=skill_execute,
        skill_runtime_data=skill_runtime_data,
    )


class SkillInformationServicer(skill_service_pb2_grpc.SkillInformationServicer):
  """Implementation of the skill Information service."""

  def __init__(self, skill: skills_pb2.Skill):
    self._skill = skill

  def GetSkillInfo(
      self, request: empty_pb2.Empty, context: grpc.ServicerContext
  ) -> skill_service_pb2.SkillInformationResult:
    """Runs Skill information retrieval operation.

    Args:
      request: Request (currently empty).
      context: grpc server context.

    Returns:
      SkillInformationResult containing skill information.
    """
    result = skill_service_pb2.SkillInformationResult()
    result.skill.CopyFrom(self._skill)
    return result


class _SkillExecutionOperations:
  """A collection of skill execution operations."""

  class OperationError(Exception):
    """Base SkillExecutionOperations error."""

  class OperationAlreadyExistsError(OperationError, ValueError):
    """An operation already exists in the collection."""

  class OperationNotFinishedError(OperationError, RuntimeError):
    """A disallowed action was performed on an unfinished operation."""

  class OperationNotFoundError(OperationError, ValueError):
    """A requested operation was not found."""

  class OperationCacheFullError(OperationError, RuntimeError):
    """The skill operation cache is full of unfinished operations."""

  def __init__(self):
    self._lock = threading.Lock()
    self._operations: Dict[str, _SkillExecutionOperation] = {}

  def add(self, operation: _SkillExecutionOperation) -> None:
    """Adds an operation to the collection.

    Args:
      operation: The operation to add.

    Raises:
      OperationAlreadyExistsError: If an operation with the same name already
        exists in the collection.
      OperationCacheFullError: If the cache is already full of unfinished
        operations.
    """
    with self._lock:
      # First remove the oldest finished operation if we've reached our limit of
      # tracked operations.
      while len(self._operations) >= MAX_NUM_OPERATIONS:
        old_operation_name = None
        for name, old_operation in self._operations.items():
          if old_operation.finished:
            assert name is not None, 'Operation name was unexpectedly None.'
            old_operation_name = name
            break

        if old_operation_name is None:
          raise self.OperationCacheFullError(
              f'Cannot add operation {operation.name!r}, since there are'
              f' already {len(self._operations)} unfinished operations.'
          )

        del self._operations[old_operation_name]

      if operation.name in self._operations:
        raise self.OperationAlreadyExistsError(
            f'An operation already exists with name {operation.name!r}.'
        )

      self._operations[operation.name] = operation

  def get(self, name: str) -> _SkillExecutionOperation:
    """Gets an operation by name.

    Args:
      name: The operation name.

    Returns:
      The operation.

    Raises:
      OperationNotFoundError: If no operation with the specified name exists.
    """
    with self._lock:
      try:
        return self._operations[name]
      except KeyError as err:
        raise self.OperationNotFoundError(
            f'No operation found with name {name!r}.'
        ) from err

  def clear(self) -> None:
    """Clears all operations in the collection.

    NOTE: The operations must all be finished before clearing them. If any
    operation is not yet finished, no operations will be cleared, and an error
    will be raised.

    Raises:
      OperationNotFinishedError: If any operation is not yet finished.
    """
    with self._lock:
      unfinished_operation_names = []
      for operation in self._operations.values():
        if not operation.finished:
          unfinished_operation_names.append(operation.name)

      if unfinished_operation_names:
        names_list = ', '.join(unfinished_operation_names)
        raise self.OperationNotFinishedError(
            f'The following operations are not yet finished: {names_list}.'
        )

      self._operations = {}


class _SkillExecutionOperation:
  """Information about a single skill execution operation.

  Attributes:
    finished: True if the skill execution has finished.
    name: A unique name for the skill execution operation.
    operation: The current operation proto for the skill execution.
  """

  class OperationAlreadyStartedError(RuntimeError):
    """A disallowed action was taken on an already-started operation."""

  class OperationAlreadyFinishedError(RuntimeError):
    """A disallowed action was taken on a finished operation."""

  class OperationHasNoNameError(ValueError):
    """An attempt was made to create an operation with no name."""

  @property
  def finished(self) -> bool:
    return self._finished_event.is_set()

  @property
  def name(self) -> str:
    return self.operation.name

  @property
  def operation(self) -> operations_pb2.Operation:
    with self._lock:
      return self._operation

  def __init__(
      self,
      canceller: skill_canceller.SkillCancellationManager,
      context: skl.ExecuteContext,
      operation: operations_pb2.Operation,
      request: skill_service_pb2.ExecuteRequest,
      skill_execute: skl.SkillExecuteInterface,
      skill_runtime_data: rd.SkillRuntimeData,
  ) -> None:
    """Initializes the instance.

    Args:
      canceller: Supports cooperative cancellation of the skill.
      context: The skill's ExecuteContext.
      operation: The current operation proto for the skill execution.
      request: The skill's ExecuteRequest.
      skill_execute: The SkillExecute instance.
      skill_runtime_data: The skill's runtime data.

    Raises:
      OperationHasNoNameError: If the specified operation has no name.
    """
    if not operation.name:
      raise self.OperationHasNoNameError('Operation must have a name.')

    self._canceller = canceller
    self._context = context
    self._operation = operation
    self._request = request
    self._skill_execute = skill_execute
    self._skill_runtime_data = skill_runtime_data

    self._supports_cancellation = (
        skill_runtime_data.execution_options.supports_cancellation
    )
    self._started = False
    self._cancelled = False
    self._finished_event = threading.Event()
    self._lock = threading.RLock()

    self._pool = futures.ThreadPoolExecutor()

  def start_execution(self) -> None:
    """Starts execution of the skill."""
    with self._lock:
      if self._started:
        raise self.OperationAlreadyStartedError(
            f'Execution has already started: {self.name!r}.'
        )
      self._started = True

    self._pool.submit(self._execute)

  def request_cancellation(self) -> None:
    """Requests cancellation of the operation.

    Valid requests are ignored if the skill has already finished.

    Raises:
      Exception: Any exception raised when calling the cancellation callback.
      NotImplementedError: If the skill does not support cancellation.
      SkillAlreadyCancelledError: If the skill was already cancelled.
    """
    with self._lock:
      if self._cancelled:
        raise skill_canceller.SkillAlreadyCancelledError(
            'The skill was already cancelled.'
        )
      self._cancelled = True

      if not self._supports_cancellation:
        raise NotImplementedError(
            f'Skill does not support cancellation: {self.name!r}.'
        )

      if self.finished:
        logging.debug(
            (
                'Ignoring cancellation request, since operation %r has already'
                ' finished.'
            ),
            self.name,
        )
        return

    self._canceller.cancel()

  def wait(self, timeout: Optional[float] = None) -> operations_pb2.Operation:
    """Waits for the operation to finish.

    Args:
      timeout: The maximum number of seconds to wait for the operation to
        finish, or None for no timeout.

    Returns:
      The state of the Operation when it either finished or the wait timed out.
    """
    self._finished_event.wait(timeout=timeout)

    return self.operation

  def _execute(self) -> None:
    """Executes the skill."""
    with self._lock:
      if self.finished:
        raise self.OperationAlreadyFinishedError(
            f'The operation has already finished: {self.name!r}.'
        )

      skill = self._skill_execute
      assert skill is not None

      context = self._context
      assert context is not None

    result = None
    error_status = None
    try:
      request = self._proto_to_execute_request(self._request)
      returned_result = skill.execute(request, context)
      if isinstance(returned_result, skill_service_pb2.ExecuteResult):
        logging.warning(
            'Execute returned ExecuteResult instead of the message to be'
            ' wrapped.  Using the returned message directly.'
        )
        result = returned_result
      else:
        result_any = None
        if returned_result is not None:
          result_any = any_pb2.Any()
          result_any.Pack(returned_result)
        result = skill_service_pb2.ExecuteResult(result=result_any)

    except _CannotConstructExecuteRequestError as err:
      error_status = status_pb2.Status(
          code=status.StatusCode.INTERNAL,
          message=(
              'Could not construct execute request for skill'
              f' {self._request.instance.id_version}: {err}.'
          ),
      )
    except skl.SkillCancelledError as err:
      message = f'Skill cancelled during operation {self.name!r}: {err}'
      logging.info(message)

      error_status = status_pb2.Status(
          code=status.StatusCode.CANCELLED, message=message
      )
    # Since we are calling user-provided code here, we want to be as broad as
    # possible and catch anything that could occur.
    except Exception:  # pylint: disable=broad-except
      logging.exception('Skill returned an error duration execution.')

      error_status = status_pb2.Status(
          code=status.StatusCode.INTERNAL,
          message=(
              'Failure during execution of skill'
              f' {self._request.instance.id_version}. Error:'
              f' {traceback.format_exc()}'
          ),
      )

    if error_status is not None:
      error_status.details.add().Pack(
          error_pb2.SkillErrorInfo(
              error_type=error_pb2.SkillErrorInfo.ERROR_TYPE_SKILL
          )
      )

    self._finish(error_status, result)

  def _finish(
      self,
      error: status_pb2.Status | None,
      result: skill_service_pb2.ExecuteResult | None,
  ) -> None:
    """Marks the operation as finished, with an error and/or result."""
    with self._lock:
      if self.finished:
        raise self.OperationAlreadyFinishedError(
            f'The operation has already finished: {self.name!r}.'
        )

      if error is not None:
        self._operation.error.CopyFrom(error)
      if result is not None:
        result_any = any_pb2.Any()
        result_any.Pack(result)
        self._operation.response.CopyFrom(result_any)
      self._operation.done = True

      # Clean up some variables to free memory.
      self._context = None
      self._skill = None

      self._finished_event.set()

  def _proto_to_execute_request(
      self, proto: skill_service_pb2.ExecuteRequest
  ) -> skl.ExecuteRequest:
    """Converts an ExecuteRequest proto to the request to send to the skill.

    Args:
      proto: The proto to convert.

    Returns:
      The request to send to the skill.

    Raises:
      _CannotConstructExecuteRequestError: If the request cannot be converted.
    """
    try:
      params = _unpack_any_from_descriptor(
          proto.parameters, self._skill_runtime_data.parameter_data.descriptor
      )
    except proto_utils.ProtoMismatchTypeError as err:
      raise _CannotConstructExecuteRequestError(str(err)) from err

    return skl.ExecuteRequest(
        params=params,
    )


def _abort_with_status(
    context: grpc.ServicerContext,
    code: status.StatusCode,
    message: str,
    skill_error_info: error_pb2.SkillErrorInfo,
) -> NoReturn:
  """Calls context.abort_with_status.

  This function annotates its (lack of) return type properly so the static type
  checker doesn't think execution might continue after its call (and, e.g.,
  complain about variables possibly being uninitialized when they are used).

  Args:
    context: See context.abort_with_status.
    code: See context.abort_with_status.
    message: See context.abort_with_status.
    skill_error_info: See context.abort_with_status.
  """
  context.abort_with_status(
      error_utils.make_grpc_status_with_error_info(
          code=code, message=message, skill_error_info=skill_error_info
      )
  )

  # This will never be raised, but we need it to satisfy static type checking,
  # since context.abort_with_status does not properly annotate its return value
  # as NoReturn.
  raise AssertionError('This error should not have been raised.')


def _proto_to_get_footprint_request(
    proto: skill_service_pb2.GetFootprintRequest,
    skill_runtime_data: rd.SkillRuntimeData,
) -> skl.GetFootprintRequest:
  """Converts a GetFootprintRequest proto to the request to send to the skill.

  Args:
    proto: The proto to convert.
    skill_runtime_data: The runtime data for the skill.

  Returns:
    The request to send to the skill.

  Raises:
    _CannotConstructGetFootprintRequestError: If the request cannot be
      converted.
  """
  try:
    params = _unpack_any_from_descriptor(
        proto.parameters, skill_runtime_data.parameter_data.descriptor
    )
  except proto_utils.ProtoMismatchTypeError as err:
    raise _CannotConstructGetFootprintRequestError(str(err)) from err

  return skl.GetFootprintRequest(
      params=params,
  )


def _unpack_any_from_descriptor(
    any_message: any_pb2.Any, descriptor: proto_descriptor.Descriptor
) -> proto_message.Message:
  """Unpacks a proto Any into a message, given the message's Descriptor.

  Args:
    any_message: a proto Any message.
    descriptor: The descriptor of the target message type.

  Returns:
    The unpacked proto message.

  Raises:
    proto_utils.ProtoMismatchTypeError: If the type of `proto_message` does not
      match that of the specified Any proto.
  """
  # Cache the generated class to save time and provide a consistent type to the
  # skill.
  try:
    proto_message_type = _message_type_cache[descriptor.full_name]
  except KeyError:
    proto_message_type = _message_type_cache[descriptor.full_name] = (
        message_factory.GetMessageClass(descriptor)
    )

  return proto_utils.unpack_any(any_message, proto_message_type())


# Cache used by _unpack_any_from_descriptor.
_message_type_cache = {}
