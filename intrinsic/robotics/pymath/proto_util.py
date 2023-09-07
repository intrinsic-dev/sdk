# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Protobuf conversion utilities.

Vectors are represented as a numpy.ndarray.
"""

from typing import Optional, Tuple, Union
from absl import logging
from intrinsic.robotics.messages import vector_pb2
from intrinsic.robotics.pymath import math_types
from intrinsic.robotics.pymath import vector_util
import numpy as np

# ----------------------------------------------------------------------------
# Pytype definitions.

VectorProtoType = Union[
    vector_pb2.Vectord,
    vector_pb2.Vectorf,
    vector_pb2.Vectori,
    vector_pb2.Vector2d,
    vector_pb2.Vector2f,
    vector_pb2.Vector2i,
    vector_pb2.Vector3d,
    vector_pb2.Vector3f,
    vector_pb2.Vector3i,
    vector_pb2.Vector4d,
    vector_pb2.Vector4f,
    vector_pb2.Vector4i,
]

# ----------------------------------------------------------------------------

# Field names for Vector protobufs with fixed size.
#
# The final entry causes conversion to fail with a predictable message when
# converting a vector that does not fit in the protobuf.
_FIELD_NAMES = ('x', 'y', 'z', 'w', 'NO_SUCH_FIELD')

_MIN_FIXED_DIMENSION = 2
_MAX_FIXED_DIMENSION = 4
_UNBOUNDED_DIMENSION = -1


def _dim_and_type_of_proto(math_proto: VectorProtoType) -> Tuple[int, np.dtype]:
  """Returns the numeric type and the dimension of the associated vector.

  The representable dimension of the vector is returned.

  If the vector is resizable and can represent vectors of arbitrary dimension,
  returns _UNBOUNDED_DIMENSION.

  Args:
    math_proto: A protobuf representing an object in a vector space.

  Returns:
    dim: Dimension of the space, either an integer or _UNBOUNDED_DIMENSION.
    type: Numeric type (int or float).
  """

  proto_to_dim_and_type = {
      vector_pb2.Vectord: (_UNBOUNDED_DIMENSION, np.dtype(np.float64)),
      vector_pb2.Vector2d: (2, np.dtype(np.float64)),
      vector_pb2.Vector3d: (3, np.dtype(np.float64)),
      vector_pb2.Vector4d: (4, np.dtype(np.float64)),
      vector_pb2.Vectorf: (_UNBOUNDED_DIMENSION, np.dtype(np.float32)),
      vector_pb2.Vector2f: (2, np.dtype(np.float32)),
      vector_pb2.Vector3f: (3, np.dtype(np.float32)),
      vector_pb2.Vector4f: (4, np.dtype(np.float32)),
      vector_pb2.Vectori: (_UNBOUNDED_DIMENSION, np.dtype(np.int64)),
      vector_pb2.Vector2i: (2, np.dtype(np.int64)),
      vector_pb2.Vector3i: (3, np.dtype(np.int64)),
      vector_pb2.Vector4i: (4, np.dtype(np.int64)),
  }

  return proto_to_dim_and_type[(type(math_proto))]


def dim_and_type_key(vec: math_types.VectorType):
  vec = vector_util.as_vector(vec)
  dim = vec.size
  if dim < _MIN_FIXED_DIMENSION or dim > _MAX_FIXED_DIMENSION:
    dim = _UNBOUNDED_DIMENSION
  is_integer = np.issubdtype(vec.dtype, np.signedinteger)
  return (dim, is_integer)


def vector_proto_for_vector(
    vector_in: math_types.VectorType,
) -> VectorProtoType:
  """Returns the appropriate Vector protobuf for this vector."""
  key = dim_and_type_key(vector_in)
  proto_for_dim_and_type = {
      (2, True): vector_pb2.Vector2i,
      (3, True): vector_pb2.Vector3i,
      (4, True): vector_pb2.Vector4i,
      (2, False): vector_pb2.Vector2d,
      (3, False): vector_pb2.Vector3d,
      (4, False): vector_pb2.Vector4d,
      (_UNBOUNDED_DIMENSION, True): vector_pb2.Vectori,
      (_UNBOUNDED_DIMENSION, False): vector_pb2.Vectord,
  }
  return proto_for_dim_and_type[key]()


def vector_to_proto(
    vector_in: math_types.VectorType,
    proto_out: Optional[VectorProtoType] = None,
) -> VectorProtoType:
  """Returns a protobuf that represents the vector.

  Args:
    vector_in: Vector as a numpy array.
    proto_out: Optional output protobuf.

  Returns:
    Protobuf that represents the vector.
  """
  vector_in = vector_util.as_vector(vector_in)
  if proto_out is None:
    proto_out = vector_proto_for_vector(vector_in)
  proto_out.Clear()
  logging.debug('Populating %s from %s', type(proto_out), vector_in)
  if hasattr(proto_out, 'data'):
    proto_out.data[:] = vector_in
  else:
    for index in range(vector_in.size):
      setattr(proto_out, _FIELD_NAMES[index], vector_in[index])
  return proto_out


def vector_from_proto(proto_in: VectorProtoType) -> np.ndarray:
  """Returns a numpy array containing the vector defined in the protobuf.

  Args:
    proto_in: Protobuf representing a vector.

  Returns:
    Vector as a numpy array.
  """
  logging.debug('Extracting from %s %s', proto_in, type(proto_in))
  if hasattr(proto_in, 'data'):
    return np.asarray(proto_in.data)
  else:
    dim, _ = _dim_and_type_of_proto(proto_in)
    vector_out = [getattr(proto_in, _FIELD_NAMES[i]) for i in range(dim)]
    return np.asarray(vector_out)
