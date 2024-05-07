# Copyright 2023 Intrinsic Innovation LLC

"""Tests for deployments."""

import io
from unittest import mock

from absl.testing import absltest
from google.protobuf import empty_pb2
import grpc
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.solutions import auth
from intrinsic.solutions import deployments
from intrinsic.solutions import dialerutil
from intrinsic.solutions import error_processing
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import execution
from intrinsic.solutions import simulation as simulation_mod
from intrinsic.solutions import userconfig
from intrinsic.solutions import worlds


class DeploymentsTest(absltest.TestCase):
  """Tests public methods of the deployments module."""

  def test_connect_raises_if_all_params_set(
      self,
  ):
    with self.assertRaisesRegex(ValueError, "Only one .*"):
      deployments.connect(
          grpc_channel_or_hostport="localhost:1234",
          address="localhost:1234",
          org="test-org",
          solution="test-solution",
      )

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  def test_connect_defaults_to_localhost(
      self,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_create_channel.return_value = None
    mock_for_channel.return_value = None
    deployments.connect()
    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(address=deployments._DEFAULT_HOSTPORT),
        grpc_options=deployments._GRPC_OPTIONS,
    )
    self.assertTrue(mock_for_channel.called)

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  def test_connect_grpc_channel_or_hostport_with_hostport(
      self,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_create_channel.return_value = None
    mock_for_channel.return_value = None
    deployments.connect(grpc_channel_or_hostport="localhost:1234")
    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(address="localhost:1234"),
        grpc_options=deployments._GRPC_OPTIONS,
    )
    self.assertTrue(mock_for_channel.called)

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  def test_connect_grpc_channel_or_hostport_with_channel(
      self,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_create_channel.return_value = None
    mock_for_channel.return_value = None
    channel = grpc.insecure_channel("localhost:1234")
    deployments.connect(
        grpc_channel_or_hostport=channel,
    )
    mock_create_channel.assert_not_called()
    mock_for_channel.assert_called_with(channel, options=None)

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  def test_connect_grpc_channel(
      self,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_create_channel.return_value = None
    mock_for_channel.return_value = None

    channel = grpc.insecure_channel("localhost:1234")
    deployments.connect(
        grpc_channel=channel,
    )
    mock_create_channel.assert_not_called()
    mock_for_channel.assert_called_with(channel, options=None)

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  def test_connect_address(
      self,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_create_channel.return_value = None
    mock_for_channel.return_value = None
    deployments.connect(
        address="localhost:1234",
    )
    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(address="localhost:1234"),
        grpc_options=deployments._GRPC_OPTIONS,
    )
    self.assertTrue(mock_for_channel.called)

  def test_connect_raises_on_invalid_params(self):
    with self.assertRaisesRegex(ValueError, "org.*solution.*required together"):
      deployments.connect(org="test-org")

    with self.assertRaisesRegex(ValueError, "org.*solution.*required together"):
      deployments.connect(solution="test-solution")

  @mock.patch.object(deployments.Solution, "for_channel")
  @mock.patch.object(dialerutil, "create_channel")
  @mock.patch.object(deployments, "_get_cluster_from_solution")
  @mock.patch.object(auth, "read_org_info")
  def test_connect_org_and_solution(
      self,
      mock_read_org_info: mock.MagicMock,
      mock_get_cluster_from_solution: mock.MagicMock,
      mock_create_channel: mock.MagicMock,
      mock_for_channel: mock.MagicMock,
  ):
    mock_read_org_info.return_value = auth.OrgInfo(
        organization="test-org", project="test-project"
    )
    mock_get_cluster_from_solution.return_value = "test-cluster"
    mock_create_channel.return_value = grpc.insecure_channel("localhost:1234")
    mock_for_channel.return_value = None

    deployments.connect(org="test-org", solution="test-solution")

    mock_read_org_info.assert_called_with("test-org")
    mock_get_cluster_from_solution.assert_called_with(
        "test-project", "test-solution"
    )
    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(
            organization_name="test-org",
            project_name="test-project",
            cluster="test-cluster",
        ),
        grpc_options=deployments._GRPC_OPTIONS,
    )
    self.assertTrue(mock_for_channel.called)

  @mock.patch.object(userconfig, "read")
  def test_deployments_connect_to_selected_solution_fails(
      self,
      mock_userconfig_read: mock.MagicMock,
  ):
    mock_userconfig_read.return_value = {}
    with self.assertRaisesRegex(
        solutions_errors.NotFoundError, "solution selection"
    ):
      deployments.connect_to_selected_solution()

    mock_userconfig_read.return_value = {
        userconfig.SELECTED_SOLUTION_TYPE: (
            userconfig.SELECTED_SOLUTION_TYPE_REMOTE
        )
    }
    with self.assertRaisesRegex(
        solutions_errors.NotFoundError, "solution selection.*No project"
    ):
      deployments.connect_to_selected_solution()

    mock_userconfig_read.return_value = {
        userconfig.SELECTED_SOLUTION_TYPE: (
            userconfig.SELECTED_SOLUTION_TYPE_REMOTE
        ),
        userconfig.SELECTED_PROJECT: "test-project",
    }
    with self.assertRaisesRegex(
        solutions_errors.NotFoundError, "solution selection.*No solution"
    ):
      deployments.connect_to_selected_solution()

  @mock.patch.object(userconfig, "read")
  @mock.patch.object(dialerutil, "create_channel")
  @mock.patch.object(deployments.Solution, "for_channel")
  def test_deployments_connect_to_selected_solution_local_case(
      self,
      mock_for_channel: mock.MagicMock,
      mock_create_channel: mock.MagicMock,
      mock_userconfig_read: mock.MagicMock,
  ):
    mock_userconfig_read.return_value = {
        userconfig.SELECTED_SOLUTION_TYPE: (
            userconfig.SELECTED_SOLUTION_TYPE_LOCAL
        )
    }
    mock_for_channel.return_value = None

    deployments.connect_to_selected_solution()

    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(address=deployments._DEFAULT_HOSTPORT),
        grpc_options=deployments._GRPC_OPTIONS,
    )

  @mock.patch.object(userconfig, "read")
  @mock.patch.object(deployments, "_get_cluster_from_solution")
  @mock.patch.object(dialerutil, "create_channel")
  @mock.patch.object(deployments.Solution, "for_channel")
  def test_deployments_connect_to_selected_solution_remote_case(
      self,
      mock_for_channel: mock.MagicMock,
      mock_create_channel: mock.MagicMock,
      mock_get_cluster_from_solution: mock.MagicMock,
      mock_userconfig_read: mock.MagicMock,
  ):
    mock_userconfig_read.return_value = {
        "selectedProject": "test-project",
        "selectedSolution": "test-solution",
    }
    mock_get_cluster_from_solution.return_value = "test-cluster"
    mock_create_channel.return_value = grpc.insecure_channel("localhost:1234")
    mock_for_channel.return_value = None

    deployments.connect_to_selected_solution()

    mock_get_cluster_from_solution.assert_called_with(
        "test-project", "test-solution"
    )
    mock_create_channel.assert_called_with(
        dialerutil.CreateChannelParams(
            project_name="test-project", cluster="test-cluster"
        ),
        grpc_options=deployments._GRPC_OPTIONS,
    )

  def test_get_solution_status_with_retry_raises(self):
    class FakeGrpcError(grpc.RpcError):
      """Simple sub-class to create RpcError with specific error code."""

      def __init__(self, code: grpc.StatusCode):
        self._code = code
        super().__init__("An error occurred")

      def code(self) -> grpc.StatusCode:
        return self._code

    mock_stub = mock.MagicMock()
    mock_stub.GetInstalledSpec.side_effect = FakeGrpcError(
        code=grpc.StatusCode.NOT_FOUND
    )

    with self.assertRaises(solutions_errors.BackendNoWorkcellError):
      deployments._get_solution_status_with_retry(mock_stub)


