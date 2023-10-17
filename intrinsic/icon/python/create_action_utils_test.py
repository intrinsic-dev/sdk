# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from google.protobuf import duration_pb2
from intrinsic.icon.actions import point_to_point_move_utils
from intrinsic.icon.actions import stop_utils
from intrinsic.icon.actions import tare_force_torque_sensor_utils
from intrinsic.icon.actions import trajectory_tracking_action_utils
from intrinsic.icon.actions import wait_for_settling_utils
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.icon.python import create_action_utils
import numpy as np


class ActionUtilsTest(absltest.TestCase):

  def test_create_trajectory_tracking_action(self):
    action = create_action_utils.CreateTrajectoryTrackingAction(
        1,
        "my_part",
        joint_space_pb2.JointTrajectoryPVA(
            state=[
                joint_space_pb2.JointStatePVA(
                    position=[0.0, 0.0],
                    velocity=[0.0, 0.0],
                    acceleration=[0.0, 0.0],
                )
            ],
            time_since_start=[duration_pb2.Duration(seconds=2, nanos=14)],
        ),
    )

    self.assertEqual(
        action.proto.action_type_name,
        trajectory_tracking_action_utils.ACTION_TYPE_NAME,
    )

  def test_create_tare_force_torque_sensor_action(self):
    action = create_action_utils.CreateTareForceTorqueSensorAction(2, "my_part")

    self.assertEqual(
        action.proto.action_type_name,
        tare_force_torque_sensor_utils.ACTION_TYPE_NAME,
    )

  def test_create_point_to_point_move(self):
    action = create_action_utils.CreatePointToPointMoveAction(
        5, "my_part", [1.2, 2.3]
    )

    self.assertEqual(
        action.proto.action_type_name,
        point_to_point_move_utils.ACTION_TYPE_NAME,
    )

  def test_create_stop(self):
    action = create_action_utils.CreateStopAction(4, "my_part")

    self.assertEqual(
        action.proto.action_type_name,
        stop_utils.ACTION_TYPE_NAME,
    )

  def test_create_wait_for_settling(self):
    action = create_action_utils.CreateWaitForSettlingAction(4, "my_part")

    self.assertEqual(
        action.proto.action_type_name,
        wait_for_settling_utils.ACTION_TYPE_NAME,
    )


if __name__ == "__main__":
  absltest.main()
