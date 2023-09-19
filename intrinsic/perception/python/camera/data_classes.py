# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Common camera data classes."""
from __future__ import annotations

import datetime
from typing import Dict, List, Mapping, Optional, Tuple

from intrinsic.math.python import pose3
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.proto import camera_params_pb2
from intrinsic.perception.proto import capture_result_pb2
from intrinsic.perception.proto import sensor_config_pb2
from intrinsic.perception.proto import sensor_image_pb2
from intrinsic.perception.python import image_utils
from intrinsic.perception.python.camera import _camera_utils
from intrinsic.perception.service.proto import camera_server_pb2
import numpy as np


class CameraParams:
  """Convenience wrapper for CameraParams."""

  _proto: camera_params_pb2.CameraParams

  def __init__(self, camera_params: camera_params_pb2.CameraParams):
    if camera_params is None:
      raise ValueError("CameraParams cannot be None.")

    self._proto = camera_params

  @property
  def proto(self) -> camera_params_pb2.CameraParams:
    """Returns the camera params proto."""
    return self._proto

  @property
  def dimensions(self) -> Tuple[int, int]:
    """Camera intrinsic dimensions (width, height)."""
    ip = self._proto.intrinsic_params
    return _camera_utils.extract_intrinsic_dimensions(ip)

  @property
  def intrinsic_matrix(self) -> np.ndarray:
    """Camera intrinsic matrix."""
    ip = self._proto.intrinsic_params
    return _camera_utils.extract_intrinsic_matrix(ip)

  @property
  def distortion_params(self) -> Optional[np.ndarray]:
    """Camera distortion params; (k1, k2, p1, p2, k3, [k4, k5, k6]) or None."""
    dp = self._proto.distortion_params
    if dp is None:
      return None
    return _camera_utils.extract_distortion_params(dp)


class SensorInformation:
  """Convenience wrapper for SensorInformation."""

  _proto: camera_server_pb2.SensorInformation

  def __init__(self, sensor_information: camera_server_pb2.SensorInformation):
    if sensor_information is None:
      raise ValueError("Sensor information cannot be None.")

    self._proto = sensor_information

  @property
  def proto(self) -> camera_server_pb2.SensorInformation:
    """Returns the sensor information proto."""
    return self._proto

  @property
  def sensor_id(self) -> int:
    """Sensor id."""
    return self._proto.id

  @property
  def display_name(self) -> str:
    """Sensor name."""
    return self._proto.display_name

  @property
  def factory_intrinsic_matrix(self) -> Optional[np.ndarray]:
    """Sensor factory intrinsic matrix."""
    ip = self._proto.factory_intrinsic_params
    if ip is None:
      return None
    return _camera_utils.extract_intrinsic_matrix(ip)

  @property
  def factory_distortion_params(self) -> Optional[np.ndarray]:
    """Sensor factory distortion params; (k1, k2, p1, p2, k3, [k4, k5, k6]) or None."""
    dp = self._proto.factory_distortion_params
    if dp is None:
      return None
    return _camera_utils.extract_distortion_params(dp)

  @property
  def camera_t_sensor(self) -> Optional[pose3.Pose3]:
    """Camera to sensor pose."""
    if self._proto.camera_t_sensor is None:
      return None
    return math_proto_conversion.pose_from_proto(self._proto.camera_t_sensor)

  @property
  def dimensions(self) -> Tuple[int, int]:
    """Sensor dimensions (width, height)."""
    dimensions = self._proto.dimensions
    return _camera_utils.extract_dimensions(dimensions)


