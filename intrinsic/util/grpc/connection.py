# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides utilities for creating gRPC connections."""

from __future__ import annotations
import dataclasses
from typing import List, Optional, Tuple


@dataclasses.dataclass
class ConnectionParams:
  """Specifies how Client should connect to a gRPC server.

  Servers running behind an ingress in a kubernetes cluster require the
  appropriate metadata information to be set.
  """

  address: str
  instance_name: Optional[str]
  header: Optional[str]

  @classmethod
  def no_ingress(cls, address: str) -> ConnectionParams:
    """Helper for connecting to an instance of a server not behind an ingress.

    Args:
      address: The full address, including port number, on which to connect.

    Returns:
      A ConnectionParams that can be used with Client.connect_with_params
    """
    return cls(address, None, None)

  @classmethod
  def local_port(cls, port: int) -> ConnectionParams:
    """Helper for connecting to a local instance of a server on a specific port.

    This primarily should be used for testing purposes.  It will not specify
    information for ingress into a kubernetes cluster.

    Args:
      port: The port number on which to connect localhost.

    Returns:
      A ConnectionParams that can be used with Client.connect_with_params
    """
    return cls(f"localhost:{port}", None, None)

  def headers(self) -> Optional[List[Tuple[str, str]]]:
    """Generates the http headers needed to route to the appropriate ingress."""
    if not self.header or not self.instance_name:
      return None
    return [(self.header, self.instance_name)]
