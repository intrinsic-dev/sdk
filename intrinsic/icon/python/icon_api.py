# Copyright 2023 Intrinsic Innovation LLC

"""Python client for the ICON Application Layer.

Provides a Python client API for application developers and skill authors who
wish to interact with ICON-compatible robots.
"""

from __future__ import annotations

import enum
from typing import Iterable, List, Mapping, Optional, Union
import warnings

import grpc
from intrinsic.icon.proto import logging_mode_pb2
from intrinsic.icon.proto import service_pb2
from intrinsic.icon.proto import service_pb2_grpc
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import _session
from intrinsic.icon.python import actions
from intrinsic.icon.python import errors
from intrinsic.icon.python import reactions
from intrinsic.icon.python import state_variable_path
from intrinsic.logging.proto import context_pb2
from intrinsic.solutions import deployments
from intrinsic.util.grpc import connection
from intrinsic.util.grpc import interceptor
from intrinsic.world.robot_payload.python import robot_payload

# Type forwarding, to enable instantiating these without loading the respective
# modules in client code. We believe that wrapping all class definitions in a
# single ICON module will increase usability.
Action = actions.Action
Condition = reactions.Condition
Reaction = reactions.Reaction
StartActionInRealTime = reactions.StartActionInRealTime
StartParallelActionInRealTime = reactions.StartParallelActionInRealTime
TriggerCallback = reactions.TriggerCallback
Event = reactions.Event
EventFlag = reactions.EventFlag
OperationalState = types_pb2.OperationalState
StateVariablePath = state_variable_path.StateVariablePath
# For generating documentation, Session needs to be publicly visible, but we
# override the settings to at least hide the constructor since it's not meant
# to be directly created.
Session = _session.Session
Stream = _session.Stream
__pdoc__ = {}
__pdoc__["Session.__init__"] = None

_DEFAULT_INSECURE = True
_DEFAULT_RPC_TIMEOUT_INFINITE = None
_DEFAULT_CONNECT_TIMEOUT_SECONDS = 20

# The default header to be used by ICON when connecting through the ingress.
# This is not valid if ICON is run as a resource.
ICON_HEADER_NAME = "x-icon-instance-name"


def _create_stub(
    connection_params: connection.ConnectionParams,
    insecure: bool = _DEFAULT_INSECURE,
    connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
) -> service_pb2_grpc.IconApiStub:
  """Creates a stub for the ICON gRPC service.

  Args:
    connection_params: The required parameters to talk to the specific ICON
      instance.
    insecure: Whether to use insecure channel credentials.
    connect_timeout: Time in seconds to wait for the ICON gRPC server to be
      ready.

  Returns:
    The ICON Client API stub.
  """
  if insecure:
    channel = grpc.insecure_channel(connection_params.address)
  else:
    channel_creds = grpc.local_channel_credentials()
    channel = grpc.secure_channel(connection_params.address, channel_creds)

  try:
    grpc.channel_ready_future(channel).result(timeout=connect_timeout)
  except grpc.FutureTimeoutError as e:
    raise errors.Client.ServerError("Failed to connect to ICON server") from e

  channel = grpc.intercept_channel(
      channel, interceptor.HeaderAdderInterceptor(connection_params.headers)
  )

  return service_pb2_grpc.IconApiStub(channel)


