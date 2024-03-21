# Copyright 2023 Intrinsic Innovation LLC

"""A thin wrapper around the executive gRPC service to make it easy to use.

See go/intrinsic-python-api and
go/intrinsic-workcell-python-implementation-design for
more details.

Typical usage example:

from intrinsic.solutions import execution
from intrinsic.executive.proto import executive_service_pb2

my_executive = execution.Executive()
my_executive.load(my_behavior_tree)
my_executive.start()
my_executive.suspend()
my_executive.reset()
"""

import datetime
import enum
import time
from typing import Any, List, Optional, Union, cast

from google.longrunning import operations_pb2
import grpc
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.executive.proto import executive_execution_mode_pb2
from intrinsic.executive.proto import executive_service_pb2
from intrinsic.executive.proto import executive_service_pb2_grpc
from intrinsic.executive.proto import run_metadata_pb2
from intrinsic.solutions import behavior_tree as bt
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import error_processing
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import ipython
from intrinsic.solutions import simulation as simulation_mod
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions
from intrinsic.util.grpc import error_handling

_DEFAULT_POLLING_INTERVAL_IN_SECONDS = 0.5
_CSS_SUCCESS_STYLE = (
    "color: #2c8b22; font-family: monospace; font-weight: bold; "
    "padding-left: var(--jp-code-padding);"
)
_CSS_INTERRUPTED_STYLE = (
    "color: #bb5333; font-family: monospace; font-weight: bold; "
    "padding-left: var(--jp-code-padding);"
)
_PROCESS_TREE_SCOPE = "PROCESS_TREE"

BehaviorTreeOrActionType = Union[
    bt.BehaviorTree,
    bt.Node,
    List[Union[actions.ActionBase, List[actions.ActionBase]]],
    actions.ActionBase,
]


def _flatten_list(list_to_flatten: List[Any]) -> List[Any]:
  """Recursively flatten a list.

  Examples:
    _flatten_list([1,2,[3,[4,5]]]) -> [1,2,3,4,5]
    _flatten_list([1]) -> [1]
    _flatten_list([1, [2, 3]]) -> [1,2,3]

  Args:
    list_to_flatten: input list

  Returns:
    Flat list with the elements of input list and any nested
    lists found therein.
  """
  flat_list = []
  for element in list_to_flatten:
    if isinstance(element, list):
      flat_list.extend(_flatten_list(element))
    else:
      flat_list.append(element)
  return flat_list


class Error(solutions_errors.Error):
  """Top-level module error for executive."""


class ExecutionFailedError(Error):
  """Thrown in case of errors during execution."""


class NoActiveOperationError(Error):
  """Thrown in case that no operation is active when the call requires one."""


class OperationNotFoundError(Error):
  """Thrown in case that a specific operation was not available."""


