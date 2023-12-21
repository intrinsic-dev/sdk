# Copyright 2023 Intrinsic Innovation LLC

"""Helper module to construct an ADIOAction."""

from collections import abc
import dataclasses
from intrinsic.icon.actions import adio_pb2
from intrinsic.icon.python import actions

ACTION_TYPE_NAME = "xfa.adio"


@dataclasses.dataclass(frozen=True)
class StateVariables:
  OUTPUTS_SET = "xfa.outputs_set"


def create_digital_output_action(
    action_id: int,
    adio_part_name: str,
    digital_outputs: abc.Mapping[str, adio_pb2.DigitalBlock] | None = None,
) -> actions.Action:
  """Creates an ADIOAction to det digital outputs.

  Args:
    action_id: The ID of the action.
    adio_part_name: The name of the part providing the ADIO interface.
    digital_outputs: The digital outputs to set.

  Returns:
    The ADIO action.
  """
  params = adio_pb2.ADIOFixedParams()

  if digital_outputs is not None:
    for key, value in digital_outputs.items():
      params.outputs.digital_outputs[key].CopyFrom(value)

  return actions.Action(action_id, ACTION_TYPE_NAME, adio_part_name, params)