class Client:
  """Wrapper for the ICON gRPC service.

  Attributes:
    ActionType: Dynamically generated enum of all available action type names.
  """

  # Explicitly avoid errors around dynamically-populated action enums.
  _HAS_DYNAMIC_ATTRIBUTES = True
  _rpc_timeout_seconds: Optional[int] = None

  def __init__(
      self,
      stub: service_pb2_grpc.IconApiStub,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
  ):
    # Ensure the timeout is set before calling any methods that do RPCs, like
    # self._generate_action_types. By setting it before self._stub we should be
    # safe.
    self._rpc_timeout_seconds = rpc_timeout
    self._stub = stub
    self._generate_action_types()

  # Disable lint warnings since this is a class, not a standard attribute.
  # pylint: disable=invalid-name
  @property
  def ActionType(self) -> enum.Enum:
    return self._ActionType

  @ActionType.setter
  def ActionType(self, value: enum.Enum):
    self._ActionType = value

  # pylint: enable=invalid-name

  def _generate_action_types(self) -> None:
    """Dynamically generates the ActionType enum from the available actions."""
    action_signatures = self.list_action_signatures()
    action_type_names = {}
    for action_signature in action_signatures:
      if not action_signature.action_type_name:
        continue
      # Strip out namespace prefixes and convert to upper case constant.
      const_name = action_signature.action_type_name.split(".")[-1].upper()
      action_type_names[const_name] = action_signature.action_type_name
    # Disable lint warnings since this is a class, not a standard attribute.
    # pylint: disable=invalid-name
    self.ActionType = enum.Enum("ActionType", action_type_names)
    # pylint: enable=invalid-name

  @classmethod
  def connect(
      cls,
      grpc_host: str = "localhost",
      grpc_port: int = 8128,
      insecure: bool = _DEFAULT_INSECURE,
      connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
  ) -> Client:
    """Connects to the ICON gRPC service.

    This is a convenience wrapper around creating the stub and instantiating the
    Client separately.

    Args:
      grpc_host: Host to connect to for the ICON gRPC server.
      grpc_port: Port to connect to for the ICON gRPC server.
      insecure: Whether to use insecure channel credentials.
      connect_timeout: Time in seconds to wait for the ICON gRPC server to be
        ready.
      rpc_timeout: Time in seconds to wait for RPCs to complete.

    Returns:
      An instance of the ICON Client.
    """
    return cls.connect_with_params(
        connection.ConnectionParams.no_ingress(f"{grpc_host}:{grpc_port}"),
        insecure=insecure,
        connect_timeout=connect_timeout,
        rpc_timeout=rpc_timeout,
    )

  @classmethod
  def connect_with_params(
      cls,
      connection_params: connection.ConnectionParams,
      insecure: bool = _DEFAULT_INSECURE,
      connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT_SECONDS,
      rpc_timeout: Optional[int] = _DEFAULT_RPC_TIMEOUT_INFINITE,
  ) -> Client:
    """Connects to the ICON gRPC service.

    This is a convenience wrapper around creating the stub and instantiating the
    Client separately.

    Args:
      connection_params: The required parameters to talk to the specific ICON
        instance.
      insecure: Whether to use insecure channel credentials.
      connect_timeout: Time in seconds to wait for the ICON gRPC server to be
        ready.
      rpc_timeout: Time in seconds to wait for RPCs to complete.

    Returns:
      An instance of the ICON Client.
    """
    return cls(
        _create_stub(
            connection_params=connection_params,
            insecure=insecure,
            connect_timeout=connect_timeout,
        ),
        rpc_timeout,
    )

  @classmethod
  def for_solution(cls, solution: deployments.Solution) -> Client:
    """Connects to the ICON gRPC service for a given solution."""
    return cls(service_pb2_grpc.IconApiStub(solution.grpc_channel))

  def get_action_signature_by_name(
      self, action_type_name: str
  ) -> Optional[types_pb2.ActionSignature]:
    """Gets details of an action type, by name.

    Args:
      action_type_name: The action type to lookup.

    Returns:
      ActionSignature, or None if the action type is not found.
      Propagates gRPC exceptions.
    """
    response = self._stub.GetActionSignatureByName(
        service_pb2.GetActionSignatureByNameRequest(name=action_type_name),
        timeout=self._rpc_timeout_seconds,
    )
    if not response.HasField("action_signature"):
      return None
    return response.action_signature

  def get_config(self) -> service_pb2.GetConfigResponse:
    """Gets part-specific config properties.

    These are fixed properties for the lifetime of the server (for
    example, the number of DOFs for a robot arm.)
    Returns:
      GetConfigResponse.
      Propagates gRPC exceptions.
    """
    return self._stub.GetConfig(
        service_pb2.GetConfigRequest(), timeout=self._rpc_timeout_seconds
    )

  def get_status(self) -> service_pb2.GetStatusResponse:
    """Gets a snapshot of the server-side status, including part-specific status.

    Returns:
      GetStatusResponse.
      Propagates gRPC exceptions.
    """
    return self._stub.GetStatus(
        service_pb2.GetStatusRequest(), timeout=self._rpc_timeout_seconds
    )

  def is_action_compatible(self, action_type_name: str, part: str) -> bool:
    """Reports whether actions of type `action_type_name` are compatible with `part`.

    Args:
      action_type_name: The action type to check.
      part: Name of the part to check.

    Returns:
      True iff actions of type `action_type_name` can be instantiated using
      `part` (in one of their slots).
      Propagates gRPC exceptions.
    """
    return self._stub.IsActionCompatible(
        service_pb2.IsActionCompatibleRequest(
            action_type_name=action_type_name, part_name=part
        ),
        timeout=self._rpc_timeout_seconds,
    ).is_compatible

  def list_action_signatures(self) -> Iterable[types_pb2.ActionSignature]:
    """Lists details of all available action types.

    Returns:
      Iterable of ActionSignatures.
    """
    return self._stub.ListActionSignatures(
        service_pb2.ListActionSignaturesRequest(),
        timeout=self._rpc_timeout_seconds,
    ).action_signatures

  def list_compatible_parts(
      self, action_type_names: Iterable[str]
  ) -> List[str]:
    """Lists the parts that are compatible with all of the listed action types.

    Args:
      action_type_names: The action types to check.

    Returns:
      List of individual parts that can be controlled by actions listed in
      `action_type_name`. If `action_type_names` is empty, returns all parts.
    """
    return self._stub.ListCompatibleParts(
        service_pb2.ListCompatiblePartsRequest(
            action_type_names=action_type_names
        ),
        timeout=self._rpc_timeout_seconds,
    ).parts

  def list_parts(self) -> List[str]:
    """Lists all available parts.

    Returns:
      List of available parts.
    """
    return self._stub.ListParts(
        service_pb2.ListPartsRequest(), timeout=self._rpc_timeout_seconds
    ).parts

  def start_session(
      self, parts: List[str], context: Optional[context_pb2.Context] = None
  ) -> _session.Session:
    """Starts a new `Session` for the given parts.

    Context management is supported, and it is recommended to obtain the Session
    using the `with` statement. For example:

      with icon_client.start_session(["robot_arm", "robot_gripper"]) as session:
        # ...

    Otherwise, do not forget to call `end()` once done with the Session. For
    example:

      session = icon_client.start_session(["robot_arm", "robot_gripper"])
      try:
        # ...
      finally:
        session.end()

    Attempts to recreate the same Session without calling `end()` will cause an
    exception since parts are exclusive to a Session. Otherwise once the Python
    process ends, the Session will be cleaned up via garbage collection. Note
    that this is not always guaranteed, see
    https://docs.python.org/3.3/reference/datamodel.html). In a notebook
    environment such as Jupyter, this can be triggered by restarting the kernel.

    Args:
      parts: List of parts to control.
      context: The log context passed to the session. Needed to sync ICON logs
        to the cloud. In skills use `context.logging_context`.

    Returns:
      A new Session.

    Raises:
      grpc.RpcError: An error occurred while starting the `Session`.
    """
    return _session.Session(self._stub, parts, context)

  def enable(self) -> None:
    """Enables all parts on the server.

    Performs all steps necessary to get the parts ready to receive commands.

    NOTE: Enabling a server is something the user does directly. DO NOT call
    this from library code automatically to make things more convenient. Human
    users must be able to rely on the robot to stay still unless they enable
    it.

    Raises:
      grpc.RpcError: An error occurred while enabling.
    """
    warnings.warn(
        "enable() is deprecated. ICON automatically enables whenever possible,"
        " and this function will be removed once all call sites are gone.",
        DeprecationWarning,
    )
    self._stub.Enable(
        service_pb2.EnableRequest(), timeout=self._rpc_timeout_seconds
    )

  def disable(self) -> None:
    """Disables all parts on the server.

    NOTE: Disabling a server is something the user does directly. DO NOT call
    this from library code automatically to make things more convenient. Human
    users must be able to rely on the robot to stay enabled unless they
    explicitly disable it (or the robot encounters a fault).


    Ends all currently-active sessions.

    Raises:
      grpc.RpcError: An error occurred while disabling.
    """
    warnings.warn(
        "enable() is deprecated. ICON automatically enables whenever possible,"
        " and this function will be removed once all call sites are gone.",
        DeprecationWarning,
    )
    self._stub.Disable(
        service_pb2.DisableRequest(), timeout=self._rpc_timeout_seconds
    )

  def clear_faults(self) -> None:
    """Clears all faults and returns the server to a disabled state.

    NOTE: Clearing faults is something the user does directly. DO NOT call this
    from library code automatically to make things more convenient, ESPECIALLY
    not in connection with re-enabling the server afterwards! Human users must
    be able to rely on the robot to stay still unless they explicitly clear the
    fault(s) and enable it again.

    Some classes of faults (internal server errors or issues that have a
    physical root cause) may require additional server- or hardware-specific
    mitigation before clear_faults can successfully clear the fault.

    Raises:
      grpc.RpcError: An error occurred while clearing faults.
    """
    self._stub.ClearFaults(
        service_pb2.ClearFaultsRequest(), timeout=self._rpc_timeout_seconds
    )

  def get_operational_status(self) -> types_pb2.OperationalStatus:
    """Returns the operational status of the server.

    This status may indicate that the server is ENABLED, DISABLED, or FAULTED.
    If FAULTED, OperationalStatus also includes a string explaining why the
    robot faulted.

    Returns:
      The operational status of the server.

    Raises:
      grpc.RpcError: An error occurred while getting the state.
    """
    resp = self._stub.GetOperationalStatus(
        service_pb2.GetOperationalStatusRequest(),
        timeout=self._rpc_timeout_seconds,
    )
    return resp.operational_status

  def get_speed_override(self) -> float:
    """Returns the current speed override value.

    This is a value between 0 and 1, and acts as a multiplier to the speed of
    compatible actions.
    """
    resp = self._stub.GetSpeedOverride(
        service_pb2.GetSpeedOverrideRequest(), timeout=self._rpc_timeout_seconds
    )
    return resp.override_factor

  def set_speed_override(self, new_speed_override: float) -> None:
    """Sets the speed override value.

    Args:
      new_speed_override: A value between 0 and 1. Compatible actions will do
        their best to scale their speed.

    Raises:
      grpc.RpcError on errors, including invalid values
    """
    self._stub.SetSpeedOverride(
        service_pb2.SetSpeedOverrideRequest(override_factor=new_speed_override),
        timeout=self._rpc_timeout_seconds,
    )

  def get_logging_mode(self) -> logging_mode_pb2.LoggingMode:
    """Gets the logging mode."""
    return self._stub.GetLoggingMode(
        service_pb2.GetLoggingModeRequest(), timeout=self._rpc_timeout_seconds
    ).logging_mode

  def set_logging_mode(
      self, logging_mode: logging_mode_pb2.LoggingMode
  ) -> None:
    """Sets the logging mode.

    The logging mode defines which robot-status logs are logged to the cloud.
    ICON logs only to the cloud if a session is active. PuSub is not influenced
    by this setting.

    Args:
      logging_mode: The logging mode to set.
    """
    self._stub.SetLoggingMode(
        service_pb2.SetLoggingModeRequest(logging_mode=logging_mode),
        timeout=self._rpc_timeout_seconds,
    )

  def get_part_properties(self) -> service_pb2.GetPartPropertiesResponse:
    """Gets the values of all part properties.

    Returns:
      A GetPartPropertiesResponse proto that contains:
      * The control timestamp at the time the properties were reported
      * The wall time at the time the properties were reported
      * A map from part name to a map from property name to value
        For instance: {'robot': {'motor_0_current_amps': 2.0}}

    Raises:
      grpc.RpcError: The ICON server responds with an error. See message for
        details.
    """
    return self._stub.GetPartProperties(
        service_pb2.GetPartPropertiesRequest(),
        timeout=self._rpc_timeout_seconds,
    )

  def set_part_properties(
      self, part_properties: Mapping[str, Mapping[str, Union[bool, float]]]
  ) -> None:
    """Sets part properties.

    Check the output of get_part_properties to learn the available properties
    and their types.

    Args:
      part_properties: A map from part name to a map from property name to
        value. For instance: {'robot': {'internal_controller_p_value': 0.2}}

    Raises:
      grpc.RpcError: Server responded with an error. Common errors include
        unknown part or property names, or wrong property types.
    """
    request = service_pb2.SetPartPropertiesRequest()
    for part_name, properties in part_properties.items():
      properties_proto = service_pb2.PartPropertyValues()
      for property_name, property_value in properties.items():
        value_proto = service_pb2.PartPropertyValue()
        if isinstance(property_value, bool):
          value_proto.bool_value = property_value
        if isinstance(property_value, float):
          value_proto.double_value = property_value
        properties_proto.property_values_by_name[property_name].CopyFrom(
            value_proto
        )
      request.part_properties_by_part_name[part_name].CopyFrom(properties_proto)
    self._stub.SetPartProperties(request, timeout=self._rpc_timeout_seconds)
