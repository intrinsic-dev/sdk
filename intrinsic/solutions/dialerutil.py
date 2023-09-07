# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides methods to API key autorized gRPC calls.

This file implements a subset of the
`//intrinsic/skills/tools/skill/cmd/dialerutil.go` library.
"""

import dataclasses
from typing import Any, List, Optional, Tuple
import grpc
from intrinsic.solutions import auth


@dataclasses.dataclass()
class CreateChannelParams:
  """Contains information to create a gRPC connection."""

  address: Optional[str] = None
  cluster: Optional[str] = None
  project_name: Optional[str] = None
  cred_alias: Optional[str] = None

  def has_local_address(self) -> bool:
    if self.address is None:
      return False

    return any(
        local in self.address for local in ["127.0.0.1", "local", "xfa.lan"]
    )


class _TokenAuth(grpc.AuthMetadataPlugin):
  """gRPC Metadata Plugin that adds an API key to the header."""

  def __init__(self, token: auth.ProjectToken):
    self._token = token

  def __call__(self, context, callback):
    callback(self._token.get_request_metadata(), None)


class _ServerName(grpc.AuthMetadataPlugin):
  """gRPC Metadata Plugin that adds the cluster name to the header."""

  def __init__(self, server_name: str):
    self._server_name = server_name

  def __call__(self, context, callback):
    callback((("x-server-name", self._server_name),), None)


class CredentialsRequiredError(ValueError):
  """Thrown in case the credential name is missing for a non-local gRPC call."""


def _load_credentials(
    params: CreateChannelParams,
) -> auth.ProjectToken:
  """Reads and creates a ProjectToken from local API keys."""
  if params.project_name is not None:
    configuration = auth.get_configuration(params.project_name)

    if params.cred_alias is None:
      return configuration.get_default_credentials()

    return configuration.get_credentials(params.cred_alias)

  raise CredentialsRequiredError()


def create_channel(
    params: CreateChannelParams,
    grpc_options: Optional[List[Tuple[str, Any]]] = None,
) -> grpc.Channel:
  """Creates a gRPC channel with the provided connection information."""

  if params.has_local_address():
    return grpc.insecure_channel(params.address, options=grpc_options)

  if params.project_name is None:
    raise ValueError(
        f"Non-local connection '{params.address}' without a project name is not"
        " supported!"
    )

  channel_credentials = grpc.ssl_channel_credentials()
  call_credentials = []

  token = _load_credentials(params)
  call_credentials.append(
      grpc.metadata_call_credentials(_TokenAuth(token), name="TokenAuth")
  )

  if params.cluster is not None:
    call_credentials.append(
        grpc.metadata_call_credentials(
            _ServerName(params.cluster), name="ServerName"
        )
    )

  return grpc.secure_channel(
      f"dns:///www.endpoints.{params.project_name}.cloud.goog:443",
      grpc.composite_channel_credentials(
          channel_credentials, *call_credentials
      ),
      options=grpc_options,
  )
