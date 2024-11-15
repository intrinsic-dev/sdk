# Copyright 2023 Intrinsic Innovation LLC

"""Tests for motion planner client."""

from unittest import mock

from absl.testing import absltest
from google.protobuf import empty_pb2
from intrinsic.motion_planning.proto import motion_planner_service_pb2_grpc
from intrinsic.solutions import motion_planning

_WORLD_ID = "world"


class MotionPlannerClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.stub = mock.create_autospec(
        motion_planner_service_pb2_grpc.MotionPlannerServiceStub,
        instance=True,
    )
    self.stub.ClearCache = mock.MagicMock()
    self.motion_planner_client = motion_planning.MotionPlannerClient(
        _WORLD_ID, self.stub
    )

  def test_for_solution(self):
    channel = mock.MagicMock()
    solution = mock.MagicMock()
    solution.world.world_id = _WORLD_ID
    solution.grpc_channel = channel
    mpc = motion_planning.MotionPlannerClient.for_solution(solution)
    self.assertIsInstance(mpc, motion_planning.MotionPlannerClient)

  def test_exposed_methods(self):
    expected_methods = [
        "clear_cache",
        "for_solution",
    ]
    for method in dir(motion_planning.MotionPlannerClient):
      if not method.startswith("_"):
        self.assertIn(method, expected_methods)

  def test_clear_cache(self):
    self.stub.ClearCache.return_value = empty_pb2.Empty()
    self.motion_planner_client.clear_cache()
    self.stub.ClearCache.assert_called_once_with(empty_pb2.Empty())


if __name__ == "__main__":
  absltest.main()
