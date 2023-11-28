# Copyright 2023 Intrinsic Innovation LLC

"""Helper module to construct a WaitForSettling action."""

from typing import Optional

from intrinsic.icon.actions import wait_for_settling_action_pb2
from intrinsic.icon.python import actions

ACTION_TYPE_NAME = "xfa.wait_for_settling_action"


def create_wait_for_settling_action(
    action_id: int,
    arm_part_name: str,
    uncertainty_threshold: Optional[float] = None,
) -> actions.Action:
  """Creates a WaitForSettling action.

  The action monitors joint velocity signals and waits until all long-lasting
  transients have vanished.

  Args:
    action_id: The ID of the action.
    arm_part_name: The name of the part providing JointPosition and
      JointVelocity interfaces.
    uncertainty_threshold: The uncertainty value below which the action is
      considered settled and done. Must be in range [0.01, 0.5]. Default is 0.2.

  Returns:
    The WaitForSettling action.
  """
  params = wait_for_settling_action_pb2.WaitForSettlingActionFixedParams()
  if uncertainty_threshold:
    params.uncertainty_threshold = uncertainty_threshold
  return actions.Action(action_id, ACTION_TYPE_NAME, arm_part_name, params)
