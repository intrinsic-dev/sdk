# Copyright 2023 Intrinsic Innovation LLC

"""Python client for the Gripper Layer.

Provides a Python client API for application developers and skill authors who
wish to interact with grippers.
"""

from __future__ import annotations

import enum
import logging
from typing import Optional

import grpc
from intrinsic.hardware.gripper.eoat import eoat_service_pb2
from intrinsic.hardware.gripper.eoat import eoat_service_pb2_grpc
from intrinsic.hardware.gripper.service.proto import generic_gripper_pb2
from intrinsic.hardware.gripper.service.proto import generic_gripper_pb2_grpc
from intrinsic.icon.python import errors
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.util.grpc import connection
from intrinsic.util.grpc import interceptor

# For generating documentation, Session needs to be publicly visible, but we
# override the settings to at least hide the constructor since it's not meant
# to be directly created.

_DEFAULT_INSECURE = True
_DEFAULT_RPC_TIMEOUT_INFINITE = None
_DEFAULT_CONNECT_TIMEOUT_SECONDS = 20

_STUB_LIKE_TYPES = (
    eoat_service_pb2_grpc.SuctionGripperStub
    | eoat_service_pb2_grpc.PinchGripperStub
    | generic_gripper_pb2_grpc.GenericGripperStub
)


class GripperTypes(enum.Enum):
  """Types of grippers."""

  UNKNOWN = 0
  SUCTION = 1
  PINCH = 2
  # Implemented by intrinsic/hardware/gripper/service/generic_gripper_service.h
  ADAPTIVE_PINCH = 3


_GRIPPER_TYPE_TO_GRIPPER_STUB_CONSTRUCTOR = {
    GripperTypes.SUCTION: eoat_service_pb2_grpc.SuctionGripperStub,
    GripperTypes.PINCH: eoat_service_pb2_grpc.PinchGripperStub,
    GripperTypes.ADAPTIVE_PINCH: generic_gripper_pb2_grpc.GenericGripperStub,
}
_DEFAULT_GRIPPER_TYPE = GripperTypes.SUCTION


def _create_stub(
    connection_params: connection.ConnectionParams,
    insecure: bool = _DEFAULT_INSECURE,
    connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
    gripper_type: GripperTypes = _DEFAULT_GRIPPER_TYPE,
) -> _STUB_LIKE_TYPES:
  """Creates a stub for the gripper gRPC service.

  Currently supports suction, pinch and adaptive pinch grippers.

  Args:
    connection_params: The required parameters to talk to the specific gripper
      instance.
    insecure: Whether to use insecure channel credentials.
    connect_timeout: Time in seconds to wait for the gripper gRPC server to be
      ready.
    gripper_type: The gripper type.

  Returns:
    The gripper client API stub.
  """
  # Check gripper type.
  if gripper_type not in _GRIPPER_TYPE_TO_GRIPPER_STUB_CONSTRUCTOR.keys():
    raise NotImplementedError(
        f"Gripper type unsupported: {gripper_type}. Currently only support"
        f" {_GRIPPER_TYPE_TO_GRIPPER_STUB_CONSTRUCTOR.keys()}"
    )

  # Creates a channel.
  if insecure:
    channel = grpc.insecure_channel(connection_params.address)
  else:
    channel_creds = grpc.local_channel_credentials()
    channel = grpc.secure_channel(connection_params.address, channel_creds)

  try:
    grpc.channel_ready_future(channel).result(timeout=connect_timeout)
  except grpc.FutureTimeoutError as e:
    raise errors.Client.ServerError(
        "Failed to connect to the gripper server"
    ) from e

  channel = grpc.intercept_channel(
      channel, interceptor.HeaderAdderInterceptor(connection_params.headers)
  )

  return _GRIPPER_TYPE_TO_GRIPPER_STUB_CONSTRUCTOR[gripper_type](
      channel=channel
  )


