# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from intrinsic.icon.actions import tare_force_torque_sensor_pb2
from intrinsic.icon.actions import tare_force_torque_sensor_utils


class TareForceTorqueSensorUtilsTest(absltest.TestCase):

  def test_create_action(self):
    action = (
        tare_force_torque_sensor_utils.create_tare_force_torque_sensor_action(
            35, "sensor_part", 13
        )
    )

    self.assertEqual(action.proto.action_instance_id, 35)
    self.assertEqual(action.proto.part_name, "sensor_part")
    self.assertEmpty(action.reactions)
    self.assertEqual(
        action.proto.action_type_name, "xfa.tare_force_torque_sensor"
    )

    got_params = tare_force_torque_sensor_pb2.TareForceTorqueSensorParams()
    self.assertTrue(action.proto.fixed_parameters.Unpack(got_params))
    self.assertEqual(got_params.num_taring_cycles, 13)

  def test_create_action_with_default(self):
    action = (
        tare_force_torque_sensor_utils.create_tare_force_torque_sensor_action(
            35, "sensor_part"
        )
    )

    self.assertEqual(action.proto.action_instance_id, 35)
    self.assertEqual(action.proto.part_name, "sensor_part")
    self.assertEmpty(action.reactions)
    self.assertEqual(
        action.proto.action_type_name, "xfa.tare_force_torque_sensor"
    )

    got_params = tare_force_torque_sensor_pb2.TareForceTorqueSensorParams()
    self.assertTrue(action.proto.fixed_parameters.Unpack(got_params))
    self.assertFalse(got_params.HasField("num_taring_cycles"))


if __name__ == "__main__":
  absltest.main()
