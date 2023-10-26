# Copyright 2023 Intrinsic Innovation LLC

"""Miscellaneous image helper methods."""

import io
from typing import Optional, Tuple, Type, Union

from intrinsic.perception.proto import image_buffer_pb2
import numpy as np
from PIL import Image


def _image_buffer_data_type(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> Union[np.dtype, Type[np.generic]]:
  """Returns the data type of the given image buffer."""
  data_type = image_buffer.type
  if data_type == image_buffer_pb2.DataType.TYPE_8U:
    return np.uint8
  elif data_type == image_buffer_pb2.DataType.TYPE_16U:
    return np.uint16
  elif data_type == image_buffer_pb2.DataType.TYPE_32U:
    return np.uint32
  elif data_type == image_buffer_pb2.DataType.TYPE_8S:
    return np.int8
  elif data_type == image_buffer_pb2.DataType.TYPE_16S:
    return np.int16
  elif data_type == image_buffer_pb2.DataType.TYPE_32S:
    return np.int32
  elif data_type == image_buffer_pb2.DataType.TYPE_32F:
    return np.float32
  elif data_type == image_buffer_pb2.DataType.TYPE_64F:
    return np.float64
  else:
    raise ValueError(f"Data type not supported: {data_type}.")


def _image_buffer_encoding(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> Optional[str]:
  """Returns the encoding of the given image buffer."""
  encoding = image_buffer.encoding
  if encoding == image_buffer_pb2.ENCODING_UNSPECIFIED:
    return None
  elif encoding == image_buffer_pb2.ENCODING_JPEG:
    return "JPEG"
  elif encoding == image_buffer_pb2.ENCODING_PNG:
    return "PNG"
  elif encoding == image_buffer_pb2.ENCODING_WEBP:
    return "WEBP"
  else:
    raise ValueError(
        f"Encoding not supported: {image_buffer_pb2.Encoding.Name(encoding)}."
    )


def _image_buffer_decoded(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> np.ndarray:
  encoding = _image_buffer_encoding(image_buffer)
  if encoding is None:
    return np.frombuffer(
        image_buffer.data, dtype=_image_buffer_data_type(image_buffer)
    )
  else:
    return np.asarray(
        Image.open(io.BytesIO(image_buffer.data), formats=[encoding])
    )


def _image_buffer_shape(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> Union[Tuple[int, int], Tuple[int, int, int]]:
  """Returns the shape of the given image buffer."""
  if image_buffer.num_channels == 1:
    return (
        image_buffer.dimensions.rows,
        image_buffer.dimensions.cols,
    )
  else:
    return (
        image_buffer.dimensions.rows,
        image_buffer.dimensions.cols,
        image_buffer.num_channels,
    )


def _image_buffer_size(
    image_buffer: image_buffer_pb2.ImageBuffer,
) -> int:
  """Returns the number of elements in the given image buffer."""
  return (
      image_buffer.dimensions.rows
      * image_buffer.dimensions.cols
      * image_buffer.num_channels
  )


def deserialize_image_buffer(
    image: image_buffer_pb2.ImageBuffer,
) -> np.ndarray:
  """Deserializes image from proto format.

  Computes the number of channels per pixel from the total data size, the
  per-channel data type, and the number of pixels, and returns the decoded
  image.

  Args:
    image: The serialized image.

  Returns:
    The unpacked image of size [height, width, num_channels].

  Raises:
    ValueError if the buffer size is invalid.
  """
  if not image.data:
    raise ValueError("No image buffer data provided.")

  buffer = _image_buffer_decoded(image)
  shape = _image_buffer_shape(image)
  size = _image_buffer_size(image)

  if buffer.size != size:
    raise ValueError("Invalid buffer size %d != %d" % (buffer.size, size))

  return buffer.reshape(shape)
