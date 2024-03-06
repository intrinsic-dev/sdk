# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.solutions.execution."""

import datetime
import time
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from google.longrunning import operations_pb2
from google.protobuf import any_pb2
from google.protobuf import text_format
import grpc
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.executive.proto import executive_execution_mode_pb2
from intrinsic.executive.proto import executive_service_pb2
from intrinsic.executive.proto import executive_service_pb2_grpc
from intrinsic.executive.proto import run_metadata_pb2
from intrinsic.logging.errors.proto import error_report_pb2
from intrinsic.solutions import behavior_tree as bt
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import error_processing
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import execution
from intrinsic.solutions import simulation as simulation_mod
from intrinsic.solutions.internal import behavior_call
from intrinsic.solutions.testing import test_skill_params_pb2


# Make sure all log items are considered.
_TIMESTAMP = 2147483647

_OPERATION_NAME = 'abc123'


def _to_any(msg):
  x = any_pb2.Any()
  x.Pack(msg)
  return x


class _GrpcError(grpc.RpcError, grpc.Call):

  def __init__(self, code):
    self._code = code

  def code(self):
    return self._code

  def details(self):
    return '_GrpcError'


@mock.patch.object(
    target=time, attribute='sleep', new=mock.MagicMock()
)  # From retry logic in errors.py.
class ExecutiveTest(parameterized.TestCase):
  """Tests all public methods of the Executive gRPC wrapper class."""

  def setUp(self):
    super().setUp()
    self._installer_stub = mock.MagicMock()
    self._errors: error_processing.ErrorsLoader = error_processing.ErrorsLoader(
        self._installer_stub
    )
    self._executive_service_stub: (
        executive_service_pb2_grpc.ExecutiveServiceStub
    ) = mock.MagicMock()
    self._simulation: simulation_mod.Simulation = mock.MagicMock()
    self._executive: execution.Executive = execution.Executive(
        self._executive_service_stub,
        self._errors,
        self._simulation,
    )

  def _create_operation_proto(
      self,
      state: behavior_tree_pb2.BehaviorTree.State = behavior_tree_pb2.BehaviorTree.RUNNING,
      bt_proto: behavior_tree_pb2.BehaviorTree = behavior_tree_pb2.BehaviorTree(),
  ):
    metadata = run_metadata_pb2.RunMetadata(behavior_tree_state=state)
    metadata.behavior_tree.CopyFrom(bt_proto)
    done = False
    if state in [
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.FAILED,
        behavior_tree_pb2.BehaviorTree.CANCELED,
    ]:
      done = True
    return operations_pb2.Operation(
        name=_OPERATION_NAME,
        done=done,
        metadata=_to_any(metadata),
    )

  def _setup_create_operation(self, setup_empty_list_operations: bool = True):
    """Makes a create call to prime the executive client with an operation."""
    self._executive_service_stub.CreateOperation.side_effect = (
        # Lambda isn't long, the arguments are...
        # pylint: disable=g-long-lambda
        lambda request: self._create_operation_proto(
            behavior_tree_pb2.BehaviorTree.ACCEPTED,
            bt_proto=request.behavior_tree,
        )
    )

    if setup_empty_list_operations:
      # Will try to list existing operations before, report none
      list_response = operations_pb2.ListOperationsResponse()
      self._executive_service_stub.ListOperations.return_value = list_response

  def _setup_start_operation(self):
    start_response = self._create_operation_proto(
        behavior_tree_pb2.BehaviorTree.RUNNING
    )
    self._executive_service_stub.StartOperation.return_value = start_response

  def _create_operation(
      self,
      my_bt: bt.BehaviorTree = bt.BehaviorTree(root=bt.Sequence()),
  ):
    """Makes a create call to prime the executive client with an operation."""
    self._setup_create_operation()
    self._executive.load(my_bt)

  def _setup_get_operation(
      self,
      state: behavior_tree_pb2.BehaviorTree.State = behavior_tree_pb2.BehaviorTree.RUNNING,
      bt_proto: behavior_tree_pb2.BehaviorTree = behavior_tree_pb2.BehaviorTree(),
  ):
    """Makes a create call to prime the executive client with an operation."""
    response = self._create_operation_proto(state, bt_proto)
    self._executive_service_stub.GetOperation.return_value = response

  def _setup_get_operation_sequence(
      self,
      states: list[behavior_tree_pb2.BehaviorTree.State],
  ):
    """Makes a GetOperation sequence."""
    self._executive_service_stub.GetOperation.side_effect = [
        self._create_operation_proto(state) for state in states
    ]

  def test_load_works(self):
    """Tests if executive.load() calls CreateOperation in the executive service."""
    list_response = operations_pb2.ListOperationsResponse()
    self._executive_service_stub.ListOperations.return_value = list_response

    response = self._create_operation_proto(
        behavior_tree_pb2.BehaviorTree.ACCEPTED
    )
    self._executive_service_stub.CreateOperation.return_value = response

    my_bt = bt.BehaviorTree(root=bt.Sequence())
    self._executive.load(my_bt)

    self._executive_service_stub.CreateOperation.assert_called_with(
        executive_service_pb2.CreateOperationRequest(behavior_tree=my_bt.proto)
    )

  def test_load_validates_uniqueness(self):
    """Tests if executive.load() validates uniqueness of ids."""
    list_response = operations_pb2.ListOperationsResponse()
    self._executive_service_stub.ListOperations.return_value = list_response

    my_bt = bt.BehaviorTree(root=bt.Sequence(children=[bt.Fail()]))
    my_bt.root.node_id = 1
    my_bt.root.children[0].node_id = 1

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        '.*violates uniqueness.*',
    ):
      self._executive.load(my_bt)

  def test_run_async_works(self):
    """Tests if executive.run_async() calls start in the executive service."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.ACCEPTED)
    response = self._create_operation_proto(
        behavior_tree_pb2.BehaviorTree.RUNNING
    )
    self._executive_service_stub.StartOperation.return_value = response

    self._executive.run_async()

    self._executive_service_stub.StartOperation.assert_called_with(
        executive_service_pb2.StartOperationRequest(
            name=_OPERATION_NAME,
            skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
        )
    )

  def test_operation_find_name(self):
    """Tests if executive.operation.find_tree_and_node_id works."""
    my_bt = bt.BehaviorTree(root=bt.Sequence(children=[bt.Fail(name='a_node')]))
    my_bt.tree_id = 'tree'
    my_bt.root.node_id = 1
    my_bt.root.children[0].node_id = 2
    self._create_operation(my_bt)
    self._setup_get_operation(
        behavior_tree_pb2.BehaviorTree.ACCEPTED, bt_proto=my_bt.proto
    )

    self.assertEqual(
        self._executive.operation.find_tree_and_node_id('a_node'), ('tree', 2)
    )

  def test_run_async_fails_on_unavailable_error(self):
    """Tests if executive.run_async() translates UNAVAILABLE error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.ACCEPTED)

    self._executive_service_stub.StartOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNAVAILABLE
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.run_async()
    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)
    for _ in range(6):  # Will retry 5 times.
      self._executive_service_stub.StartOperation.assert_called_with(
          executive_service_pb2.StartOperationRequest(
              name=_OPERATION_NAME,
              skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
          )
      )

  def test_run_async_fails_on_grpc_error(self):
    """Tests if executive.run_async() forwards other grpc errors correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.ACCEPTED)

    self._executive_service_stub.StartOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNKNOWN
    )

    with self.assertRaises(_GrpcError):
      self._executive.run_async()

    self._executive_service_stub.StartOperation.assert_called_once_with(
        executive_service_pb2.StartOperationRequest(
            name=_OPERATION_NAME,
            skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
        )
    )

  def test_run_async_works_on_action(self):
    """Tests if executive.run_async(action) calls create."""
    self._setup_create_operation()

    my_action = behavior_call.Action(skill_id='my_action')

    self._executive.run_async(my_action)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.task.call_behavior.CopyFrom(
        my_action.proto
    )
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

  def test_run_async_on_action_fails_on_unavailable_error(self):
    """Tests if executive.run_async(action) translates UNAVAILABLE error correctly."""

    list_response = operations_pb2.ListOperationsResponse()
    self._executive_service_stub.ListOperations.return_value = list_response

    self._executive_service_stub.CreateOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNAVAILABLE
    )

    my_action = behavior_call.Action(skill_id='my_action')
    with self.assertRaises(_GrpcError) as context:
      self._executive.run_async(my_action)
    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)
    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.task.call_behavior.CopyFrom(
        my_action.proto
    )
    for _ in range(6):  # Will retry 5 times.
      self._executive_service_stub.CreateOperation.assert_called_with(
          create_request
      )

  def test_run_async_on_action_fails_on_grpc_error(self):
    """Tests if executive.run_async(action) forwards other grpc errors correctly."""

    list_response = operations_pb2.ListOperationsResponse()
    self._executive_service_stub.ListOperations.return_value = list_response

    self._executive_service_stub.CreateOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNKNOWN
    )

    my_action = behavior_call.Action(skill_id='my_action')
    with self.assertRaises(_GrpcError):
      self._executive.run_async(my_action)
    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.task.call_behavior.CopyFrom(
        my_action.proto
    )
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

  def test_run_async_works_on_behavior_tree_node(self):
    """Tests if executive.run_async(node) calls create."""
    self._setup_create_operation()

    my_node = bt.Fail()
    self._executive.run_async(my_node)

    create_request = executive_service_pb2.CreateOperationRequest()
    (create_request.behavior_tree.root.CopyFrom(my_node.proto))
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

  def test_run_works(self):
    """Tests if executive.run(action) waits for success."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.task.call_behavior.CopyFrom(
        my_action.proto
    )
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )
    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_run_start_node_works(self):
    """Tests if executive.run(start_node) executes the start node."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    tree = bt.BehaviorTree()
    tree_id = tree.generate_and_set_unique_id()
    n2 = bt.Sequence()
    n2_id = n2.generate_and_set_unique_id()

    tree.set_root(bt.Sequence(children=[bt.Sequence(), n2, bt.Sequence()]))

    self._executive.run(
        tree, start_node=bt.NodeIdentifierType(tree_id=tree_id, node_id=n2_id)
    )

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME
    )
    start_request.skill_trace_handling = (
        run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK
    )
    start_request.start_tree_id = tree_id
    start_request.start_node_id = n2_id
    self._executive_service_stub.StartOperation.assert_called_once_with(
        start_request
    )

  def test_operation_done(self):
    """Tests if executive.operation.done works."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action)

    self.assertTrue(self._executive.operation.done)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.task.call_behavior.CopyFrom(
        my_action.proto
    )
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )
    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_run_sends_stepwise_mode(self):
    """Tests that executive.run(action, stepwise=True) sends expected mode."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action, step_wise=True)

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME,
        execution_mode=executive_execution_mode_pb2.EXECUTION_MODE_STEP_WISE,
        skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
    )
    self._executive_service_stub.StartOperation.assert_called_with(
        start_request
    )

  @parameterized.named_parameters(
      dict(
          testcase_name='DEFAULT',
          simulation_mode=None,
          simulation_proto_mode=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_UNSPECIFIED,
      ),
      dict(
          testcase_name='REALITY',
          simulation_mode=execution.Executive.SimulationMode.REALITY,
          simulation_proto_mode=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_REALITY,
      ),
      dict(
          testcase_name='DRAFT',
          simulation_mode=execution.Executive.SimulationMode.DRAFT,
          simulation_proto_mode=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_DRAFT,
      ),
  )
  def test_run_with_simulation_mode(
      self, simulation_mode, simulation_proto_mode
  ):
    """Tests if executive.run(action, simulation_mode=x) sets proper mode."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action, simulation_mode=simulation_mode)

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME,
        simulation_mode=simulation_proto_mode,
        skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
    )
    self._executive_service_stub.StartOperation.assert_called_with(
        start_request
    )

  @parameterized.named_parameters(
      dict(
          testcase_name='NORMAL',
          proto_enum=executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_NORMAL,
          expected_execution_mode=execution.Executive.ExecutionMode.NORMAL,
      ),
      dict(
          testcase_name='STEP_WISE',
          proto_enum=executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_STEP_WISE,
          expected_execution_mode=execution.Executive.ExecutionMode.STEP_WISE,
      ),
  )
  def test_execution_mode_property(self, proto_enum, expected_execution_mode):
    """Tests if executive.execution_mode property returns expected value."""
    self._create_operation()

    operation = self._create_operation_proto(
        behavior_tree_pb2.BehaviorTree.RUNNING
    )
    metadata = run_metadata_pb2.RunMetadata()
    operation.metadata.Unpack(metadata)
    metadata.execution_mode = proto_enum
    operation.metadata.Pack(metadata)

    self._executive_service_stub.GetOperation.return_value = operation

    self.assertEqual(self._executive.execution_mode, expected_execution_mode)

  @parameterized.named_parameters(
      dict(
          testcase_name='REALITY',
          proto_enum=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_REALITY,
          expected_simulation_mode=execution.Executive.SimulationMode.REALITY,
      ),
      dict(
          testcase_name='DRAFT',
          proto_enum=executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_DRAFT,
          expected_simulation_mode=execution.Executive.SimulationMode.DRAFT,
      ),
  )
  def test_simulation_mode_property(self, proto_enum, expected_simulation_mode):
    """Tests if executive.simulation_mode property returns expected value."""
    self._create_operation()

    operation = self._create_operation_proto(
        behavior_tree_pb2.BehaviorTree.RUNNING
    )
    metadata = run_metadata_pb2.RunMetadata()
    operation.metadata.Unpack(metadata)
    metadata.simulation_mode = proto_enum
    operation.metadata.Pack(metadata)

    self._executive_service_stub.GetOperation.return_value = operation

    self.assertEqual(self._executive.simulation_mode, expected_simulation_mode)

  def test_run_works_nested_list(self):
    """Tests if executive.run(action) waits for success.

    Tests with a nested list of actions as request.
    """

    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action_list = [
        behavior_call.Action(skill_id='action_1'),
        [
            behavior_call.Action(skill_id='action_21'),
            behavior_call.Action(skill_id='action_22'),
        ],
    ]
    self._executive.run(my_action_list)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.sequence.children.append(
        behavior_tree_pb2.BehaviorTree.Node(
            task=behavior_tree_pb2.BehaviorTree.TaskNode(
                call_behavior=my_action_list[0].proto
            )
        )
    )
    create_request.behavior_tree.root.sequence.children.append(
        behavior_tree_pb2.BehaviorTree.Node(
            task=behavior_tree_pb2.BehaviorTree.TaskNode(
                call_behavior=my_action_list[1][0].proto
            )
        )
    )
    create_request.behavior_tree.root.sequence.children.append(
        behavior_tree_pb2.BehaviorTree.Node(
            task=behavior_tree_pb2.BehaviorTree.TaskNode(
                call_behavior=my_action_list[1][1].proto
            )
        )
    )
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME,
        skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
    )
    self._executive_service_stub.StartOperation.assert_called_with(
        start_request
    )

  def test_run_works_behavior_tree(self):
    """Tests if executive.run(behavior_tree) waits for success.

    Tests with a BehaviorTree instance.
    """
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    bt_instance = bt.BehaviorTree('test_bt')
    bt_instance.set_root(
        bt.Sequence().set_children(
            bt.Task(behavior_call.Action(skill_id='action_1'))
        )
    )
    self._executive.run(bt_instance)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.CopyFrom(bt_instance.proto)
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME,
        skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
    )
    self._executive_service_stub.StartOperation.assert_called_with(
        start_request
    )

  def test_run_works_on_behavior_tree_node(self):
    """Tests if executive.run(node) calls create."""
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_node = bt.Fail()
    self._executive.run(my_node)

    create_request = executive_service_pb2.CreateOperationRequest()
    create_request.behavior_tree.root.CopyFrom(my_node.proto)
    self._executive_service_stub.CreateOperation.assert_called_once_with(
        create_request
    )

    start_request = executive_service_pb2.StartOperationRequest(
        name=_OPERATION_NAME,
        skill_trace_handling=run_metadata_pb2.RunMetadata.TracingInfo.SKILL_TRACES_LINK,
    )
    self._executive_service_stub.StartOperation.assert_called_with(
        start_request
    )

  def test_run_resets_simulation(self):
    """Tests if executive.run(action) resets the simulation.

    Case 1: ... if no operation exists (locally or in executive)
    """
    self._setup_create_operation()
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action)

    self._simulation.reset.assert_called_once()

  def test_run_does_not_reset_simulation(self):
    """Tests if executive.run(action) does not reset the simulation.

    Case 2: ... if operation exists in executive
    """
    response = operations_pb2.ListOperationsResponse()
    response.operations.append(
        self._create_operation_proto(behavior_tree_pb2.BehaviorTree.SUCCEEDED)
    )
    self._executive_service_stub.ListOperations.return_value = response

    self._setup_create_operation(setup_empty_list_operations=False)
    self._setup_start_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    my_action = behavior_call.Action(skill_id='my_action')
    self._executive.run(my_action)

    self._simulation.reset.assert_not_called()

  def test_errors_printed(self):
    """Tests if executive.run(action) prints errors correctly."""
    self._setup_create_operation()
    self._setup_start_operation()

    def create_operation(state, errors_reports=None):
      operation = self._create_operation_proto(state)
      if errors_reports:
        details_any = operation.error.details.add()
        details_any.Pack(
            error_report_pb2.ErrorReports(error_reports=errors_reports)
        )
      return operation

    error_report = text_format.Parse(
        """
        description {
          status: {
            code: 7
            message: "some message"
          }
          human_readable_summary: "some text"
        }""",
        error_report_pb2.ErrorReport(),
    )

    self._executive_service_stub.GetOperation.side_effect = [
        create_operation(behavior_tree_pb2.BehaviorTree.RUNNING),
        create_operation(behavior_tree_pb2.BehaviorTree.FAILED, [error_report]),
        create_operation(behavior_tree_pb2.BehaviorTree.FAILED, [error_report]),
        # extra call in error case as get_errors also accesses self.operation
        create_operation(behavior_tree_pb2.BehaviorTree.FAILED, [error_report]),
    ]

    my_action = behavior_call.Action(skill_id='my_action')
    with self.assertRaisesRegex(execution.ExecutionFailedError, 'some text'):
      self._executive.run(my_action)

  @parameterized.product(
      start_state=[
          behavior_tree_pb2.BehaviorTree.ACCEPTED,
          behavior_tree_pb2.BehaviorTree.RUNNING,
          behavior_tree_pb2.BehaviorTree.SUSPENDING,
          behavior_tree_pb2.BehaviorTree.SUSPENDED,
          behavior_tree_pb2.BehaviorTree.CANCELING,
      ],
      end_state=[
          behavior_tree_pb2.BehaviorTree.CANCELED,
          behavior_tree_pb2.BehaviorTree.FAILED,
          behavior_tree_pb2.BehaviorTree.SUCCEEDED,
      ],
  )
  def test_cancel_calls_stub_and_waits_for_valid_state(
      self, start_state, end_state
  ):
    self._create_operation()
    self._setup_get_operation_sequence([start_state, end_state])

    self._executive.cancel()
    self._executive_service_stub.CancelOperation.assert_called_with(
        operations_pb2.CancelOperationRequest(name=_OPERATION_NAME)
    )
    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_cancel_async_works(self):
    """Tests if executive.cancel_async() calls cancel."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.RUNNING)
    self._executive.cancel_async()
    self._executive_service_stub.CancelOperation.assert_called_with(
        operations_pb2.CancelOperationRequest(name=_OPERATION_NAME)
    )

  def test_suspend_works(self):
    """Tests if executive.suspend_async() calls suspends and waits until executive state changes to suspended."""

    self._create_operation()

    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.SUSPENDED,
    ])

    self._executive.suspend()

    self._executive_service_stub.SuspendOperation.assert_called_with(
        executive_service_pb2.SuspendOperationRequest(name=_OPERATION_NAME)
    )
    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_suspend_async_works(self):
    """Tests if executive.suspend_async() calls suspends and waits until executive state changes to suspended."""
    self._create_operation()

    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.SUSPENDING,
        behavior_tree_pb2.BehaviorTree.SUSPENDED,
    ])

    self._executive.suspend_async()

    self._executive_service_stub.SuspendOperation.assert_called_with(
        executive_service_pb2.SuspendOperationRequest(name=_OPERATION_NAME)
    )

  def test_suspend_fails_on_unavailable_error(self):
    """Tests if executive.suspend() translates UNAVAILABLE error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.RUNNING)

    self._executive_service_stub.SuspendOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNAVAILABLE
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.suspend()

    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)

    for _ in range(6):  # Will retry 5 times.
      self._executive_service_stub.SuspendOperation.assert_called_with(
          executive_service_pb2.SuspendOperationRequest(name=_OPERATION_NAME)
      )

  def test_suspend_fails_on_invalid_argument_error(self):
    """Tests if executive.suspend() translates INVALID_ARGUMENT error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.RUNNING)

    self._executive_service_stub.SuspendOperation.side_effect = _GrpcError(
        grpc.StatusCode.INVALID_ARGUMENT
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.suspend()

    self.assertEqual(context.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

    self._executive_service_stub.SuspendOperation.assert_called_once_with(
        executive_service_pb2.SuspendOperationRequest(name=_OPERATION_NAME)
    )

  def test_suspend_fails_on_grpc_error(self):
    """Tests if executive.suspend() forwards other grpc errors correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.RUNNING)

    self._executive_service_stub.SuspendOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNKNOWN
    )

    with self.assertRaises(_GrpcError):
      self._executive.suspend()

    self._executive_service_stub.SuspendOperation.assert_called_once_with(
        executive_service_pb2.SuspendOperationRequest(name=_OPERATION_NAME)
    )

  def test_resume_works(self):
    """Tests if executive.resume() calls resume of the executive service."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUSPENDED)

    self._executive_service_stub.ResumeOperation.return_value = (
        self._create_operation_proto(behavior_tree_pb2.BehaviorTree.RUNNING)
    )

    self._executive.resume()

    self._executive_service_stub.ResumeOperation.assert_called_once_with(
        executive_service_pb2.ResumeOperationRequest(name=_OPERATION_NAME)
    )

  def test_resume_fails_on_unavailable_error(self):
    """Tests if executive.resume() translates UNAVAILABLE error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUSPENDED)

    self._executive_service_stub.ResumeOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNAVAILABLE
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.resume()
    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)

    for _ in range(6):  # Will retry 5 times.
      self._executive_service_stub.ResumeOperation.assert_called_with(
          executive_service_pb2.ResumeOperationRequest(name=_OPERATION_NAME)
      )

  def test_resume_fails_on_invalid_argument_error(self):
    """Tests if executive.resume() translates INVALID_ARGUMENT error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUSPENDED)

    self._executive_service_stub.ResumeOperation.side_effect = _GrpcError(
        grpc.StatusCode.INVALID_ARGUMENT
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.resume()
    self.assertEqual(context.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
    self._executive_service_stub.ResumeOperation.assert_called_once_with(
        executive_service_pb2.ResumeOperationRequest(name=_OPERATION_NAME)
    )

  def test_resume_fails_on_grpc_error(self):
    """Tests if executive.resume() forwards other grpc errors correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUSPENDED)

    self._executive_service_stub.ResumeOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNKNOWN
    )

    with self.assertRaises(_GrpcError):
      self._executive.resume()
    self._executive_service_stub.ResumeOperation.assert_called_once_with(
        executive_service_pb2.ResumeOperationRequest(name=_OPERATION_NAME)
    )

  def test_reset_works(self):
    """Tests if executive.reset() calls Reset of the executive service."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUCCEEDED)

    self._executive.reset()

    self._executive_service_stub.ResetOperation.assert_called_once_with(
        executive_service_pb2.ResetOperationRequest(name=_OPERATION_NAME)
    )

  def test_reset_fails_on_unavailable_error(self):
    """Tests if executive.reset() translates UNAVAILABLE error correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUCCEEDED)

    self._executive_service_stub.ResetOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNAVAILABLE
    )

    with self.assertRaises(_GrpcError) as context:
      self._executive.reset()

    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)
    for _ in range(6):  # Will retry 5 times.
      self._executive_service_stub.ResetOperation.assert_called_with(
          executive_service_pb2.ResetOperationRequest(name=_OPERATION_NAME)
      )

  def test_reset_fails_on_grpc_error(self):
    """Tests if executive.reset() forwards other grpc errors correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUCCEEDED)

    self._executive_service_stub.ResetOperation.side_effect = _GrpcError(
        grpc.StatusCode.UNKNOWN
    )

    with self.assertRaises(_GrpcError):
      self._executive.reset()
    self._executive_service_stub.ResetOperation.assert_called_once_with(
        executive_service_pb2.ResetOperationRequest(name=_OPERATION_NAME)
    )

  def test_block_until_completed_works(self):
    """Tests if executive.block_until_completed(action) waits for success."""

    self._create_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    self._executive.block_until_completed()

    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_block_until_completed_works_when_suspended(self):
    """Tests if executive.block_until_completed(action) waits for success."""

    self._create_operation()
    self._setup_get_operation_sequence([
        behavior_tree_pb2.BehaviorTree.SUSPENDED,
        behavior_tree_pb2.BehaviorTree.RUNNING,
        behavior_tree_pb2.BehaviorTree.SUCCEEDED,
    ])

    self._executive.block_until_completed()

    self._executive_service_stub.GetOperation.assert_called_with(
        operations_pb2.GetOperationRequest(name=_OPERATION_NAME)
    )

  def test_block_until_completed_raises_exception_on_run_error(self):
    """Tests if executive.block_until_completed() raises an exception if execution fails."""

    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.FAILED)

    with self.assertRaises(execution.ExecutionFailedError):
      self._executive.block_until_completed()

  @parameterized.named_parameters(
      dict(
          testcase_name='CONTINUE',
          resume_mode=execution.Executive.ResumeMode.CONTINUE,
          expected_proto_enum=executive_service_pb2.ResumeOperationRequest.CONTINUE,
      ),
      dict(
          testcase_name='STEP',
          resume_mode=execution.Executive.ResumeMode.STEP,
          expected_proto_enum=executive_service_pb2.ResumeOperationRequest.STEP,
      ),
      dict(
          testcase_name='NEXT',
          resume_mode=execution.Executive.ResumeMode.NEXT,
          expected_proto_enum=executive_service_pb2.ResumeOperationRequest.NEXT,
      ),
  )
  def test_resume_parameterization_works(
      self, resume_mode, expected_proto_enum
  ):
    """Tests if executive.resume(resume_mode) calls resume method correctly."""
    self._create_operation()
    self._setup_get_operation(behavior_tree_pb2.BehaviorTree.SUSPENDED)

    self._executive_service_stub.ResumeOperation.return_value = (
        self._create_operation_proto()
    )

    self._executive.resume(mode=resume_mode)
    self._executive_service_stub.ResumeOperation.assert_called_once_with(
        executive_service_pb2.ResumeOperationRequest(
            name=_OPERATION_NAME, mode=expected_proto_enum
        )
    )


class ResumeModeTest(absltest.TestCase):
  """Tests that proto values are correctly converted."""

  def test_from_proto(self):
    none_value = execution.Executive.ResumeMode.from_proto(None)
    self.assertIsNone(none_value)

    unspecified_value = execution.Executive.ResumeMode.from_proto(
        executive_service_pb2.ResumeOperationRequest.RESUME_MODE_UNSPECIFIED
    )
    self.assertIsNone(unspecified_value)

    continue_value = execution.Executive.ResumeMode.from_proto(
        executive_service_pb2.ResumeOperationRequest.CONTINUE
    )
    self.assertEqual(continue_value, execution.Executive.ResumeMode.CONTINUE)

    step_value = execution.Executive.ResumeMode.from_proto(
        executive_service_pb2.ResumeOperationRequest.STEP
    )
    self.assertEqual(step_value, execution.Executive.ResumeMode.STEP)

    next_value = execution.Executive.ResumeMode.from_proto(
        executive_service_pb2.ResumeOperationRequest.NEXT
    )
    self.assertEqual(next_value, execution.Executive.ResumeMode.NEXT)


class SimulationModeTest(absltest.TestCase):
  """Tests that proto values are correctly converted."""

  def test_from_proto(self):
    none_value = execution.Executive.SimulationMode.from_proto(None)
    self.assertIsNone(none_value)

    unspecified_value = execution.Executive.SimulationMode.from_proto(
        executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_UNSPECIFIED
    )
    self.assertIsNone(unspecified_value)

    reality_value = execution.Executive.SimulationMode.from_proto(
        executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_REALITY
    )
    self.assertEqual(
        reality_value,
        execution.Executive.SimulationMode.REALITY,
    )

    draft_value = execution.Executive.SimulationMode.from_proto(
        executive_execution_mode_pb2.SimulationMode.SIMULATION_MODE_DRAFT
    )
    self.assertEqual(draft_value, execution.Executive.SimulationMode.DRAFT)


class ExecutionModeTest(absltest.TestCase):
  """Tests that proto values are correctly converted."""

  def test_from_proto(self):
    none_value = execution.Executive.ExecutionMode.from_proto(None)
    self.assertIsNone(none_value)

    unspecified_value = execution.Executive.ExecutionMode.from_proto(
        executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_UNSPECIFIED
    )
    self.assertIsNone(unspecified_value)

    normal_value = execution.Executive.ExecutionMode.from_proto(
        executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_NORMAL
    )
    self.assertEqual(
        normal_value,
        execution.Executive.ExecutionMode.NORMAL,
    )

    stepwise_value = execution.Executive.ExecutionMode.from_proto(
        executive_execution_mode_pb2.ExecutionMode.EXECUTION_MODE_STEP_WISE
    )
    self.assertEqual(
        stepwise_value, execution.Executive.ExecutionMode.STEP_WISE
    )


if __name__ == '__main__':
  absltest.main()
