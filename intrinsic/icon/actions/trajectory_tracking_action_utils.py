# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Helper module to construct a TrajectoryTrackingAction."""

from intrinsic.icon.actions import trajectory_tracking_action_pb2
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.icon.python import actions

ACTION_TYPE_NAME: str = 'xfa.trajectory_tracking'


# If the initial robot position deviates more from the first trajectory position
# than this threshold, the Action will return FailedPrecondition.
MAX_INITIAL_JOINT_POSITION_DEVIATION: float = 0.1  # [rad]

# If the initial robot position deviates more from the first trajectory position
# than this threshold, the Action will return FailedPrecondition.
MAX_INITIAL_JOINT_VELOCITY_DEVIATION: float = 0.15  # [rad/sec]


def CreateTrajectoryTrackingAction(
    action_id: int,
    part: str,
    trajectory: joint_space_pb2.JointTrajectoryPVA,
) -> actions.Action:
  """Creates a TrajectoryTrackingAction.

  Follows a given JointTrajectoryPVA and uses quintic splining to interpolate
  between the discretized states. The previously commanded robot
  position/velocity setpoint must be within
  `MAX_INITIAL_JOINT_POSITION_DEVIATION` and
  `MAX_INITIAL_JOINT_VELOCITY_DEVIATION` of the first joint state of the
  command. A residual controller is applied to compensate for initial state
  deviations smaller than above thresholds.

  Args:
    action_id: The ID of the action.
    part: The part has to provide a JointPosition interface.
    trajectory: Joint trajectory the robot should follow. the number of joints
      has to match the robot.

  Returns:
    The TrajectoryTrackingAction.
  """
  return actions.Action(
      action_id,
      ACTION_TYPE_NAME,
      part,
      trajectory_tracking_action_pb2.TrajectoryTrackingActionFixedParams(
          trajectory=trajectory
      ),
  )