class SolutionTest(absltest.TestCase):
  """Tests public methods of the Solution wrapper class."""

  def setUp(self):
    super().setUp()

    self._mock_channel = mock.MagicMock()

    self._executive_stub = mock.MagicMock()

    self._installer_stub = mock.MagicMock()
    errors = error_processing.ErrorsLoader(self._installer_stub)

    self._object_world_service_stub = mock.MagicMock()
    object_world = worlds.ObjectWorld("world", self._object_world_service_stub)

    simulation_service_stub = mock.MagicMock()
    simulation = simulation_mod.Simulation(
        simulation_service_stub, self._object_world_service_stub
    )

    executive = execution.Executive(self._executive_stub, errors, simulation)

    self._skill_registry_stub = mock.MagicMock()
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().id = "ai.intrinsic.my_skill"
    self._skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        self._skill_registry_stub
    )

    resource_registry = mock.MagicMock()
    resource_registry.list_all_resource_handles.return_value = []

    pose_estimators = mock.MagicMock()

    self._executive = executive
    self._skill_registry = skill_registry
    self._resource_registry = resource_registry
    self._object_world = object_world
    self._simulation = simulation
    self._errors = errors
    self._pose_estimators = pose_estimators

  def init_solution(self) -> deployments.Solution:
    is_simulated = True
    return deployments.Solution(
        self._mock_channel,
        is_simulated,
        self._executive,
        self._skill_registry,
        self._resource_registry,
        self._object_world,
        self._simulation,
        self._errors,
        self._pose_estimators,
        self._installer_stub,
    )

  def test_initializes(self):
    """Tests if Workcell can be instantiated."""
    solution = self.init_solution()

    self.assertIsNotNone(solution.executive)
    self.assertIsNotNone(solution.skills)
    self.assertIsNotNone(solution.resources)
    self.assertIsNotNone(solution.simulator)
    self.assertIsInstance(solution.world, worlds.ObjectWorld)
    self.assertIsNotNone(solution.pose_estimators)

    skills = dir(solution.skills)
    self.assertIn("my_skill", skills)
    self._skill_registry_stub.GetSkills.assert_called_once_with(
        empty_pb2.Empty()
    )

  def test_health_query(self):
    """Tests that the health of the workcell backend can be queried."""
    solution = self.init_solution()

    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.HEALTHY
    )
    self._installer_stub.GetInstalledSpec.return_value = (
        installer_service_response
    )

    self.assertEqual(
        solution.get_health_status(), deployments.Solution.HealthStatus.HEALTHY
    )
    self._installer_stub.GetInstalledSpec.assert_called_once_with(
        empty_pb2.Empty()
    )

  def test_skills_overview(self):
    # First just the 'my_skill' already inserted
    mock_stdout = io.StringIO()
    solution = self.init_solution()
    with mock.patch("sys.stdout", mock_stdout):
      solution.skills_overview()
    self.assertEqual(mock_stdout.getvalue(), "ai.intrinsic.my_skill\n")

    # Add a 'z_move' skill with description
    skill_registry_response = self._skill_registry_stub.GetSkills.return_value
    z_move = skill_registry_response.skills.add()
    z_move.id = "ai.intrinsic.z_move"
    z_move.description = r"""DocFor z_move.

More z_move Doc."""
    solution = self.init_solution()

    # Test the ordering in the printout
    mock_stdout = io.StringIO()
    with mock.patch("sys.stdout", mock_stdout):
      solution.skills_overview()
    self.assertEqual(
        mock_stdout.getvalue(), "ai.intrinsic.my_skill\nai.intrinsic.z_move\n"
    )

    # Test docstring output
    mock_stdout = io.StringIO()
    with mock.patch("sys.stdout", mock_stdout):
      solution.skills_overview(with_doc=True)
    self.assertEqual(
        mock_stdout.getvalue(),
        r"""ai.intrinsic.my_skill

Skill class for ai.intrinsic.my_skill.

ai.intrinsic.z_move

Skill class for ai.intrinsic.z_move.

DocFor z_move.

More z_move Doc.

""",
    )


if __name__ == "__main__":
  absltest.main()
