# Copyright 2023 Intrinsic Innovation LLC

"""Tests for simulation_smoke."""

from unittest import mock

from absl.testing import absltest
from google.protobuf import empty_pb2
from intrinsic.simulation.service.proto import simulation_service_pb2
from intrinsic.solutions import simulation as simulation_mod


class SimulationTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.simulation_service_stub = mock.MagicMock()
    self.object_world_service_stub = mock.MagicMock()
    self.simulation = simulation_mod.Simulation(
        self.simulation_service_stub, self.object_world_service_stub
    )

  def test_reset(self):
    self.simulation_service_stub.ResetSimulation.return_value = (
        empty_pb2.Empty()
    )

    self.simulation.reset()

    self.simulation_service_stub.ResetSimulation.assert_called_once_with(
        simulation_service_pb2.ResetSimulationRequest()
    )

  def test_get_realtime_factor(self):
    self.simulation_service_stub.GetRealtimeFactor.return_value = 2

    result = self.simulation.get_realtime_factor()

    self.simulation_service_stub.GetRealtimeFactor.assert_called_once_with(
        empty_pb2.Empty()
    )
    self.assertEqual(result, 2)


if __name__ == '__main__':
  absltest.main()
