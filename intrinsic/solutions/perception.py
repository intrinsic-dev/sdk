# Copyright 2023 Intrinsic Innovation LLC

"""Camera access within the workcell API."""

import datetime
import math
from typing import Mapping, Optional, Tuple, cast

import grpc
from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.python.camera import data_classes
from intrinsic.perception.service.proto import camera_server_pb2
from intrinsic.perception.service.proto import camera_server_pb2_grpc
from intrinsic.resources.client import resource_registry_client
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.solutions import camera_utils
from intrinsic.solutions import deployments
from intrinsic.solutions import execution
from intrinsic.util.grpc import connection
from intrinsic.util.grpc import error_handling
from intrinsic.util.grpc import interceptor
import matplotlib.pyplot as plt
import numpy as np


# On the guitar cluster grabbing a frame can take more than 7s; if another
# camera is rendering as well this time can go up 16s. To be on the safe side
# the timeout is set to a high value.
# Since frame grabbing tends to timeout on overloaded guitar clusters we
# increase this value even further.
_MAX_FRAME_WAIT_TIME_SECONDS = 120
_CONFIG_EQUIPMENT_IDENTIFIER_DEPRECATED = 'Config'
_CONFIG_EQUIPMENT_IDENTIFIER = 'CameraConfig'
_MIN_DEPTH_METERS = 0.0
_MAX_DEPTH_METERS = 2.0  # Reasonable assumption for our current depth cameras.
_PLOT_WIDTH_INCHES = 40
_PLOT_HEIGHT_INCHES = 20


def _get_camera_config(
    data: Mapping[str, resource_handle_pb2.ResourceHandle.ResourceData],
) -> Optional[camera_config_pb2.CameraConfig]:
  """Returns camera config, or None if resource is not a camera."""
  config = None
  if _CONFIG_EQUIPMENT_IDENTIFIER in data:
    config = data[_CONFIG_EQUIPMENT_IDENTIFIER]
  elif _CONFIG_EQUIPMENT_IDENTIFIER_DEPRECATED in data:
    config = data[_CONFIG_EQUIPMENT_IDENTIFIER_DEPRECATED]
  if config is None:
    return None
  camera_config = camera_config_pb2.CameraConfig()
  if not config.contents.Unpack(camera_config):
    return None
  return camera_config


