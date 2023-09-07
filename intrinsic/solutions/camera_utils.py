# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Utility functions to work with image frames."""

import base64
import io
from typing import Any, Optional, Type, Union

from intrinsic.perception.proto import frame_pb2
from intrinsic.perception.proto import image_buffer_pb2
import matplotlib.pyplot as plt
import numpy as np


def _deserialize_image(
    image: Optional[image_buffer_pb2.ImageBuffer],
    dtype: Union[np.dtype, Type[np.generic]],
) -> Optional[np.ndarray]:
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
    return None
  if image.encoding != image_buffer_pb2.ENCODING_UNSPECIFIED:
    raise ValueError('Image buffer is compressed')

  buffer = np.frombuffer(image.data, dtype=dtype)
  num_items = image.dimensions.cols * image.dimensions.rows * image.num_channels
  if buffer.size != num_items:
    raise ValueError('Invalid buffer size %d != %d' % (buffer.size, num_items))

  return buffer.reshape(
      image.dimensions.rows, image.dimensions.cols, image.num_channels
  )


class Frame:
  """A frame with optional channels; mirrors the perception.Frame.

  Attributes:
    rgb8u: Color image. Optional.
    depth32f: Depth image. Optional.
    acquisition_time: Timestamp when this frame was taken.
    camera_params: Intrinsic and distortion parameters.
  """

  def __init__(self, frame: frame_pb2.Frame):
    """Initializes a frame from a proto.

    Args:
      frame: The proto representation of a frame.
    """
    self.rgb8u = _deserialize_image(frame.rgb8u, np.uint8)
    self.depth32f = _deserialize_image(frame.depth32f, np.float32)
    self.acquisition_time = frame.acquisition_time
    self.camera_params = frame.camera_params

  def proto(self) -> frame_pb2.Frame:
    """Converts frame to proto (uncompressed)."""
    frame = frame_pb2.Frame()
    frame.acquisition_time.CopyFrom(self.acquisition_time)
    frame.camera_params.CopyFrom(self.camera_params)
    if self.rgb8u is not None:
      (frame.rgb8u.dimensions.rows, frame.rgb8u.dimensions.cols) = (
          self.rgb8u.shape[0:2]
      )
      frame.rgb8u.pixel_type = image_buffer_pb2.PixelType.PIXEL_INTENSITY
      frame.rgb8u.num_channels = 3
      frame.rgb8u.data = self.rgb8u.tobytes()
      frame.rgb8u.encoding = image_buffer_pb2.ENCODING_UNSPECIFIED
      frame.rgb8u.type = image_buffer_pb2.TYPE_8U
    if self.depth32f is not None:
      (frame.depth32f.dimensions.rows, frame.depth32f.dimensions.cols) = (
          self.depth32f.shape[0:2]
      )
      frame.depth32f.pixel_type = image_buffer_pb2.PixelType.PIXEL_DEPTH
      frame.depth32f.num_channels = 1
      frame.depth32f.data = self.depth32f.tobytes()
      frame.depth32f.encoding = image_buffer_pb2.ENCODING_UNSPECIFIED
      frame.depth32f.type = image_buffer_pb2.TYPE_32F
    return frame


def get_frame_from_any(value: Any) -> Frame:
  """Converts proto representation into Frame (if possible).

  Args:
    value: The proto value to be converted into a Frame

  Returns:
    The frame.

  Raises:
    ValueError if the image frame cannot be decoded
  """
  try:
    frame = frame_pb2.Frame()
    frame.ParseFromString(value.value)
    return Frame(frame)
  except Exception as exc:
    raise ValueError('Cannot decode attached image frame.') from exc


def get_encoded_frame(frame: Frame) -> str:
  """Takes frame and returns an encoded, embeddable string of that frame.

  Args:
    frame: The frame to encode

  Returns:
    The encoded frame.
  """
  tmp_file = io.BytesIO()
  if frame.rgb8u is not None:
    plt.imshow(frame.rgb8u)
  plt.axis('off')
  plt.savefig(tmp_file)
  plt.close()

  return base64.b64encode(tmp_file.getbuffer()).decode('ascii')  # pytype: disable=wrong-arg-types
