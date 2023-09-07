# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Base camera class wrapping gRPC connection and calls."""
from __future__ import annotations

import datetime
from typing import List, Optional

import grpc
from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.proto import camera_params_pb2
from intrinsic.perception.proto import camera_settings_pb2
from intrinsic.perception.proto import capture_result_pb2
from intrinsic.perception.service.proto import camera_server_pb2
from intrinsic.perception.service.proto import camera_server_pb2_grpc
from intrinsic.util.grpc import connection
from intrinsic.util.grpc import interceptor


class CameraClient:
  """Base camera class wrapping gRPC connection and calls.

  Skill users should use the `Camera` class, which provides a more pythonic
  interface.
  """

  camera_config: camera_config_pb2.CameraConfig
  _camera_stub: camera_server_pb2_grpc.CameraServerStub
  _camera_handle: str

  def __init__(
      self,
      camera_channel: grpc.Channel,
      connection_params: connection.ConnectionParams,
      camera_config: camera_config_pb2.CameraConfig,
  ):
    """Creates a CameraClient object."""
    self.camera_config = camera_config

    # Create stub.
    intercepted_camera_channel = grpc.intercept_channel(
        camera_channel,
        interceptor.HeaderAdderInterceptor(connection_params.headers),
    )
    self._camera_stub = camera_server_pb2_grpc.CameraServerStub(
        intercepted_camera_channel
    )

    # Access a camera instance.
    request = camera_server_pb2.CreateCameraRequest(camera_config=camera_config)
    response = self._camera_stub.CreateCamera(request)
    self._camera_handle = response.camera_handle

    if not self._camera_handle:
      raise RuntimeError("Could not create camera.")

  def describe_camera(
      self,
  ) -> camera_server_pb2.DescribeCameraResponse:
    """Describes the sensors/configurations available for the camera."""
    request = camera_server_pb2.DescribeCameraRequest(
        camera_handle=self._camera_handle
    )
    response = self._camera_stub.DescribeCamera(request)
    return response

  def capture(
      self,
      timeout: Optional[datetime.timedelta] = None,
      sensor_ids: Optional[List[int]] = None,
  ) -> capture_result_pb2.CaptureResult:
    """Captures sensor images from the camera and returns a CaptureResult."""
    request = camera_server_pb2.CaptureRequest(
        camera_handle=self._camera_handle
    )
    if timeout is not None:
      request.timeout.FromTimedelta(timeout)
    if sensor_ids is not None:
      request.sensor_ids[:] = sensor_ids
    response = self._camera_stub.Capture(request)
    return response.capture_result

  def read_camera_setting_properties(
      self,
      name: str,
  ) -> camera_settings_pb2.CameraSettingProperties:
    """Read the properties of a camera setting by name."""
    request = camera_server_pb2.ReadCameraSettingPropertiesRequest(
        camera_handle=self._camera_handle,
        name=name,
    )
    response = self._camera_stub.ReadCameraSettingProperties(request)
    return response.properties

  def read_camera_setting(
      self,
      name: str,
  ) -> camera_settings_pb2.CameraSetting:
    """Read a camera setting by name."""
    request = camera_server_pb2.ReadCameraSettingRequest(
        camera_handle=self._camera_handle,
        name=name,
    )
    response = self._camera_stub.ReadCameraSetting(request)
    return response.setting

  def update_camera_setting(
      self,
      setting: camera_settings_pb2.CameraSetting,
  ) -> None:
    """Update a camera setting."""
    request = camera_server_pb2.UpdateCameraSettingRequest(
        camera_handle=self._camera_handle,
        setting=setting,
    )
    self._camera_stub.UpdateCameraSetting(request)

  def read_camera_params(self) -> camera_params_pb2.CameraParams:
    """Read the camera params."""
    request = camera_server_pb2.ReadCameraParamsRequest(
        camera_handle=self._camera_handle,
    )
    response = self._camera_stub.ReadCameraParams(request)
    return response.camera_params

  def update_camera_params(
      self, camera_params: camera_params_pb2.CameraParams
  ) -> None:
    """Update the camera params."""
    request = camera_server_pb2.UpdateCameraParamsRequest(
        camera_handle=self._camera_handle,
        camera_params=camera_params,
    )
    self._camera_stub.UpdateCameraParams(request)

  def clear_camera_params(self) -> None:
    """Clear the camera params."""
    request = camera_server_pb2.ClearCameraParamsRequest(
        camera_handle=self._camera_handle,
    )
    self._camera_stub.ClearCameraParams(request)
