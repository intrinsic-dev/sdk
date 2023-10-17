# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from google.protobuf import any_pb2
from intrinsic.icon.actions import stop_utils


class StopUtilsTest(absltest.TestCase):

  def test_create_action(self):
    action = stop_utils.CreateStopAction(
        action_id=17, joint_position_part_name="my_part"
    )

    self.assertEqual(action.proto.action_instance_id, 17)
    self.assertEqual(action.proto.part_name, "my_part")
    self.assertEmpty(action.reactions)
    self.assertEqual(action.proto.action_type_name, "xfa.stop")
    self.assertEqual(action.proto.fixed_parameters, any_pb2.Any())

  def test_is_setteld_variable_name_is_correct(self):
    self.assertEqual(stop_utils.StateVariables.IS_SETTLED, "is_settled")


if __name__ == "__main__":
  absltest.main()
