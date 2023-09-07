# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Helper module to construct a Stop action."""

from intrinsic.icon.python import actions

ACTION_TYPE_NAME = "xfa.stop"


def CreateStopAction(
    action_id: int, joint_position_part_name: str
) -> actions.Action:
  """Creates a Stop action.

  Args:
    action_id: The ID of the action.
    joint_position_part_name:  The name of the part providing the JointPosition
      interface.

  Returns:
    The Stop action.
  """
  return actions.Action(
      action_id, ACTION_TYPE_NAME, joint_position_part_name, None
  )
