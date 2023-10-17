# Copyright 2023 Intrinsic Innovation LLC

"""Example of using operational status from the ICON Application Layer.

Showcases how to use the ICON Python client API to modify and retrieve the ICON
server's operational status.
"""

import time

from absl import app
from absl import flags
from intrinsic.icon.python import icon_api
from intrinsic.util.grpc import connection

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


def _display_operational_status(icon_client: icon_api.Client):
  """Displays the ICON server's operational status."""
  status = icon_client.get_operational_status()
  if status.state == icon_api.OperationalState.FAULTED:
    print('ICON is FAULTED with reason ', status.fault_reason)
  elif status.state == icon_api.OperationalState.DISABLED:
    print('ICON is DISABLED')
  elif status.state == icon_api.OperationalState.ENABLED:
    print('ICON is ENABLED')


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  icon_client = icon_api.Client.connect_with_params(
      connection.ConnectionParams(
          f'{_HOST.value}:{_PORT.value}', _INSTANCE.value, _HEADER.value
      )
  )
  _display_operational_status(icon_client)

  icon_client.disable()
  time.sleep(1.0)
  _display_operational_status(icon_client)

  icon_client.enable()
  _display_operational_status(icon_client)


if __name__ == '__main__':
  app.run(main)