class Camera:
  """Convenience wrapper for Camera."""

  _stub: camera_server_pb2_grpc.CameraServerStub
  _handle: Optional[str]
  _resource_id: str
  _resource_registry: resource_registry_client.ResourceRegistryClient
  _executive: execution.Executive
  _is_simulated: bool

  def __init__(
      self,
      channel: grpc.Channel,
      handle: resource_handle_pb2.ResourceHandle,
      resource_registry: resource_registry_client.ResourceRegistryClient,
      executive: execution.Executive,
      is_simulated: bool,
  ):
    """Creates a Camera object.

    During construction the camera is not yet open. Opening the camera on the
    camera server will happen once it's needed: first, the current camera
    config will be requested from the resource registry, then, the camera
    handle will be created on the camera server.

    Args:
      channel: The grpc channel to the respective camera server.
      handle: Resource handle for the camera.
      resource_registry: Resource registry to fetch camera resources from.
      executive: The executive for checking the state.
      is_simulated: Whether or not the world is being simulated.
    """
    grpc_info = handle.connection_info.grpc
    connection_params = connection.ConnectionParams(
        grpc_info.address, grpc_info.server_instance, grpc_info.header
    )
    intercepted_channel = grpc.intercept_channel(
        channel, interceptor.HeaderAdderInterceptor(connection_params.headers)
    )
    stub = camera_server_pb2_grpc.CameraServerStub(intercepted_channel)

    self._stub = stub
    self._handle = None
    self._resource_id = handle.name
    self._resource_registry = resource_registry
    self._executive = executive
    self._is_simulated = is_simulated

  def get_frame(
      self,
      timeout: datetime.timedelta = datetime.timedelta(
          seconds=_MAX_FRAME_WAIT_TIME_SECONDS
      ),
      skip_undistortion: bool = False,
  ) -> camera_utils.Frame:
    """Performs grpc request to retrieve a frame from the camera.

    If the camera handle is no longer valid (eg, if the server returns a
    NOT_FOUND status), the camera will be reopened (once) on the camera server;
    if re-opening the camera fails an exception is raised.

    Args:
      timeout: Timeout duration for GetFrame() service calls.
      skip_undistortion: If set to true the returned frame will be distorted.

    Returns:
      The acquired frame.

    Raises:
      grpc.RpcError from the camera or resource service.
    """
    if self._is_simulated:
      try:
        _ = self._executive.operation
      except execution.OperationNotFoundError:
        print(
            'Note: The image could be showing an outdated simulation state. Run'
            ' `simulation.reset()` to resolve this.'
        )

    deadline = datetime.datetime.now() + timeout
    if not self._handle:
      self._reinitialize_from_resources(deadline)

    get_frame_func = lambda: self._get_frame(deadline, skip_undistortion)
    try:
      response = get_frame_func()
    except grpc.RpcError as e:
      if cast(grpc.Call, e).code() != grpc.StatusCode.NOT_FOUND:
        raise
      # If the camera was not found, recreate the camera. This can happen when
      # switching between sim/real or when a service restarts.
      self._reinitialize_from_resources(deadline)
      response = get_frame_func()
    return camera_utils.Frame(response.frame)

  def show_rgb_frame(self) -> None:
    """Acquires and plots frame."""
    frame = self.get_frame()
    plt.imshow(frame.rgb8u)
    plt.axis('off')

  def show_depth_frame(self) -> None:
    """Acquires and plots depth frame."""
    frame = self.get_frame()
    img = np.squeeze(frame.depth32f)
    plt.imshow(
        img, cmap='copper', vmin=_MIN_DEPTH_METERS, vmax=_MAX_DEPTH_METERS
    )
    plt.axis('off')

  def capture(
      self,
      timeout: datetime.timedelta = datetime.timedelta(
          seconds=_MAX_FRAME_WAIT_TIME_SECONDS
      ),
      sensor_ids: Optional[list[int]] = None,
  ) -> data_classes.CaptureResult:
    """Performs grpc request to capture sensor images from the camera.

    If the camera handle is no longer valid (eg, if the server returns a
    NOT_FOUND status), the camera will be reopened (once) on the camera server;
    if re-opening the camera fails an exception is raised.

    Args:
      timeout: Timeout duration for Capture() service calls.
      sensor_ids: List of selected sensor identifiers for Capture() service
        calls.

    Returns:
      The acquired list of sensor images.

    Raises:
      grpc.RpcError from the camera or resource service.
    """

    if self._is_simulated:
      try:
        _ = self._executive.operation
      except execution.OperationNotFoundError:
        print(
            'Note: The image could be showing an outdated simulation state. Run'
            ' `simulation.reset()` to resolve this.'
        )

    deadline = datetime.datetime.now() + timeout
    if not self._handle:
      self._reinitialize_from_resources(deadline)

    sensor_ids = sensor_ids or []
    try:
      response = self._capture(deadline, sensor_ids)
    except grpc.RpcError as e:
      if cast(grpc.Call, e).code() != grpc.StatusCode.NOT_FOUND:
        raise
      # If the camera was not found, recreate the camera. This can happen when
      # switching between sim/real or when a service restarts.
      self._reinitialize_from_resources(deadline)
      response = self._capture(deadline, sensor_ids)
    return data_classes.CaptureResult(response.capture_result)

  def show_capture(
      self,
      figsize: Tuple[float, float] = (_PLOT_WIDTH_INCHES, _PLOT_HEIGHT_INCHES),
  ) -> None:
    """Acquires and plots all sensor images from a capture call in a grid plot.

    Args:
      figsize: Size of grid plot. It is defined as a (width, height) tuple with
        the dimensions in inches.
    """
    capture_result = self.capture()
    fig = plt.figure(figsize=figsize)
    nrows = math.ceil(len(capture_result.sensor_images) / 2)
    ncols = 2

    for i, sensor_image in enumerate(capture_result.sensor_images.values()):
      # The first half sensor images are shown on the left side of the plot grid
      # and the second half on the right side.
      if i < nrows:
        fig.add_subplot(nrows, ncols, 2 * i + 1)
      else:
        fig.add_subplot(nrows, ncols, 2 * (i % nrows) + 2)

      if sensor_image.shape[-1] == 1:
        plt.imshow(sensor_image.array, cmap='gray')
      else:
        plt.imshow(sensor_image.array)
      plt.axis('off')
      plt.title(f'Sensor {sensor_image.sensor_id}')

  def _reinitialize_from_resources(self, deadline: datetime.datetime) -> None:
    """Create camera handle from resources."""
    handle = self._resource_registry.get_resource_instance(
        self._resource_id
    ).resource_handle
    request = camera_server_pb2.CreateCameraRequest()
    config = _get_camera_config(handle.resource_data)
    if config is None:
      raise ValueError(
          'CameraConfig not found in resource handle %s' % self._resource_id
      )
    request.camera_config.CopyFrom(config)
    response = self._create_camera(request, deadline)
    self._handle = response.camera_handle

  @error_handling.retry_on_grpc_unavailable
  def _get_frame(
      self,
      deadline: datetime.datetime,
      skip_undistortion: bool,
  ) -> camera_server_pb2.GetFrameResponse:
    """Grabs and returns frame from camera service."""
    timeout = deadline - datetime.datetime.now()
    if timeout <= datetime.timedelta(seconds=0):
      raise grpc.RpcError(grpc.StatusCode.DEADLINE_EXCEEDED)
    request = camera_server_pb2.GetFrameRequest()
    request.camera_handle = self._handle
    request.timeout.FromTimedelta(timeout)
    if skip_undistortion:
      request.post_processing.skip_undistortion = True
    response, _ = self._stub.GetFrame.with_call(
        request, timeout=timeout.seconds
    )
    return response

  @error_handling.retry_on_grpc_unavailable
  def _capture(
      self, deadline: datetime.datetime, sensor_ids: list[int]
  ) -> camera_server_pb2.CaptureResponse:
    """Grabs and returns frame from camera service."""
    timeout = deadline - datetime.datetime.now()
    if timeout <= datetime.timedelta(seconds=0):
      raise grpc.RpcError(grpc.StatusCode.DEADLINE_EXCEEDED)
    request = camera_server_pb2.CaptureRequest()
    request.camera_handle = self._handle
    request.timeout.FromTimedelta(timeout)
    request.sensor_ids[:] = sensor_ids
    response, _ = self._stub.Capture.with_call(request, timeout=timeout.seconds)
    return response

  @error_handling.retry_on_grpc_unavailable
  def _create_camera(
      self,
      request: camera_server_pb2.CreateCameraRequest,
      deadline: datetime.datetime,
  ) -> camera_server_pb2.CreateCameraResponse:
    """Creates and returns camera from camera service."""
    timeout = deadline - datetime.datetime.now()
    if timeout <= datetime.timedelta(seconds=0):
      raise grpc.RpcError(grpc.StatusCode.DEADLINE_EXCEEDED)
    response, _ = self._stub.CreateCamera.with_call(
        request, timeout=timeout.seconds
    )
    return response