class SensorConfig:
  """Convenience wrapper for SensorConfig."""

  _proto: sensor_config_pb2.SensorConfig

  def __init__(self, sensor_config: sensor_config_pb2.SensorConfig):
    if sensor_config is None:
      raise ValueError("Sensor config cannot be None.")

    self._proto = sensor_config

  @property
  def proto(self) -> sensor_config_pb2.SensorConfig:
    """Returns the sensor config proto."""
    return self._proto

  @property
  def sensor_id(self) -> int:
    """Sensor id."""
    return self._proto.id

  @property
  def camera_t_sensor(self) -> Optional[pose3.Pose3]:
    """Camera to sensor pose."""
    if self._proto.camera_t_sensor is None:
      return None
    return math_proto_conversion.pose_from_proto(self._proto.camera_t_sensor)

  @property
  def dimensions(self) -> Optional[Tuple[int, int]]:
    """Sensor intrinsic dimensions (width, height)."""
    ip = self._proto.intrinsic_params
    if ip is None:
      return None
    return _camera_utils.extract_intrinsic_dimensions(ip)

  @property
  def intrinsic_matrix(self) -> Optional[np.ndarray]:
    """Sensor intrinsic matrix."""
    ip = self._proto.intrinsic_params
    if ip is None:
      return None
    return _camera_utils.extract_intrinsic_matrix(ip)

  @property
  def distortion_params(self) -> Optional[np.ndarray]:
    """Sensor distortion params; (k1, k2, p1, p2, k3, [k4, k5, k6]) or None."""
    dp = self._proto.distortion_params
    if dp is None:
      return None
    return _camera_utils.extract_distortion_params(dp)


class CameraConfig:
  """Convenience wrapper for CameraConfig."""

  _proto: camera_config_pb2.CameraConfig

  sensor_configs: Mapping[int, SensorConfig]

  def __init__(self, camera_config: camera_config_pb2.CameraConfig):
    if camera_config is None:
      raise ValueError("Camera config cannot be None.")

    self._proto = camera_config
    self.sensor_configs = {
        sensor_config.id: SensorConfig(sensor_config)
        for sensor_config in self._proto.sensor_configs
    }

  @property
  def proto(self) -> camera_config_pb2.CameraConfig:
    """Returns the camera config proto."""
    return self._proto

  @property
  def identifier(self) -> Optional[str]:
    """Camera identifier."""
    return _camera_utils.extract_identifier(self._proto)

  @property
  def dimensions(self) -> Optional[Tuple[int, int]]:
    """Camera intrinsic dimensions (width, height)."""
    ip = self._proto.intrinsic_params
    if ip is None:
      return None
    return _camera_utils.extract_intrinsic_dimensions(ip)

  @property
  def intrinsic_matrix(self) -> Optional[np.ndarray]:
    """Camera intrinsic matrix."""
    ip = self._proto.intrinsic_params
    if ip is None:
      return None
    return _camera_utils.extract_intrinsic_matrix(ip)

  @property
  def distortion_params(self) -> Optional[np.ndarray]:
    """Camera distortion params; (k1, k2, p1, p2, k3, [k4, k5, k6]) or None."""
    dp = self._proto.distortion_params
    if dp is None:
      return None
    return _camera_utils.extract_distortion_params(dp)