class GripperClient:
  """Wrapper for the gripper gRPC service."""

  _rpc_timeout_seconds: Optional[int] = None

  def __init__(
      self,
      stub: _STUB_LIKE_TYPES,
      gripper_type: GripperTypes,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
  ):
    # Ensure the timeout is set before calling any methods that do RPCs, like
    # self._generate_action_types. By setting it before self._stub we should be
    # safe.
    self._rpc_timeout_seconds = rpc_timeout
    self._stub = stub

    if gripper_type == GripperTypes.UNKNOWN:
      raise ValueError("Gripper type is UNKNOWN.")

    if gripper_type == GripperTypes.ADAPTIVE_PINCH:
      if not isinstance(stub, generic_gripper_pb2_grpc.GenericGripperStub):
        raise ValueError(
            "Gripper type is ADAPTIVE_PINCH, but the given stub is"
            f" {type(stub)} not a GenericGripperStub."
        )
    if gripper_type == GripperTypes.SUCTION:
      if not isinstance(stub, eoat_service_pb2_grpc.SuctionGripperStub):
        raise ValueError(
            f"Gripper type is SUCTION, but the given stub is {type(stub)} not a"
            " SuctionGripperStub."
        )
    if gripper_type == GripperTypes.PINCH:
      if not isinstance(stub, eoat_service_pb2_grpc.PinchGripperStub):
        raise ValueError(
            f"Gripper type is PINCH, but the given stub is {type(stub)} not a"
            " PinchGripperStub."
        )

    # Gripper type.
    self._gripper_type = gripper_type

  @classmethod
  def connect(
      cls,
      grpc_host: str = "localhost",
      grpc_port: int = 8128,
      insecure: bool = _DEFAULT_INSECURE,
      connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
      gripper_type: GripperTypes = _DEFAULT_GRIPPER_TYPE,
  ) -> GripperClient:
    """Connects to the Gripper gRPC service.

    This is a convenience wrapper around creating the stub and instantiating the
    Client separately.

    Args:
      grpc_host: Host to connect to for the Gripper gRPC server.
      grpc_port: Port to connect to for the Gripper gRPC server.
      insecure: Whether to use insecure channel credentials.
      connect_timeout: Time in seconds to wait for the ICON gRPC server to be
        ready.
      rpc_timeout: Time in seconds to wait for RPCs to complete.
      gripper_type: The type of gripper to connect to.

    Returns:
      An instance of the Gripper Client.
    """
    return cls.connect_with_params(
        connection.ConnectionParams.no_ingress(f"{grpc_host}:{grpc_port}"),
        insecure=insecure,
        connect_timeout=connect_timeout,
        rpc_timeout=rpc_timeout,
        gripper_type=gripper_type,
    )

  @classmethod
  def connect_with_params(
      cls,
      connection_params: connection.ConnectionParams,
      insecure: bool = _DEFAULT_INSECURE,
      connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
      gripper_type: GripperTypes = _DEFAULT_GRIPPER_TYPE,
  ) -> GripperClient:
    """Connects to the Gripper gRPC service.

    This is a convenience wrapper around creating the stub and instantiating the
    GripperClient separately.

    Args:
      connection_params: The required parameters to talk to the specific ICON
        instance.
      insecure: Whether to use insecure channel credentials.
      connect_timeout: Time in seconds to wait for the ICON gRPC server to be
        ready.
      rpc_timeout: Time in seconds to wait for RPCs to complete.
      gripper_type: The type of gripper to connect to.

    Returns:
      An instance of the GripperClient.
    """
    return cls(
        stub=_create_stub(
            connection_params=connection_params,
            insecure=insecure,
            connect_timeout=connect_timeout,
            gripper_type=gripper_type,
        ),
        gripper_type=gripper_type,
        rpc_timeout=rpc_timeout,
    )

  @classmethod
  def connect_with_gripper_handle(
      cls,
      gripper_handle: resource_handle_pb2.ResourceHandle,
      insecure: bool = _DEFAULT_INSECURE,
      connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
      gripper_type: GripperTypes = _DEFAULT_GRIPPER_TYPE,
  ) -> GripperClient:
    """Connects to the Gripper gRPC service.

    This is another convenience wrapper around creating the stub and
    instantiating the GripperClient separately.

    Args:
      gripper_handle: The gripper's resource handle. Contains parameters to
        connect to the gripper service.
      insecure: Whether to use insecure channel credentials.
      connect_timeout: Time in seconds to wait for the ICON gRPC server to be
        ready.
      rpc_timeout: Time in seconds to wait for RPCs to complete.
      gripper_type: The type of gripper to connect to.

    Returns:
      An instance of the GripperClient.
    """
    grpc_info = gripper_handle.connection_info.grpc
    connection_params = connection.ConnectionParams(
        address=grpc_info.address,
        instance_name=grpc_info.server_instance,
        header=grpc_info.header,
    )
    logging.info(
        "Connecting to gripper service at '%s:%s'",
        grpc_info.address,
        grpc_info.server_instance,
    )
    return cls.connect_with_params(
        connection_params=connection_params,
        insecure=insecure,
        connect_timeout=connect_timeout,
        rpc_timeout=rpc_timeout,
        gripper_type=gripper_type,
    )

  def grasp(self) -> None:
    """Request `grasp` on the server."""
    if self._gripper_type == GripperTypes.ADAPTIVE_PINCH:
      self._stub.Grasp(
          generic_gripper_pb2.GraspRequest(), timeout=self._rpc_timeout_seconds
      )
    else:
      self._stub.Grasp(
          eoat_service_pb2.GraspRequest(), timeout=self._rpc_timeout_seconds
      )

  def release(self) -> None:
    """Request `release` on the server."""
    if self._gripper_type == GripperTypes.ADAPTIVE_PINCH:
      self._stub.Release(
          generic_gripper_pb2.ReleaseRequest(enable_blowoff=False),
          timeout=self._rpc_timeout_seconds,
      )
    else:
      self._stub.Release(
          eoat_service_pb2.ReleaseRequest(), timeout=self._rpc_timeout_seconds
      )

  def blow_off(self) -> None:
    """Request `blow off` on the server.

    Note that only suction gripper has this function.

    Raises:
      ValueError: If this is requested on a non-suction gripper.
    """
    if isinstance(self._stub, eoat_service_pb2_grpc.SuctionGripperStub):
      self._stub.BlowOff(
          eoat_service_pb2.BlowOffRequest(), timeout=self._rpc_timeout_seconds
      )
    else:
      raise ValueError(f"Gripper type {self._gripper_type} cannot blow off .")

  def gripping_indicated(self) -> bool:
    """Check if the gripper is holding something.

    On a suction gripper, this means suction pressure exceeds a preset
    threshold, which indicates an object is present. On a pinch gripper, this
    usually means the distance between fingers is larger than a threshold.

    Returns:
      Whether the grasp was successful.
    """
    if self._gripper_type == GripperTypes.ADAPTIVE_PINCH:
      return self._stub.GrippingIndicated(
          generic_gripper_pb2.GrippingIndicatedRequest(),
          timeout=self._rpc_timeout_seconds,
      ).indicated

    return self._stub.GrippingIndicated(
        eoat_service_pb2.GrippingIndicatedRequest(),
        timeout=self._rpc_timeout_seconds,
    ).indicated

  def command(
      self, command: generic_gripper_pb2.CommandRequest
  ) -> generic_gripper_pb2.CommandResponse:
    """Commands the gripper.

    On an adaptive pinch gripper, controls the gripper with one or more of the
    following commands:
     * move to a specific position
     * move with a specific velocity
     * move with a specific force

    Args:
      command: The command to send to the gripper.

    Returns:
      The response from the gripper.

    Raises:
      ValueError: If this is requested on a non-adaptive pinch gripper.
    """
    if isinstance(self._stub, generic_gripper_pb2_grpc.GenericGripperStub):
      return self._stub.Command(command, timeout=self._rpc_timeout_seconds)
    raise ValueError(f"Gripper type {self._gripper_type} cannot be commanded.")
