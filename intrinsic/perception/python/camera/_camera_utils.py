# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Camera misc helper methods."""
from __future__ import annotations

from typing import Optional, Tuple, Type, Union

from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.proto import dimensions_pb2
from intrinsic.perception.proto import distortion_params_pb2
from intrinsic.perception.proto import image_buffer_pb2
from intrinsic.perception.proto import intrinsic_params_pb2
import numpy as np


def extract_identifier(config: camera_config_pb2.CameraConfig) -> Optional[str]:
  """Extract the camera identifier from the camera config."""
  # extract device_id from oneof
  identifier = config.identifier
  camera_driver = identifier.WhichOneof("drivers")
  if camera_driver == "genicam":
    return identifier.genicam.device_id
  elif camera_driver == "openni":
    return identifier.openni.device_id
  elif camera_driver == "v4l":
    return str(identifier.v4l.device_id)
  elif camera_driver == "photoneo":
    return identifier.photoneo.device_id
  elif camera_driver == "realsense":
    return identifier.realsense.device_id
  elif camera_driver == "plenoptic_unit":
    return identifier.plenoptic_unit.device_id
  elif camera_driver == "fake_genicam":
    return "fake_genicam"
  else:
    return None


def image_buffer_shape(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> Tuple[int, int, int]:
  """Returns the shape of the given image buffer."""
  return (
      image_buffer.dimensions.rows,
      image_buffer.dimensions.cols,
      image_buffer.num_channels,
  )


def image_buffer_size(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> int:
  """Returns the number of elements in the given image buffer."""
  return (
      image_buffer.dimensions.rows
      * image_buffer.dimensions.cols
      * image_buffer.num_channels
  )


def deserialize_image_buffer(
    image: Optional[image_buffer_pb2.ImageBuffer],
    dtype: Union[np.dtype, Type[np.generic]],
) -> np.ndarray:
  """Deserializes image from proto format.

  Computes the number of channels per pixel from the total data size, the
  per-channel data type, and the number of pixels.

  Args:
    image: The serialized image.
    dtype: Per-channel data type.

  Returns:
    The unpacked image of size [height, width, num_channels] or none, if the
    input image is none.

  Raises:
    ValueError if the image buffer is compressed.
    ValueError if the buffer size is invalid.
  """
  if not image or not image.data:
    raise ValueError("No image buffer or data provided.")
  if image.encoding != image_buffer_pb2.ENCODING_UNSPECIFIED:
    raise ValueError("Image buffer is compressed")

  buffer = np.frombuffer(image.data, dtype=dtype)
  shape = image_buffer_shape(image)
  size = image_buffer_size(image)

  if buffer.size != size:
    raise ValueError("Invalid buffer size %d != %d" % (buffer.size, size))

  return buffer.reshape(shape)


def extract_dimensions(
    dimensions: dimensions_pb2.Dimensions,
) -> Tuple[int, int]:
  """Extract dimensions into a tuple."""
  return (dimensions.cols, dimensions.rows)


def extract_intrinsic_dimensions(
    ip: intrinsic_params_pb2.IntrinsicParams,
) -> Tuple[int, int]:
  """Extract dimensions from intrinsic params into a tuple."""
  return extract_dimensions(ip.dimensions)


def extract_intrinsic_matrix(
    ip: intrinsic_params_pb2.IntrinsicParams,
) -> np.ndarray:
  """Extract intrinsic matrix from intrinsic params as a numpy array."""
  return np.array([
      [ip.focal_length_x, 0, ip.principal_point_x],
      [0, ip.focal_length_y, ip.principal_point_y],
      [0, 0, 1],
  ])


def extract_distortion_params(
    dp: distortion_params_pb2.DistortionParams,
) -> np.ndarray:
  """Extract distortion parameters from distortion params as a numpy array."""
  if dp.k4 or dp.k5 or dp.k6:
    return np.array([dp.k1, dp.k2, dp.p1, dp.p2, dp.k3, dp.k4, dp.k5, dp.k6])
  else:
    return np.array([dp.k1, dp.k2, dp.p1, dp.p2, dp.k3])
