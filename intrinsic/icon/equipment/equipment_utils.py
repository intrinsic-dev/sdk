# Copyright 2023 Intrinsic Innovation LLC

"""Helper functions to interact with ICON equipment in Python.

Instead of directly building ICON resource selectors and connections, use these
helper functions to avoid depending directly on the underlying proto messages.
"""

from typing import Optional
from absl import logging
from intrinsic.icon.equipment import icon_equipment_pb2
from intrinsic.icon.python import icon_api
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.proto import equipment_pb2
from intrinsic.util.grpc import connection

ICON2_POSITION_PART_KEY = "Icon2PositionPart"
ICON2_GRIPPER_PART_KEY = "Icon2GripperPart"
ICON2_ADIO_PART_KEY = "Icon2AdioPart"
ICON2_FORCE_TORQUE_SENSOR_PART_KEY = "Icon2ForceTorqueSensorPart"
ICON2_RANGEFINDER_PART_KEY = "Icon2RangefinderPart"


def make_icon_resource_selector(
    with_position_controlled_part: bool = False,
    with_gripper_part: bool = False,
    with_adio_part: bool = False,
    with_force_torque_sensor_part: bool = False,
    with_rangefinder_part: bool = False,
    with_observation_stream: bool = False,
) -> equipment_pb2.ResourceSelector:
  """Creates a resource selector for an ICON resource handle with specific parts.

  Args:
    with_position_controlled_part: If true, requires a position-controlled part.
    with_gripper_part: If true, requires a gripper part.
    with_adio_part: If true, requires an adio part.
    with_force_torque_sensor_part: If true, requires a force_torque_sensor part.
    with_rangefinder_part: If true, requires a rangefinder part.
    with_observation_stream: If true, requires an observation stream config.

  Returns:
    A populated resource selector.
  """

  capability_names = ["intrinsic_proto.icon.IconApi"]
  if with_position_controlled_part:
    capability_names.append(ICON2_POSITION_PART_KEY)
  if with_gripper_part:
    capability_names.append(ICON2_GRIPPER_PART_KEY)
  if with_adio_part:
    capability_names.append(ICON2_ADIO_PART_KEY)
  if with_force_torque_sensor_part:
    capability_names.append(ICON2_FORCE_TORQUE_SENSOR_PART_KEY)
  if with_rangefinder_part:
    capability_names.append(ICON2_RANGEFINDER_PART_KEY)
  if with_observation_stream:
    capability_names.append("IconRobotObservationStreamParams")

  return equipment_pb2.ResourceSelector(capability_names=capability_names)


