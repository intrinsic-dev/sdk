# Copyright 2023 Intrinsic Innovation LLC

"""Helper module to construct actions.

This module only should redirect Create functions to other modules to make the
usage in the external API easier.
"""

from intrinsic.icon.actions import point_to_point_move_utils
from intrinsic.icon.actions import stop_utils
from intrinsic.icon.actions import tare_force_torque_sensor_utils
from intrinsic.icon.actions import trajectory_tracking_action_utils
from intrinsic.icon.actions import wait_for_settling_utils

CreateTrajectoryTrackingAction = (
    trajectory_tracking_action_utils.CreateTrajectoryTrackingAction
)

CreateTareForceTorqueSensorAction = (
    tare_force_torque_sensor_utils.CreateTareForceTorqueSensorAction
)

CreatePointToPointMoveAction = (
    point_to_point_move_utils.CreatePointToPointMoveAction
)

CreateStopAction = stop_utils.CreateStopAction

CreateWaitForSettlingAction = (
    wait_for_settling_utils.CreateWaitForSettlingAction
)