def _create_cameras(
    resource_registry: resource_registry_client.ResourceRegistryClient,
    grpc_channel: grpc.Channel,
    executive: execution.Executive,
    is_simulated: bool,
) -> dict[str, Camera]:
  """Creates cameras for each resource handle that is a camera.

  Please note that the cameras are not opened directly on the camera service.
  The CreateCamera request is delayed until first use of get_frame.

  Args:
    resource_registry: Resource registry to fetch camera resources from.
    grpc_channel: Channel to the camera service.
    executive: The executive for checking the state.
    is_simulated: Whether or not the world is being simulated.

  Returns:
    A dict with camera handles keyed by camera name.

  Raises:
      status.StatusNotOk: If the grpc request failed (propagates grpc error).
  """
  cameras = {}
  for handle in resource_registry.list_all_resource_handles():
    if _get_camera_config(handle.resource_data) is None:
      continue

    cameras[handle.name] = Camera(
        channel=grpc_channel,
        handle=handle,
        resource_registry=resource_registry,
        executive=executive,
        is_simulated=is_simulated,
    )
  return cameras


class Cameras:
  """Convenience wrapper for camera access."""

  _cameras: dict[str, Camera]

  def __init__(
      self,
      resource_registry: resource_registry_client.ResourceRegistryClient,
      grpc_channel: grpc.Channel,
      executive: execution.Executive,
      is_simulated: bool,
  ):
    """Initializes camera handles for all camera resources.

    Note that grpc calls are performed in this constructor.

    Args:
      resource_registry: Resource registry to fetch camera resources from.
      grpc_channel: Channel to the camera grpc service.
      executive: The executive for checking the state.
      is_simulated: Whether or not the world is being simulated.

    Raises:
      status.StatusNotOk: If the grpc request failed (propagates grpc error).
    """
    self._cameras = _create_cameras(
        resource_registry, grpc_channel, executive, is_simulated
    )

  @classmethod
  def for_solution(cls, solution: deployments.Solution) -> 'Cameras':
    """Creates a Cameras instance for the given Solution.

    Args:
      solution: The deployed solution.

    Returns:
      The new Cameras instance.
    """
    resource_registry = resource_registry_client.ResourceRegistryClient.connect(
        solution.grpc_channel
    )

    return cls(
        resource_registry=resource_registry,
        grpc_channel=solution.grpc_channel,
        executive=solution.executive,
        is_simulated=solution.is_simulated,
    )

  def __getitem__(self, camera_name: str) -> Camera:
    """Returns camera wrapper for the specified identifier.

    Args:
      camera_name: Unique identifier of the camera.

    Returns:
      A camera wrapper object that contains a handle to the camera.

    Raises:
      KeyError: if there is no camera with available with the given name.
    """
    return self._cameras[camera_name]

  def __getattr__(self, camera_name: str) -> Camera:
    """Returns camera wrapper for the specified identifier.

    Args:
      camera_name: Unique identifier of the camera.

    Returns:
      A camera wrapper object that contains a handle to the camera.

    Raises:
      AttributeError: if there is no camera with available with the given name.
    """
    if camera_name not in self._cameras:
      raise AttributeError(f'Camera {camera_name} is unknown.')
    return self._cameras[camera_name]

  def __len__(self) -> int:
    """Returns the number of cameras."""
    return len(self._cameras)

  def __str__(self) -> str:
    """Concatenates all camera keys into a string."""
    return '\n'.join(self._cameras.keys())

  def __dir__(self) -> list[str]:
    """Lists all cameras by key (sorted)."""
    return sorted(self._cameras.keys())
