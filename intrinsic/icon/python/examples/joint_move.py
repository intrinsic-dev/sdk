# Copyright 2023 Intrinsic Innovation LLC

"""Example of joint motion from the ICON Application Layer.

Showcases how to use the ICON Python client API to command point-to-point moves
on the server.
"""

from typing import Sequence
from absl import app
from absl import flags
import grpc
from intrinsic.icon.python import create_action_utils
from intrinsic.icon.python import errors
from intrinsic.icon.python import icon_api
from intrinsic.util.grpc import connection
import numpy as np

_HOST = flags.DEFINE_string(
    'host', 'xfa.lan', 'ICON server gRPC connection host'
)
_PORT = flags.DEFINE_integer('port', 17080, 'ICON server gRPC connection port')
_INSTANCE = flags.DEFINE_string(
    'instance',
    None,
    'The instance of ICON, if behind an ingress, you intend to talk to',
)
_HEADER = flags.DEFINE_string(
    'header',
    icon_api.ICON_HEADER_NAME,
    'Optional header name to be used to select a specific ICON instance.  Has '
    'no effect if --instance is not set.',
)
_PART = flags.DEFINE_string('part', 'arm', 'Part to control.')


def _example_joint_move(icon_client: icon_api.Client, part_name: str):
  """Moves the robot to two different joint positions.

  The first joint position is slightly offset from the joint range center, the
  second position is the center of the joint range.

  Args:
    icon_client: The client to connect to.
    part_name: The name of the part to move.

  Raises:
    LookupError: If there is not at least one part on the ICON server.
    KeyError: If the part name is not recognized by ICON.
  """

  for config in icon_client.get_config().part_configs:
    if config.name == part_name:
      limits_config = config.generic_config.joint_limits_config
      application_limits = limits_config.application_limits
      break
  else:
    raise KeyError('Could not find a part config for part {}'.format(part_name))

  min_pos = np.asarray(application_limits.min_position.values)
  max_pos = np.asarray(application_limits.max_position.values)

  center_pos = (min_pos + max_pos) / 2.0
  joint_range = max_pos - min_pos

  jpos1 = center_pos + np.minimum(joint_range / 5.0, 0.5)
  jpos2 = center_pos

  parts = [part_name]
  if not parts:
    raise LookupError(
        'This example needs at least one part on the ICON server.'
    )

  try:
    with icon_client.start_session(parts=parts) as session:
      try:
        jmove1 = create_action_utils.create_point_to_point_move_action(
            action_id=1, joint_position_part_name=parts[0], goal_position=jpos1
        )
        jstop = create_action_utils.create_stop_action(
            action_id=2, joint_position_part_name=parts[0]
        )
        jmove2 = create_action_utils.create_point_to_point_move_action(
            action_id=3, joint_position_part_name=parts[0], goal_position=jpos2
        )
        done_signal = session.add_action_sequence([jmove1, jstop, jmove2])
        session.start_action_and_wait(jmove1, done_signal)
      except errors.Session.ActionError as e:
        print('Action error:', e)
  except grpc.RpcError as e:
    print('Session error:', e)


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  icon_client = icon_api.Client.connect_with_params(
      connection.ConnectionParams(
          f'{_HOST.value}:{_PORT.value}', _INSTANCE.value, _HEADER.value
      )
  )

  _example_joint_move(icon_client, _PART.value)


if __name__ == '__main__':
  app.run(main)