class Operation:
  """Class representing an active operation in the executive.

  Attributes:
    name: Name of the operation.
    done: Whether the operation has completed or not (independent of outcome).
    proto: Proto representation.
    metadata: RunMetadata for an active operation containing more state
      information.
  """

  _stub: executive_service_pb2_grpc.ExecutiveServiceStub
  _operation_proto: operations_pb2.Operation
  _metadata: run_metadata_pb2.RunMetadata

  def __init__(
      self,
      stub: executive_service_pb2_grpc.ExecutiveServiceStub,
      operation_proto: operations_pb2.Operation,
  ):
    self._stub = stub
    self._operation_proto = operation_proto
    self._metadata = run_metadata_pb2.RunMetadata()
    self._operation_proto.metadata.Unpack(self._metadata)

  @property
  def name(self) -> str:
    return self._operation_proto.name

  @property
  def done(self) -> bool:
    return self._operation_proto.done

  @property
  def proto(self) -> operations_pb2.Operation:
    return self._operation_proto

  @property
  def metadata(self) -> run_metadata_pb2.RunMetadata:
    return self._metadata

  @error_handling.retry_on_grpc_unavailable
  def update(self) -> None:
    """Update the operation by querying the executive."""
    self.update_from_proto(
        self._stub.GetOperation(
            operations_pb2.GetOperationRequest(
                name=self._operation_proto.name,
            )
        )
    )

  def find_tree_and_node_id(self, node_name: str) -> bt.NodeIdentifierType:
    """Searches the tree in this Operation for a node with name node_name.

    Args:
      node_name: Name of a node to search for in the tree.

    Returns:
      A NodeIdentifierType referencing the tree id and node id for the node. The
      result can be passed to calls requiring a NodeIdentifierType.

    Raises:
      solution_errors.NotFoundError if there is not behavior_tree.
      solution_errors.NotFoundError if not matching node exists.
      solution_errors.InvalidArgumentError if there is more than one matching
        node or if the node or its tree do not have an id defined.
    """
    if not self.metadata.HasField("behavior_tree"):
      raise solutions_errors.NotFoundError("No behavior tree in operation.")
    tree = bt.BehaviorTree.create_from_proto(self.metadata.behavior_tree)
    return tree.find_tree_and_node_id(node_name)

  def find_tree_and_node_ids(
      self, node_name: str
  ) -> list[bt.NodeIdentifierType]:
    """Searches the tree in this Operation for all nodes with name node_name.

    Args:
      node_name: Name of a node to search for in the tree.

    Returns:
      solution_errors.NotFoundError if there is not behavior_tree.
      A list of NodeIdentifierType referencing the tree id and node id for the
      node. The list contains information about all matching nodes, even if the
      nodes do not have a node or tree id. In that case the values are None.
    """
    if not self.metadata.HasField("behavior_tree"):
      raise solutions_errors.NotFoundError("No behavior tree in operation.")
    tree = bt.BehaviorTree.create_from_proto(self.metadata.behavior_tree)
    return tree.find_tree_and_node_ids(node_name)

  def update_from_proto(self, proto: operations_pb2.Operation) -> None:
    """Update information from a proto."""
    self._operation_proto = proto
    self._operation_proto.metadata.Unpack(self._metadata)


