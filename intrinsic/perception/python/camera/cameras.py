# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Convenience class for Camera use within skills."""
from __future__ import annotations

import datetime
from typing import List, Mapping, Optional, Tuple, Union

from absl import logging
from google.protobuf import empty_pb2
import grpc
from intrinsic.hardware.proto import settings_pb2
from intrinsic.math.python import pose3
from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.proto import camera_params_pb2
from intrinsic.perception.python.camera import camera_client
from intrinsic.perception.python.camera import data_classes
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.python import proto_utils
from intrinsic.skills.python import skill_interface
from intrinsic.util.grpc import connection
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_resources
import numpy as np

_CONFIG_EQUIPMENT_IDENTIFIER = "CameraConfig"
_GRPC_TARGET_EQUIPMENT_IDENTIFIER = "GrpcTarget"


def _unpack_camera_config(
    camera_equipment: equipment_pb2.EquipmentHandle,
) -> Optional[camera_config_pb2.CameraConfig]:
  """Returns the camera config from a camera equipment handle or None if equipment is not a camera."""
  data: Mapping[str, equipment_pb2.EquipmentHandle.EquipmentData] = (
      camera_equipment.equipment_data
  )
  config = None
  if _CONFIG_EQUIPMENT_IDENTIFIER in data:
    config = data[_CONFIG_EQUIPMENT_IDENTIFIER]

  if config is None:
    return None

  try:
    camera_config = camera_config_pb2.CameraConfig()
    proto_utils.unpack_any(config.contents, camera_config)
  except TypeError:
    return None

  return camera_config


def make_camera_equipment_selector() -> equipment_pb2.EquipmentSelector:
  """Creates the default equipment selector for a camera equipment slot.

  Used in a skill's `required_equipment` implementation.

  Returns:
    An equipment selector that is valid for cameras.
  """
  return equipment_pb2.EquipmentSelector(
      equipment_type_names=[
          _GRPC_TARGET_EQUIPMENT_IDENTIFIER,
          _CONFIG_EQUIPMENT_IDENTIFIER,
      ]
  )


