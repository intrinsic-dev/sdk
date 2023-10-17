# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from intrinsic.icon.actions import wait_for_settling_action_pb2
from intrinsic.icon.actions import wait_for_settling_utils


class WaitForSettlingUtilsTest(absltest.TestCase):

  def test_create(self):
    action = wait_for_settling_utils.CreateWaitForSettlingAction(
        action_id=238, arm_part_name="my_arm_part", uncertainty_threshold=0.3
    )

    self.assertEqual(action.proto.action_instance_id, 238)
    self.assertEqual(action.proto.part_name, "my_arm_part")
    self.assertEqual(
        action.proto.action_type_name, "xfa.wait_for_settling_action"
    )

    got_params = wait_for_settling_action_pb2.WaitForSettlingActionFixedParams()
    self.assertTrue(action.proto.fixed_parameters.Unpack(got_params))
    self.assertEqual(got_params.uncertainty_threshold, 0.3)

  def test_create_default(self):
    action = wait_for_settling_utils.CreateWaitForSettlingAction(
        action_id=238, arm_part_name="my_arm_part"
    )

    self.assertEqual(action.proto.action_instance_id, 238)
    self.assertEqual(action.proto.part_name, "my_arm_part")
    self.assertEqual(
        action.proto.action_type_name, "xfa.wait_for_settling_action"
    )

    got_params = wait_for_settling_action_pb2.WaitForSettlingActionFixedParams()
    self.assertTrue(action.proto.fixed_parameters.Unpack(got_params))
    self.assertFalse(got_params.HasField("uncertainty_threshold"))


if __name__ == "__main__":
  absltest.main()