class Executive:
  """Wrapper for the Executive gRPC service."""

  @utils.protoenum(
      proto_enum_type=executive_service_pb2.ResumeOperationRequest.ResumeMode,
      unspecified_proto_enum_map_to_none=executive_service_pb2.ResumeOperationRequest.RESUME_MODE_UNSPECIFIED,
  )
  class ResumeMode(enum.Enum):
    """Represents the intended kind of resumption when invoking Resume."""

  @utils.protoenum(
      proto_enum_type=executive_execution_mode_pb2.SimulationMode,
      unspecified_proto_enum_map_to_none=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_UNSPECIFIED,
      strip_prefix="SIMULATION_MODE_",
  )
  class SimulationMode(enum.Enum):
    """Represents the kind of simulation when starting a process."""

  @utils.protoenum(
      proto_enum_type=executive_execution_mode_pb2.ExecutionMode,
      unspecified_proto_enum_map_to_none=executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_UNSPECIFIED,
      strip_prefix="EXECUTION_MODE_",
  )
  class ExecutionMode(enum.Enum):
    """Represents the mode of execution for running a process."""

  _stub: executive_service_pb2_grpc.ExecutiveServiceStub
  _error_loader: error_processing.ErrorsLoader
  _simulation: Optional[simulation_mod.Simulation]
  _polling_interval_in_seconds: float
  _operation: Optional[Operation]

  def __init__(
      self,
      stub: executive_service_pb2_grpc.ExecutiveServiceStub,
      error_loader: error_processing.ErrorsLoader,
      simulation: Optional[simulation_mod.Simulation] = None,
      polling_interval_in_seconds: float = _DEFAULT_POLLING_INTERVAL_IN_SECONDS,
  ):
    """Constructs a new Executive object.

    Args:
      stub: The gRPC stub to be used for communication with the executive
        service.
      blackboard_stub: The gRPC stub to be used for blackboard related calls.
      error_loader: Can load ErrorReports about executions
      simulation: The workcell simulation module (optional).
      polling_interval_in_seconds: Number of seconds to wait while polling for
        the operation state in blocking calls such as Executive.suspend().
    """
    self._stub = stub
    self._error_loader = error_loader
    self._simulation = simulation
    self._polling_interval_in_seconds = polling_interval_in_seconds
    self._operation = None

  @classmethod
  def connect(
      cls,
      grpc_channel: grpc.Channel,
      error_loader: error_processing.ErrorsLoader,
      simulation: Optional[simulation_mod.Simulation] = None,
      polling_interval_in_seconds: float = _DEFAULT_POLLING_INTERVAL_IN_SECONDS,
  ) -> "Executive":
    """Connect to a running executive.

    Args:
      grpc_channel: Channel to the executive gRPC service.
      error_loader: Loads error data for executive runs.
      simulation: The workcell simulation module (optional).
      polling_interval_in_seconds: Number of seconds to wait while polling for
        the operation state in blocking calls such as Executive.suspend().

    Returns:
      A newly created instance of the Executive wrapper class.
    """
    stub = executive_service_pb2_grpc.ExecutiveServiceStub(grpc_channel)
    return cls(
        stub,
        error_loader,
        simulation,
        polling_interval_in_seconds,
    )

  @property
  def operation(self) -> Operation:
    self._update_operation()

    # Still no operation, none available in executive
    if self._operation is None:
      raise OperationNotFoundError("No active operation")

    return self._operation

  @error_handling.retry_on_grpc_unavailable
  def _update_operation(self) -> None:
    """Gets up to date information about the current operation."""
    # If an operation exists, try to update to confirm it still exists
    if self._operation is not None:
      try:
        self._operation.update()
      except grpc.RpcError as e:
        rpc_call = cast(grpc.Call, e)
        if rpc_call.code() != grpc.StatusCode.NOT_FOUND:
          raise
        self._operation = None

    # No operation, there was none or it became invalid, try to fetch new
    if self._operation is None:
      resp = self._stub.ListOperations(operations_pb2.ListOperationsRequest())
      if resp.operations:
        self._operation = Operation(self._stub, resp.operations[0])

  @property
  def execution_mode(self) -> "Executive.ExecutionMode":
    """Currently set mode of execution (normal or step-wise)."""
    mode = Executive.ExecutionMode.from_proto(
        self.operation.metadata.execution_mode
    )
    if mode is None:
      return Executive.ExecutionMode.NORMAL
    return mode

  @property
  def simulation_mode(self) -> "Executive.SimulationMode":
    """Currently set mode of simulation (physics or kinematics)."""
    mode = Executive.SimulationMode.from_proto(
        self.operation.metadata.simulation_mode
    )
    # mode should never be None, the executive always provides one, set the
    # executive's default just in case.
    if mode is None:
      return Executive.SimulationMode.REALITY
    return mode

  def cancel(self) -> None:
    """Cancels plan execution and blocks until execution finishes.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On operation not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    self._cancel(blocking=True)

  def cancel_async(self) -> None:
    """Asynchronously cancels plan execution; returns immediately.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On operation not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    self._cancel(blocking=False)

  def _cancel(self, blocking) -> None:
    """Cancels plan execution (CANCELABLE --> FAILED | SUCCEEDED).

    Args:
      blocking: If True, repeatedly poll executive state until FAILED.
        Otherwise, returns immediately.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On executive not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    cancellation_finished_states = {
        behavior_tree_pb2.BehaviorTree.CANCELED,
        behavior_tree_pb2.BehaviorTree.FAILED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    }
    cancellation_unfinished_states = {
        behavior_tree_pb2.BehaviorTree.ACCEPTED,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.SUSPENDED,
        behavior_tree_pb2.BehaviorTree.CANCELING,
    }

    self._cancel_with_retry()

    state = self.operation.metadata.behavior_tree_state
    if blocking:
      while state not in cancellation_finished_states:
        assert (
            state in cancellation_unfinished_states
        ), f"Unexpected state: {state}."
        time.sleep(self._polling_interval_in_seconds)
        state = self.operation.metadata.behavior_tree_state

  def suspend(self) -> None:
    """Requests to suspend plan execution and blocks until SUSPENDED.

    Since the executive currently cannot preempt running skills, this function
    waits until all running skills have terminated.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On executive not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    self._suspend(blocking=True)

  def suspend_async(self) -> None:
    """Requests to suspend plan execution and returns immediately.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On executive not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    self._suspend(blocking=False)

  def _suspend(self, blocking) -> None:
    """Stops plan execution after all currently running actions succeed (RUNNING --> SUSPENDED).

    Args:
      blocking: If True, repeatedly poll executive state until SUSPENDED.
        Otherwise, returns immediately.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On executive not in RUNNING state.
      grpc.RpcError: On any other gRPC error.
    """
    self._suspend_with_retry()
    if not blocking:
      return

    while True:
      if self.operation.metadata.behavior_tree_state in [
          behavior_tree_pb2.BehaviorTree.SUSPENDED,
          behavior_tree_pb2.BehaviorTree.FAILED,
          behavior_tree_pb2.BehaviorTree.SUCCEEDED,
          behavior_tree_pb2.BehaviorTree.CANCELED,
      ]:
        break

      time.sleep(self._polling_interval_in_seconds)

  def resume(
      self,
      mode: Optional["Executive.ResumeMode"] = None,
  ) -> None:
    """Resumes plan execution (SUSPENDED --> RUNNING).

    Args:
     mode: The resume mode, STEP and NEXT work when in step-wise execution mode,
       CONTINUE will switch to NORMAL execution mode before resume.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      solutions_errors.InvalidArgumentError: On executive not in SUSPENDED
      state.
      grpc.RpcError: On any other gRPC error.
    """
    self._resume_with_retry(mode)

  def reset(self) -> None:
    """Resets the current operation to the state from when it was loaded.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
    """
    try:
      self._reset_with_retry()
    except OperationNotFoundError:
      pass

  def run_async(
      self,
      plan_or_action: Optional[BehaviorTreeOrActionType] = None,
      *,
      silence_outputs: bool = False,
      step_wise: bool = False,
      start_node: Optional[bt.NodeIdentifierType] = None,
      simulation_mode: Optional["Executive.SimulationMode"] = None,
      embed_skill_traces: bool = False,
  ):
    """Requests execution of an action or plan and returns immediately.

    Note that an action can be a general action or any skill obtained through
    Skills.

    If plan_or_action is None, runs the initial plan as specified in the
    Kubernetes template.

    Implicitly calls simulation.reset() if this is the first action or plan
    being executed (after an executive.reset()). This makes sure that any world
    edits that might have occurred are reflected in the simulation.

    Args:
      plan_or_action: A behavior tree, list of actions, or a single action or
        skill.
      silence_outputs: If true, do not show success or error outputs of the
        execution in Jupyter.
      step_wise: Execute step-wise, i.e., suspend after each node of the tree.
      start_node: Run the specified node as if it were the root node of a tree
        instead of the complete tree.
      simulation_mode: Set the simulation mode on the start request. If None
        will execute in whatever mode is currently set in the executive.
      embed_skill_traces: If true, execution traces in Google Cloud will
        incorporate all information from skill traces, otherwise execution
        traces contain links to individual skill traces.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
    """
    self._run(
        plan_or_action,
        blocking=False,
        silence_outputs=silence_outputs,
        step_wise=step_wise,
        start_node=start_node,
        simulation_mode=simulation_mode,
        embed_skill_traces=embed_skill_traces,
    )

  def run(
      self,
      plan_or_action: Optional[BehaviorTreeOrActionType],
      *,
      silence_outputs: bool = False,
      step_wise: bool = False,
      start_node: Optional[bt.NodeIdentifierType] = None,
      simulation_mode: Optional["Executive.SimulationMode"] = None,
      embed_skill_traces: bool = False,
  ):
    """Executes an action or plan and blocks until completion.

    This corresponds to running load and start after one another.

    Note that an action can be a general action or any skill obtained through
    Skills.

    If plan_or_action is None, runs the initial plan as specified in the
    Kubernetes template.

    Implicitly calls simulation.reset() if this is the first action or plan
    being executed (after an executive.reset()). This makes sure that any world
    edits that might have occurred are reflected in the simulation.

    Args:
      plan_or_action: A behavior tree, a list of actions (can be nested one
        level), or a single action.
      silence_outputs: If true, do not show success or error outputs of the
        execution in Jupyter.
      step_wise: Execute step-wise, i.e., suspend after each node of the tree.
      start_node: Run the specified node as if it were the root node of a tree
        instead of the complete tree.
      simulation_mode: Set the simulation mode on the start request. If None
        will execute in whatever mode is currently set in the executive.
      embed_skill_traces: If true, execution traces in Google Cloud will
        incorporate all information from skill traces, otherwise execution
        traces contain links to individual skill traces.

    Raises:
      ExecutionFailedError: On unexpected state of the executive during plan
                execution.
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.

    Returns:
      The start and end timestamps which can be used to query the logs.
    """
    self._run(
        plan_or_action,
        blocking=True,
        silence_outputs=silence_outputs,
        step_wise=step_wise,
        start_node=start_node,
        simulation_mode=simulation_mode,
        embed_skill_traces=embed_skill_traces,
    )
    if not silence_outputs:
      ipython.display_html_or_print_msg(
          f'<span style="{_CSS_SUCCESS_STYLE}">Execution successful</span>',
          "Execution successful",
      )

  def _run(
      self,
      plan_or_action: Union[BehaviorTreeOrActionType],
      blocking: bool,
      silence_outputs: bool,
      step_wise: bool,
      simulation_mode: "Executive.SimulationMode",
      embed_skill_traces: bool,
      start_node: Optional[bt.NodeIdentifierType],
  ) -> None:
    """Implementation of run and run_async.

    Args:
      plan_or_action: A behavior tree, list of actions (can be nested one
        level), or a single action.
      blocking: If True, waits until execution finishes. Otherwise, returns
        immediately after starting.
      silence_outputs: If true, do not show success or error outputs of the
        execution in Jupyter.
      step_wise: Execute step-wise, i.e., suspend after each node of the tree.
      simulation_mode: Set the simulation mode on the start request. If None
        will execute in whatever mode is currently set in the executive.
      embed_skill_traces: If true, execution traces in Google Cloud will
        incorporate all information from skill traces, otherwise execution
        traces contain links to individual skill traces.
      start_node: Run the specified node as if it were the root node of a tree
        instead of the complete tree.

    Raises:
      ExecutionFailedError: On unexpected state of the executive during plan
                execution.
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
      OperationNotFoundError: if no operation is currently active.
    """
    # Reset the simulation the first time that anything in the executive is run.
    # This uses the presence of the operation as a heuristic to determine that
    # this is the case under the assumption that any subsequent runs by this
    # file or the frontend will always leave an operation behind and only
    # deleted it before loading a new one.
    if self._simulation is not None:
      try:
        self.operation
      except OperationNotFoundError:
        if not silence_outputs:
          print(
              "Triggering simulation.reset() "
              "since world edits might have occurred."
          )
        self._simulation.reset()

    if plan_or_action is None:
      if self._operation is None:
        raise OperationNotFoundError(
            "No operation loaded, run() requires passing a BT"
        )

      self._start_with_retry(
          step_wise=step_wise,
          start_node=start_node,
          embed_skill_traces=embed_skill_traces,
      )
      return

    self.load(plan_or_action)
    self.start(
        blocking,
        step_wise=step_wise,
        start_node=start_node,
        simulation_mode=simulation_mode,
        embed_skill_traces=embed_skill_traces,
    )

  def load(
      self, behavior_tree_or_action: Optional[BehaviorTreeOrActionType]
  ) -> None:
    """Loads an action or behavior tree into the executive.

    Note that an action can be a general action or any skill obtained through
    skills.

    Args:
      behavior_tree_or_action: A behavior tree, a list of actions (can be nested
        one level) or a single action.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
    """
    behavior_tree = None
    if isinstance(behavior_tree_or_action, actions.ActionBase):
      behavior_tree = bt.BehaviorTree(
          root=bt.Task(cast(actions.ActionBase, behavior_tree_or_action))
      )
    elif isinstance(behavior_tree_or_action, list):
      action_list = _flatten_list(behavior_tree_or_action)
      behavior_tree = bt.BehaviorTree(
          root=bt.Sequence(
              children=[
                  bt.Task(cast(actions.ActionBase, a)) for a in action_list
              ]
          )
      )
    elif isinstance(behavior_tree_or_action, bt.BehaviorTree):
      behavior_tree = cast(bt.BehaviorTree, behavior_tree_or_action)
    elif isinstance(behavior_tree_or_action, bt.Node):
      behavior_tree = bt.BehaviorTree(root=behavior_tree_or_action)

    request = executive_service_pb2.CreateOperationRequest()
    if behavior_tree is not None:
      behavior_tree.validate_id_uniqueness()
      request.behavior_tree.CopyFrom(behavior_tree.proto)

    try:
      self._delete_with_retry()
    except OperationNotFoundError:
      pass

    self._create_with_retry(request)

  def start(
      self,
      blocking: bool = True,
      silence_outputs: bool = False,
      *,
      step_wise: bool = False,
      start_node: Optional[bt.NodeIdentifierType] = None,
      simulation_mode: Optional["Executive.SimulationMode"] = None,
      embed_skill_traces: bool = False,
  ) -> None:
    """Starts the currently loaded plan.

    Args:
      blocking: If True, waits until execution finishes. Otherwise, returns
        immediately after starting.
      silence_outputs: If true, do not show success or error outputs of the
        execution in Jupyter.
      step_wise: Execute step-wise, i.e., suspend after each node of the tree.
      start_node: Start only the specified node instead of the complete tree.
      simulation_mode: Set the simulation mode on the start request. If None
        will execute in whatever mode is currently set in the executive.
      embed_skill_traces: If true, execution traces in Google Cloud will
        incorporate all information from skill traces, otherwise execution
        traces contain links to individual skill traces.

    Raises:
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
    """

    self._start_with_retry(
        step_wise=step_wise,
        start_node=start_node,
        simulation_mode=simulation_mode,
        embed_skill_traces=embed_skill_traces,
    )

    if blocking:
      try:
        self.block_until_completed(silence_outputs=silence_outputs)
      except KeyboardInterrupt as e:
        state = self.operation.metadata.behavior_tree_state
        if state == behavior_tree_pb2.BehaviorTree.RUNNING:
          ipython.display_html_or_print_msg(
              (
                  f'<span style="{_CSS_INTERRUPTED_STYLE}">Execution'
                  " interrupted - suspending execution...</span>"
              ),
              "Execution interrupted - suspending execution...",
          )
          # Use suspend_async() to immediately stop and return as this is the
          # intended user experience when stopping in jupyter/KeyboardInterrupt
          self.suspend_async()
        else:
          ipython.display_html_or_print_msg(
              (
                  f'<span style="{_CSS_INTERRUPTED_STYLE}">Python interrupted'
                  f" - executive is in state {state}</span>"
              ),
              f"Python interrupted - executive is in state {state}.",
          )
        raise e

  def block_until_completed(self, *, silence_outputs: bool = False) -> None:
    """Waits until plan execution has begun and then stops.

    Polls executive state every self._polling_interval_in_seconds.

    Args:
      silence_outputs: If true, do not show success or error outputs of the
        execution in Jupyter.

    Raises:
      ExecutionFailedError: On unexpected state of the executive during plan
                execution.
      solutions_errors.UnavailableError: On executive service not reachable.
      grpc.RpcError: On any other gRPC error.
    """

    # States that are entered upon processing an action to completion.
    completed_states = {
        behavior_tree_pb2.BehaviorTree.SUSPENDED,
        behavior_tree_pb2.BehaviorTree.FAILED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    }

    # States in which an action has not yet been completed.
    uncompleted_states = {
        behavior_tree_pb2.BehaviorTree.ACCEPTED,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.CANCELING,
    }

    while True:
      state = self.operation.metadata.behavior_tree_state
      if state in completed_states:
        break
      assert state in uncompleted_states, f"Unexpected state: {state}"
      time.sleep(self._polling_interval_in_seconds)

    if (
        self.operation.metadata.behavior_tree_state
        == behavior_tree_pb2.BehaviorTree.FAILED
    ):
      error_msg = (
          "Execution failed."
          "\nEnter executive.get_errors() for rich "
          "interactive details in Jupyter notebook."
      )
      if not silence_outputs:
        error_summary = self.get_errors()
        error_summary.display_only_in_ipython()
        error_msg += f"\n{error_summary.summary}"
      raise ExecutionFailedError(error_msg)

  def get_errors(
      self,
      print_level: error_processing.PrintLevel = (
          error_processing.PrintLevel.OFF
      ),
  ) -> error_processing.ErrorGroup:
    """Loads and optionally prints errors from current, failed operation.

    Args:
      print_level: If not set to 'OFF', error reports are printed.

    Returns:
      Error summaries.
    """
    error_summaries = self._error_loader.extract_error_data(
        self.operation.proto
    )
    error_summaries.print_info(print_level)
    return error_summaries

  @error_handling.retry_on_grpc_unavailable
  def _delete_with_retry(self) -> None:
    operation_name = self.operation.name
    self._stub.DeleteOperation(
        operations_pb2.DeleteOperationRequest(name=operation_name)
    )
    self._operation = None

  @error_handling.retry_on_grpc_unavailable
  def _start_with_retry(
      self,
      *,
      step_wise: bool = False,
      start_node: Optional[bt.NodeIdentifierType] = None,
      simulation_mode: Optional["Executive.SimulationMode"] = None,
      embed_skill_traces: bool = False,
  ) -> None:
    """Starts the executive and handles errors."""
    if self._operation is None:
      raise RuntimeError("Internal error: expected operation to be loaded.")
    request = executive_service_pb2.StartOperationRequest(
        name=self._operation.name
    )
    if simulation_mode is not None:
      request.simulation_mode = simulation_mode.value
      if simulation_mode == Executive.SimulationMode.DRAFT:
        print("Starting in draft mode.")
    if step_wise:
      request.execution_mode = (
          executive_execution_mode_pb2.EXECUTION_MODE_STEP_WISE
      )
    if embed_skill_traces:
      request.skill_trace_handling = (
          run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_EMBED
      )
    else:
      request.skill_trace_handling = (
          run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK
      )
    if start_node is not None:
      request.start_tree_id = start_node.tree_id
      request.start_node_id = start_node.node_id
    self._operation.update_from_proto(self._stub.StartOperation(request))

  @error_handling.retry_on_grpc_unavailable
  def _cancel_with_retry(self) -> None:
    operation_name = self.operation.name
    self._stub.CancelOperation(
        operations_pb2.CancelOperationRequest(name=operation_name)
    )

  @error_handling.retry_on_grpc_unavailable
  def _resume_with_retry(
      self,
      mode: Optional[ResumeMode] = None,
  ) -> None:
    operation = self.operation
    operation.update_from_proto(
        self._stub.ResumeOperation(
            executive_service_pb2.ResumeOperationRequest(
                name=operation.name,
                mode=None if mode is None else mode.value,
            )
        )
    )

  @error_handling.retry_on_grpc_unavailable
  def _reset_with_retry(self) -> None:
    operation_name = self.operation.name
    self._stub.ResetOperation(
        executive_service_pb2.ResetOperationRequest(name=operation_name)
    )

  @error_handling.retry_on_grpc_unavailable
  def _suspend_with_retry(self) -> None:
    operation_name = self.operation.name
    self._stub.SuspendOperation(
        executive_service_pb2.SuspendOperationRequest(name=operation_name)
    )

  @error_handling.retry_on_grpc_unavailable
  def _create_with_retry(self, request) -> None:
    self._operation = Operation(self._stub, self._stub.CreateOperation(request))
