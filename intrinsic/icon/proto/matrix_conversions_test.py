# Copyright 2023 Intrinsic Innovation LLC

"""Tests for matrix_conversions."""

from absl.testing import absltest
from intrinsic.icon.proto import matrix_conversions
from intrinsic.icon.proto import matrix_pb2
import numpy as np


class MatrixConversionsTest(absltest.TestCase):

  def test_from_ndarray(self):
    matrix_array = np.array([
        [0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1],
        [2, 2, 2, 2, 2, 2],
        [3, 3, 3, 3, 3, 3],
        [4, 4, 4, 4, 4, 4],
        [5, 5, 5, 5, 5, 5],
    ])
    proto_matrix = matrix_pb2.Matrix6d()
    for val in matrix_array.flatten():
      proto_matrix.data.append(val)

    returned_proto = matrix_conversions.from_ndarray(matrix_array)

    self.assertEqual(returned_proto.data, proto_matrix.data)

  def test_from_ndarray_throws_error_wrong_matrix_dim(self):
    matrix_array = np.array([
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        [2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3],
        [4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5],
    ])
    proto_matrix = matrix_pb2.Matrix6d()
    for val in matrix_array.flatten():
      proto_matrix.data.append(val)

    with self.assertRaises(ValueError):
      matrix_conversions.from_ndarray(matrix_array)

  def test_to_ndarray(self):
    proto_matrix = matrix_pb2.Matrix6d()
    for _ in range(36):
      proto_matrix.data.append(3)

    expected_array = np.array([
        [3, 3, 3, 3, 3, 3],
        [3, 3, 3, 3, 3, 3],
        [3, 3, 3, 3, 3, 3],
        [3, 3, 3, 3, 3, 3],
        [3, 3, 3, 3, 3, 3],
        [3, 3, 3, 3, 3, 3],
    ])

    returned_array = matrix_conversions.to_ndarray(proto_matrix)

    self.assertTrue(np.allclose(expected_array, returned_array))

  def test_to_ndarray_trows_error_wrong_dim(self):

    proto_matrix = matrix_pb2.Matrix6d()
    for _ in range(35):
      proto_matrix.data.append(3)

    with self.assertRaises(ValueError):
      matrix_conversions.to_ndarray(proto_matrix)


if __name__ == '__main__':
  absltest.main()
