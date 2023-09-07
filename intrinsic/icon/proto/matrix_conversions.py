# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Conversions to/from numpy ndarray from/to matrix proto types."""

from intrinsic.icon.proto import matrix_pb2
import numpy as np


def from_ndarray(matrix: np.ndarray) -> matrix_pb2.Matrix6d:
  """Converts from a numpy ndarray to a Matrix6d proto.

  Args:
    matrix: the matrix as a ndarray.

  Returns:
    A Matrix6d proto.

  Raises:
    ValueError: If the input ndarray is not 6x6.
  """
  if matrix.shape[0] != matrix.shape[1] != 6:
    raise ValueError('Matrix is not 6x6, received size [%s,%s]' % matrix.shape)

  proto_matrix = matrix_pb2.Matrix6d()
  for val in matrix.flatten():
    proto_matrix.data.append(val)

  return proto_matrix


def to_ndarray(proto_matrix: matrix_pb2.Matrix6d) -> np.ndarray:
  """Converts from a Matrix6d proto to a numpy ndarray.

  Args:
    proto_matrix: the matrix as a Matrix6d.

  Returns:
    A numpy ndarray.

  Raises:
    ValueError: if the input matrix does not have 36 elements.
  """
  if len(proto_matrix.data) != 36:
    raise ValueError(
        'Matrix is not 6x6, received size %s' % len(proto_matrix.data)
    )

  return np.array([
      proto_matrix.data[0:6],
      proto_matrix.data[6:12],
      proto_matrix.data[12:18],
      proto_matrix.data[18:24],
      proto_matrix.data[24:30],
      proto_matrix.data[30:36],
  ])