def _get_params_from_connection_info(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> Optional[connection.ConnectionParams]:
  """Creates params to start an ICON client from a handle's connection_info.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The connected ConnectionParams if the handle provides enough information.
  """
  if not resource_handle.HasField("connection_info"):
    return None
  if not resource_handle.connection_info.HasField("grpc"):
    return None
  return connection.ConnectionParams(
      resource_handle.connection_info.grpc.address,
      resource_handle.connection_info.grpc.server_instance,
      resource_handle.connection_info.grpc.header,
  )


def init_icon_client(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> icon_api.Client:
  """Creates a client for talking to the icon server.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The connected Client.

  Raises:
    KeyError: If resource_handle does not include any connection config.
  """
  connection_params = _get_params_from_connection_info(resource_handle)

  if not connection_params:
    raise KeyError("No ICON connection config was provided.")

  logging.info("ICON connection_params: %s", connection_params)
  return icon_api.Client.connect_with_params(connection_params, insecure=True)


def get_position_part_name(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> str:
  """Gets the name of the Icon2PositionPart from the resource data.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The part name.

  Raises:
    KeyError: If resource_handle does not include an Icon2PositionPart data.
  """
  icon_position_part = icon_equipment_pb2.Icon2PositionPart()
  pos_key = ICON2_POSITION_PART_KEY
  if pos_key not in resource_handle.resource_data:
    raise KeyError(
        "%s is not in resource_handle.resource_data. Available: %r"
        % (pos_key, resource_handle.resource_data.keys())
    )
  resource_handle.resource_data[pos_key].contents.Unpack(icon_position_part)
  logging.info("ICON position_part: %s", icon_position_part)
  return icon_position_part.part_name


def get_gripper_part_name(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> str:
  """Gets the name of the Icon2GripperPart from the resource data.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The part name.

  Raises:
    KeyError: If resource_handle does not include an Icon2GripperPart data.
  """
  icon_gripper_part = icon_equipment_pb2.Icon2GripperPart()
  gripper_key = ICON2_GRIPPER_PART_KEY
  if gripper_key not in resource_handle.resource_data:
    raise KeyError(
        "%s is not in resource_handle.resource_data. Available: %r"
        % (gripper_key, resource_handle.resource_data.keys())
    )
  resource_handle.resource_data[gripper_key].contents.Unpack(icon_gripper_part)
  logging.info("ICON gripper_part: %s", icon_gripper_part)
  return icon_gripper_part.part_name


def get_force_torque_sensor_part_name(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> str:
  """Gets the name of the Icon2ForceTorqueSensorPart from the resource data.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The part name.

  Raises:
    KeyError: If resource_handle does not include an Icon2ForceTorqueSensorPart
    data.
  """
  icon_force_torque_sensor_part = (
      icon_equipment_pb2.Icon2ForceTorqueSensorPart()
  )
  ft_key = ICON2_FORCE_TORQUE_SENSOR_PART_KEY
  if ft_key not in resource_handle.resource_data:
    raise KeyError(
        "%s is not in resource_handle.resource_data. Available: %r"
        % (ft_key, resource_handle.resource_data.keys())
    )
  resource_handle.resource_data[ft_key].contents.Unpack(
      icon_force_torque_sensor_part
  )
  logging.info(
      "ICON force_torque_sensor_part: %s", icon_force_torque_sensor_part
  )
  return icon_force_torque_sensor_part.part_name


def get_adio_part_name(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> str:
  """Gets the name of the Icon2AdioPart from the resource data.

  Args:
    resource_handle: The resource handle for the adio we want to read/control.

  Returns:
    The part name.

  Raises:
    KeyError: If resource_handle does not include an Icon2AdioPart data.
    ValueError: If adio_part does not include an icon_target data, i.e. a adio
      configuration that uses a different backend than icon.
  """
  adio_key = ICON2_ADIO_PART_KEY
  icon_adio_part = icon_equipment_pb2.Icon2AdioPart()
  if adio_key not in resource_handle.resource_data:
    raise KeyError(
        "%s is not in resource_handle.resource_data. Available: %r"
        % (adio_key, resource_handle.resource_data.keys())
    )
  resource_handle.resource_data[adio_key].contents.Unpack(icon_adio_part)
  if not icon_adio_part.HasField("icon_target"):
    raise ValueError(
        "adio part is not an icon_target and thus does not have a part name."
    )
  return icon_adio_part.icon_target.part_name


def get_rangefinder_part_name(
    resource_handle: resource_handle_pb2.ResourceHandle,
) -> str:
  """Gets the name of the Icon2RangefinderPart from the resource data.

  Args:
    resource_handle: The resource handle for the robot we want to control.

  Returns:
    The part name.

  Raises:
    KeyError: If resource_handle does not include Icon2RangefinderPart data.
  """
  icon_rangefinder_part = icon_equipment_pb2.Icon2RangefinderPart()
  part_key = ICON2_RANGEFINDER_PART_KEY
  if part_key not in resource_handle.resource_data:
    raise KeyError(
        "%s is not in resource_handle.resource_data. Available: %r"
        % (part_key, resource_handle.resource_data.keys())
    )
  if not resource_handle.resource_data[part_key].contents.Unpack(
      icon_rangefinder_part
  ):
    raise ValueError(
        "Failed to unpack %s as 'Icon2RangefinderPart'. Actual type is '%r'"
        % (part_key, icon_rangefinder_part.DESCRIPTOR)
    )

  logging.info("ICON %s: %s", ICON2_RANGEFINDER_PART_KEY, icon_rangefinder_part)
  return icon_rangefinder_part.part_name