class SensorImage:
  """Convenience wrapper for SensorImage."""

  _proto: sensor_image_pb2.SensorImage
  _sensor_name: str
  _sensor_image_buffer: np.ndarray
  _world_t_camera: Optional[pose3.Pose3]

  config: SensorConfig

  def __init__(
      self,
      sensor_image: sensor_image_pb2.SensorImage,
      sensor_name: str,
      world_t_camera: Optional[pose3.Pose3] = None,
  ):
    """Creates a SensorImage object."""
    if sensor_image is None:
      raise ValueError("Sensor image cannot be None.")
    if sensor_image.buffer is None:
      raise ValueError("Sensor image buffer cannot be None.")

    self._proto = sensor_image
    self._sensor_name = sensor_name
    self._world_t_camera = world_t_camera

    try:
      if not self._proto.buffer:
        raise ValueError("No image buffer provided.")

      buffer = image_utils.deserialize_image_buffer(self._proto.buffer)
      self._sensor_image_buffer = buffer
    except ValueError as e:
      raise ValueError("Could not deserialize sensor image buffer.") from e

    self.config = SensorConfig(self._proto.sensor_config)

  @property
  def proto(self) -> sensor_image_pb2.SensorImage:
    """Returns the sensor image proto."""
    return self._proto

  @property
  def sensor_id(self) -> int:
    """Sensor id."""
    return self.config.sensor_id

  @property
  def sensor_name(self) -> str:
    """Sensor name."""
    return self._sensor_name

  @property
  def camera_t_sensor(self) -> Optional[pose3.Pose3]:
    """Sensor pose relative to camera."""
    return self.config.camera_t_sensor

  @property
  def world_t_sensor(self) -> Optional[pose3.Pose3]:
    """Sensor world pose."""
    if self._world_t_camera is None or self.camera_t_sensor is None:
      return None
    return self._world_t_camera.multiply(self.camera_t_sensor)

  @property
  def dimensions(self) -> Optional[Tuple[int, int]]:
    """Sensor intrinsic dimensions (width, height)."""
    return self.config.dimensions

  @property
  def intrinsic_matrix(self) -> Optional[np.ndarray]:
    """Sensor intrinsic matrix."""
    return self.config.intrinsic_matrix

  @property
  def distortion_params(self) -> Optional[np.ndarray]:
    """Sensor distortion params; (k1, k2, p1, p2, k3, [k4, k5, k6]) or None."""
    return self.config.distortion_params

  @property
  def capture_at(self) -> datetime.datetime:
    """Returns the capture time of the sensor image."""
    return self._proto.acquisition_time.ToDatetime()

  @property
  def array(self) -> np.ndarray:
    """Converts the sensor image to a numpy array."""
    return self._sensor_image_buffer

  @property
  def shape(self) -> Tuple[int, int, int]:
    """Returns the shape of the sensor image."""
    return self._sensor_image_buffer.shape


class CaptureResult:
  """Convenience wrapper for CaptureResult."""

  _proto: capture_result_pb2.CaptureResult
  _sensor_names: Optional[Mapping[int, str]]
  _sensor_images: Dict[str, SensorImage]

  def __init__(
      self,
      capture_result: capture_result_pb2.CaptureResult,
      sensor_names: Optional[Mapping[int, str]] = None,
      world_t_camera: Optional[pose3.Pose3] = None,
  ):
    """Creates a CaptureResult object."""
    if capture_result is None:
      raise ValueError("Capture result cannot be None.")
    if not capture_result.sensor_images:
      raise ValueError("Capture result does not contain any sensor images.")

    self._proto = capture_result
    self._sensor_names = sensor_names
    self._sensor_images = {}

    # insert items ordered by sensor_id, since dictionaries preserve insertion
    # order
    sensor_images_by_id = sorted(
        self._proto.sensor_images,
        key=lambda sensor_image: sensor_image.sensor_config.id,
    )
    for sensor_image in sensor_images_by_id:
      sensor_id = sensor_image.sensor_config.id
      sensor_name_or_id = (
          self._sensor_names[sensor_id]
          if self._sensor_names is not None and sensor_id in self._sensor_names
          else str(sensor_id)
      )
      self._sensor_images[sensor_name_or_id] = SensorImage(
          sensor_image, sensor_name_or_id, world_t_camera
      )

  @property
  def proto(self) -> capture_result_pb2.CaptureResult:
    """Returns the capture result proto."""
    return self._proto

  @property
  def capture_at(self) -> datetime.datetime:
    """Returns the capture time of the capture result."""
    return self._proto.capture_at.ToDatetime()

  @property
  def sensor_names(self) -> List[str]:
    """Returns the sensor names from the capture result."""
    return list(self._sensor_images.keys())

  @property
  def sensor_images(self) -> Mapping[str, SensorImage]:
    """Returns the sensor images from the capture result."""
    return self._sensor_images

  @property
  def sensor_image_buffers(self) -> Mapping[str, np.ndarray]:
    """Returns the sensor images from the capture result as numpy arrays."""
    return {
        sensor_name: sensor_image.array
        for sensor_name, sensor_image in self._sensor_images.items()
    }