class Camera:
  """Convenience class for Camera use within skills.

  This class provides a more pythonic interface than the `CameraClient` which
  wraps the gRPC calls for interacting with cameras.

  Typical usage example:

  - Add a camera slot to the skill, e.g.:
    ```
    @classmethod
    @overrides(skl.Skill)
    def required_equipment(cls) -> Mapping[str,
    equipment_pb2.EquipmentSelector]:
      return {
          camera_slot: cameras.make_camera_equipment_selector()
      }
    ```
  - Create and use a camera in the skill:
    ```
    def execute(
        self, request: skl.ExecuteRequest, context: skl.ExecutionContext
    ) -> skill_service_pb2.ExecuteResult:
    ...

    camera = cameras.Camera.create(request, context, "camera_slot")

    intrinsic_matrix = camera.intrinsic_matrix()

    capture_result = camera.capture()
    for sensor_name, sensor_image in capture_result.sensor_images.items():
      print(sensor_image.array.shape)
    ...
    ```
  """

  _camera_equipment: equipment_pb2.EquipmentHandle
  _world_client: object_world_client.ObjectWorldClient
  _world_object: object_world_resources.WorldObject
  _client: camera_client.CameraClient
  _sensor_id_to_name: Mapping[int, str]

  config: data_classes.CameraConfig
  factory_config: Optional[data_classes.CameraConfig]
  factory_sensor_info: Mapping[str, data_classes.SensorInformation]

  @classmethod
  def create(
      cls, context: skill_interface.ExecutionContext, slot: str
  ) -> Camera:
    """Creates a Camera object from the skill's execution context.

    Args:
      context: The skill's current skill_interface.ExecutionContext.
      slot: The camera slot created in skill's required_equipment
        implementation.

    Returns:
      A connected Camera object with sensor information cached.
    """
    camera_equipment = context.equipment_handles[slot]
    world_client = context.get_object_world()

    return cls(
        camera_equipment=camera_equipment,
        world_client=world_client,
    )

  def __init__(
      self,
      camera_equipment: equipment_pb2.EquipmentHandle,
      world_client: object_world_client.ObjectWorldClient,
  ):
    """Creates a Camera object from the given camera equipment and world.

    Args:
      camera_equipment: The equipment handle with which to connect to the
        camera.
      world_client: The current world client, for camera pose information.

    Raises:
      RuntimeError: If the camera's config could not be parsed from the
      equipment handle.
    """
    self._camera_equipment = camera_equipment
    self._world_client = world_client
    self._world_object = self._world_client.get_object(camera_equipment)
    self._sensor_id_to_name = {}

    # use unlimited message size for receiving images (e.g. -1)
    options = [("grpc.max_receive_message_length", -1)]
    grpc_info = camera_equipment.connection_info.grpc
    camera_channel = grpc.insecure_channel(grpc_info.address, options=options)
    connection_params = connection.ConnectionParams(
        grpc_info.address, grpc_info.server_instance, grpc_info.header
    )

    # parse config
    camera_config = _unpack_camera_config(self._camera_equipment)
    if not camera_config:
      raise RuntimeError("Could not parse camera config from equipment handle.")

    self._client = camera_client.CameraClient(
        camera_channel, connection_params, camera_config
    )

    self.config = data_classes.CameraConfig(camera_config)
    self.factory_config = None
    self.factory_sensor_info = {}

    # attempt to describe cameras to get factory configurations
    try:
      describe_camera_proto = self._client.describe_camera()

      self.factory_config = data_classes.CameraConfig(
          describe_camera_proto.camera_config
      )
      self.factory_sensor_info = {
          sensor_info.display_name: data_classes.SensorInformation(sensor_info)
          for sensor_info in describe_camera_proto.sensors
      }

      # map sensor_ids to human readable sensor names from camera description
      # for capture result
      self._sensor_id_to_name = {
          sensor_info.sensor_id: sensor_name
          for sensor_name, sensor_info in self.factory_sensor_info.items()
      }
    except grpc.RpcError:
      logging.warning("Could not load factory configuration.")

  def capture(
      self,
      timeout: Optional[datetime.timedelta] = None,
      sensor_names: Optional[List[str]] = None,
  ) -> data_classes.CaptureResult:
    """Capture from the camera and return a CaptureResult.

    Args:
      timeout: An optional timeout for the capture operation. If it is None, the
        camera will block until it gets a response.
      sensor_names: An optional list of sensor names that will be transmitted in
        the response, if data was collected for them. This acts as a mask to
        limit the number of transmitted `SensorImage`s. If it is None, all
        `SensorImage`s will be transferred.

    Returns:
      A CaptureResult which contains the selected sensor images.

    Raises:
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      if sensor_names is not None and self.factory_sensor_info:
        sensor_ids = [
            self.factory_sensor_info[sensor_name].sensor_id
            for sensor_name in sensor_names
            if sensor_name in self.factory_sensor_info
        ]
      else:
        sensor_ids = None

      capture_result_proto = self._client.capture(
          timeout=timeout, sensor_ids=sensor_ids
      )
      return data_classes.CaptureResult(
          capture_result_proto, self._sensor_id_to_name, self.world_t_camera
      )
    except grpc.RpcError as e:
      logging.warning("Could not capture from camera.")
      raise e

  def read_camera_setting_properties(
      self,
      name: str,
  ) -> Union[
      settings_pb2.FloatSettingProperties,
      settings_pb2.IntegerSettingProperties,
      settings_pb2.EnumSettingProperties,
  ]:
    """Read the properties of a camera setting by name.

    These settings vary for different types of cameras, but generally conform to
    the GenICam Standard Features Naming
    Convention (SFNC):
    https://www.emva.org/wp-content/uploads/GenICam_SFNC_v2_7.pdf.

    Args:
      name: The setting name.

    Returns:
      The setting properties, which can be used to validate that a particular
      setting is supported.

    Raises:
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      camera_setting_properties_proto = (
          self._client.read_camera_setting_properties(name=name)
      )

      setting_properties = camera_setting_properties_proto.WhichOneof(
          "setting_properties"
      )
      if setting_properties == "float_properties":
        return camera_setting_properties_proto.float_properties
      elif setting_properties == "integer_properties":
        return camera_setting_properties_proto.integer_properties
      elif setting_properties == "enum_properties":
        return camera_setting_properties_proto.enum_properties
      else:
        raise ValueError(
            f"Could not parse setting_properties: {setting_properties}."
        )
    except grpc.RpcError as e:
      logging.warning("Could not read camera setting properties.")
      raise e

  def read_camera_setting(
      self,
      name: str,
  ) -> Union[int, float, bool, str]:
    """Read a camera setting by name.

    These settings vary for different types of cameras, but generally conform to
    the GenICam Standard Features Naming
    Convention (SFNC):
    https://www.emva.org/wp-content/uploads/GenICam_SFNC_v2_7.pdf.

    Args:
      name: The setting name.

    Returns:
      The current camera setting.

    Raises:
      ValueError: if the setting value cannot be parsed.
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      camera_setting_proto = self._client.read_camera_setting(name=name)

      value = camera_setting_proto.WhichOneof("value")
      if value == "integer_value":
        return camera_setting_proto.integer_value
      elif value == "float_value":
        return camera_setting_proto.float_value
      elif value == "bool_value":
        return camera_setting_proto.bool_value
      elif value == "string_value":
        return camera_setting_proto.string_value
      elif value == "enumeration_value":
        return camera_setting_proto.enumeration_value
      elif value == "command_value":
        return "command"
      else:
        raise ValueError(f"Could not parse value: {value}.")
    except grpc.RpcError as e:
      logging.warning("Could not read camera setting.")
      raise e

  def update_camera_setting(
      self,
      name: str,
      value: Union[int, float, bool, str],
  ) -> None:
    """Update a camera setting.

    These settings vary for different types of cameras, but generally conform to
    the GenICam Standard Features Naming
    Convention (SFNC):
    https://www.emva.org/wp-content/uploads/GenICam_SFNC_v2_7.pdf.

    Args:
      name: The setting name.
      value: The desired setting value.

    Raises:
      ValueError: Setting type could not be parsed or value doesn't match type.
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      # Cannot get sufficient type information from just
      # `Union[int, float, bool, str]`, so read the setting first and then
      # update its value.
      setting = self._client.read_camera_setting(name=name)
      value_type = setting.WhichOneof("value")
      if value_type == "integer_value":
        if not isinstance(value, int):
          raise ValueError(f"Expected int value for {name} but got '{value}'")
        setting.integer_value = value
      elif value_type == "float_value":
        # allow int values to be casted to float, but not vice versa
        if isinstance(value, int):
          value = float(value)
        if not isinstance(value, float):
          raise ValueError(f"Expected float value for {name} but got '{value}'")
        setting.float_value = value
      elif value_type == "bool_value":
        if not isinstance(value, bool):
          raise ValueError(f"Expected bool value for {name} but got '{value}'")
        setting.bool_value = value
      elif value_type == "string_value":
        if not isinstance(value, str):
          raise ValueError(
              f"Expected string value for {name} but got '{value}'"
          )
        setting.string_value = value
      elif value_type == "enumeration_value":
        if not isinstance(value, str):
          raise ValueError(
              f"Expected enumeration value string for {name} but got '{value}'"
          )
        setting.enumeration_value = value
      elif value_type == "command_value":
        # no need to check value contents
        setting.command_value = empty_pb2.Empty()
      else:
        raise ValueError(f"Could not parse value: {value_type}.")

      self._client.update_camera_setting(setting=setting)
    except grpc.RpcError as e:
      logging.warning("Could not update camera setting.")
      raise e

  def read_camera_params(self) -> data_classes.CameraParams:
    """Read the camera params.

    Returns:
      The current camera parameters, including the configured resolution, camera
      intrinsics, and optionally distortion parameters if calibrated.

    Raises:
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      camera_params_proto = self._client.read_camera_params()
      return data_classes.CameraParams(camera_params_proto)
    except grpc.RpcError as e:
      logging.warning("Could not read camera params.")
      raise e

  def update_camera_params(
      self, camera_params: camera_params_pb2.CameraParams
  ) -> None:
    """Update the camera params.

    Args:
      camera_params: The desired camera params containing resolution, camera
        intrinsics, and optionally distortion parameters.

    Raises:
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      self._client.update_camera_params(camera_params=camera_params)
    except grpc.RpcError as e:
      logging.warning("Could not update camera params.")
      raise e

  def clear_camera_params(self) -> None:
    """Clear the camera params.

    Raises:
      grpc.RpcError: A gRPC error occurred.
    """
    try:
      self._client.clear_camera_params()
    except grpc.RpcError as e:
      logging.warning("Could not clear camera params.")
      raise e

  @property
  def world_object(self) -> object_world_resources.WorldObject:
    """Camera world object."""
    return self._world_object

  @property
  def world_t_camera(self) -> pose3.Pose3:
    """Camera world pose."""
    return self._world_client.get_transform(
        self._world_client.root, self._world_object
    )

  @property
  def identifier(self) -> Optional[str]:
    """Camera identifier."""
    return self.config.identifier

  @property
  def dimensions(self) -> Optional[Tuple[int, int]]:
    """Camera intrinsic dimensions."""
    return self.config.dimensions

  @property
  def sensor_names(self) -> List[str]:
    """List of sensor names."""
    return list(self.factory_sensor_info.keys())

  @property
  def sensor_ids(self) -> List[int]:
    """List of sensor ids."""
    return [
        sensor_info.sensor_id
        for _, sensor_info in self.factory_sensor_info.items()
    ]

  @property
  def sensor_dimensions(self) -> Mapping[str, Tuple[int, int]]:
    """Mapping of sensor name to the sensor's intrinsic dimensions."""
    return {
        sensor_name: sensor_info.dimensions
        for sensor_name, sensor_info in self.factory_sensor_info.items()
    }

  def camera_t_sensor(self, sensor_name: str) -> Optional[pose3.Pose3]:
    """Get the sensor camera_t_sensor pose, falling back to factory settings if pose is missing from the sensor config.

    Args:
      sensor_name: The desired sensor's name.

    Returns:
      The pose3.Pose3 of the sensor relative to the pose of the camera itself or
      None if it couldn't be found.
    """
    if sensor_name not in self.factory_sensor_info:
      return None
    sensor_info = self.factory_sensor_info[sensor_name]
    sensor_id = sensor_info.sensor_id

    sensor_config = self.config.sensor_configs[sensor_id]

    if sensor_config is not None and sensor_config.camera_t_sensor is not None:
      return sensor_config.camera_t_sensor
    elif sensor_info is not None and sensor_info.camera_t_sensor is not None:
      return sensor_info.camera_t_sensor
    else:
      return None

  def world_t_sensor(self, sensor_name: str) -> Optional[pose3.Pose3]:
    """Get the sensor world_t_sensor pose, falling back to factory settings for camera_t_sensor if pose is missing from the sensor config.

    Args:
      sensor_name: The desired sensor's name.

    Returns:
      The pose3.Pose3 of the sensor relative to the pose of the world or None if
      it couldn't be found.
    """
    camera_t_sensor = self.camera_t_sensor(sensor_name)
    if camera_t_sensor is None:
      return None
    return self.world_t_camera.multiply(camera_t_sensor)

  def intrinsic_matrix(
      self, sensor_name: Optional[str] = None
  ) -> Optional[np.ndarray]:
    """Get the camera intrinsic matrix or that of a specific sensor (for multisensor cameras), falling back to factory settings or the camera intrinsic matrix if intrinsic params are missing from the requested sensor config.

    Args:
      sensor_name: The desired sensor name, or None for the camera intrinsic
        matrix.

    Returns:
      The sensor's intrinsic matrix or None if it couldn't be found.
    """
    if sensor_name is None:
      return self.config.intrinsic_matrix

    if sensor_name not in self.factory_sensor_info:
      return None
    sensor_info = self.factory_sensor_info[sensor_name]
    sensor_id = sensor_info.sensor_id

    sensor_config = self.config.sensor_configs[sensor_id]

    if sensor_config is not None and sensor_config.intrinsic_matrix is not None:
      return sensor_config.intrinsic_matrix
    elif (
        sensor_info is not None
        and sensor_info.factory_intrinsic_matrix is not None
    ):
      return sensor_info.factory_intrinsic_matrix
    else:
      return self.config.intrinsic_matrix

  def distortion_params(
      self, sensor_name: Optional[str] = None
  ) -> Optional[np.ndarray]:
    """Get the camera distortion params or that of a specific sensor (for multisensor cameras), falling back to factory settings if distortion params are missing from the sensor config.

    Args:
      sensor_name: The desired sensor name, or None for the camera distortion
        params.

    Returns:
      The distortion params (k1, k2, p1, p2, k3, [k4, k5, k6]) or None if it
      couldn't be found.
    """
    if sensor_name is None:
      return self.config.distortion_params

    if sensor_name not in self.factory_sensor_info:
      return None
    sensor_info = self.factory_sensor_info[sensor_name]
    sensor_id = sensor_info.sensor_id

    sensor_config = self.config.sensor_configs[sensor_id]

    if (
        sensor_config is not None
        and sensor_config.distortion_params is not None
    ):
      return sensor_config.distortion_params
    elif (
        sensor_info is not None
        and sensor_info.factory_distortion_params is not None
    ):
      return sensor_info.factory_distortion_params
    else:
      return self.config.distortion_params
