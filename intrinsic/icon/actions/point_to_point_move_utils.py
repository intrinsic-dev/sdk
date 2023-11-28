# Copyright 2023 Intrinsic Innovation LLC

"""Helper module to construct a PointToPointMoveAction."""

from typing import Optional, Sequence
from intrinsic.icon.actions import point_to_point_move_pb2
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.icon.python import actions
from intrinsic.kinematics.types import joint_limits_pb2

ACTION_TYPE_NAME = "xfa.point_to_point_move"


def create_point_to_point_move_action(
    action_id: int,
    joint_position_part_name: str,
    goal_position: Sequence[float],
    goal_velocity: Optional[Sequence[float]] = None,
    joint_limits: Optional[joint_limits_pb2.JointLimits] = None,
) -> actions.Action:
  """Creates a PointToPointMove action.

  Generates and executes a jerk-limited time-optimal trajectory to move the
  part's joints to the desired target position. Uses Reflexxes for instantaneous
  real-time motion generation. For motions with zero initial and target joint
  velocity, or co-linear initial and final velocity, the resulting trajectory
  will typically be linear in joint-space. Otherwise, there are no guarantees on
  the geometric shape of the joint move. Online trajectory execution will slow
  down/speed up according to the speed override factor in a differentially
  consistent and time-optimal way. This action also holds a settling state
  estimator which monitors residual oscillations or tracking error transients
  after the trajectory has been played back. See state variable documentation of
  `xfa.is_settled` for details.

  Args:
    action_id: The ID of the action.
    joint_position_part_name:  The name of the part providing the JointPosition
      interface.
    goal_position: The position to move to.
    goal_velocity: The desired velocity when the goal position is reached. Set
      to the zero vector to stop at the goal position. Defaults to zero.
    joint_limits:  The joint limits to apply to the motion. The actual limits
      used will be the most conservative of (i) Physical hardware limits, (ii)
      limits configured on the ICON server; and (iii) these optional
      action-specific limits.

  Returns:
    The PointToPointMove action.
  """
  params = point_to_point_move_pb2.PointToPointMoveFixedParams(
      goal_position=joint_space_pb2.JointVec(joints=goal_position)
  )
  if goal_velocity is not None:
    params.goal_velocity.joints.extend(goal_velocity)
  else:
    params.goal_velocity.joints.extend([0.0] * len(goal_position))
  if joint_limits is not None:
    params.joint_limits.CopyFrom(joint_limits)

  return actions.Action(
      action_id, ACTION_TYPE_NAME, joint_position_part_name, params
  )
