# Copyright 2023 Intrinsic Innovation LLC

"""Tests for math proto conversion utils."""

from absl.testing import absltest
from absl.testing import parameterized
import hypothesis
from hypothesis.extra import numpy as np_strategies
from intrinsic.math.proto import array_pb2
from intrinsic.math.proto import matrix_pb2
from intrinsic.math.proto import point_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.proto import quaternion_pb2
from intrinsic.math.proto import vector3_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion
import numpy as np


_rng = np.random.RandomState(seed=0)


class ProtoConversionTest(parameterized.TestCase):
  """Tests conversion of math protos to/from corresponding python classes."""

  @parameterized.parameters(
      (np.round(_rng.rand(3, 1, 4)).astype(bool),),
      (_rng.randint(low=-(2**7), high=2**7 - 1, size=(1, 5), dtype=np.int8),),
      (_rng.randint(low=-(2**15), high=2**15 - 1, size=(9,), dtype=np.int16),),
      (
          _rng.randint(
              low=-(2**31), high=2**31 - 1, size=(2, 6), dtype=np.int32
          ),
      ),
      (
          _rng.randint(
              low=-(2**63), high=2**63 - 1, size=(5, 3), dtype=np.int64
          ),
      ),
      (_rng.randint(low=0, high=2**8 - 1, size=(5, 8, 9), dtype=np.uint8),),
      (_rng.randint(low=0, high=2**16 - 1, size=(7, 9), dtype=np.uint16),),
      (_rng.randint(low=0, high=2**32 - 1, size=(3, 2, 3), dtype=np.uint32),),
      (_rng.randint(low=0, high=2**64 - 1, size=(8, 4, 6), dtype=np.uint64),),
      (
          _rng.rand(
              2,
          ).astype(np.float16),
      ),
      (_rng.rand(6, 4).astype(np.float32),),
      (_rng.rand(3, 3).astype(np.float64),),
      (
          _rng.randint(low=-(2**15), high=2**15 - 1, size=(8, 3)).astype(
              np.dtype('int16').newbyteorder('>')
          ),
      ),
      (_rng.rand(2, 7).astype(np.dtype('float32').newbyteorder('>')),),
      (
          _rng.randint(low=-(2**15), high=2**15 - 1, size=(9,)).astype(
              np.dtype('int16').newbyteorder('<')
          ),
      ),
      (
          _rng.rand(
              5,
          ).astype(np.dtype('float32').newbyteorder('<')),
      ),
  )
  def test_ndarray_to_from_proto(self, array):
    recovered = proto_conversion.ndarray_from_proto(
        proto_conversion.ndarray_to_proto(array)
    )

    self.assertEqual(array.dtype, recovered.dtype)
    np.testing.assert_array_equal(array, recovered)

  def test_ndarray_to_proto_fails_for_unknown_dtype(self):
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_to_proto(np.array('bob'))

  def test_ndarray_from_proto_fails_for_unknown_scalar_type(self):
    shape = (3,)
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_from_proto(
          array_pb2.Array(
              data=np.zeros(shape).tobytes(),
              shape=shape,
              type=array_pb2.Array.ScalarType.UNSPECIFIED_SCALAR_TYPE,
              byte_order=array_pb2.Array.ByteOrder.LITTLE_ENDIAN_BYTE_ORDER,
          )
      )

  def test_ndarray_from_proto_fails_for_unknown_byte_order(self):
    shape = (3,)
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_from_proto(
          array_pb2.Array(
              data=np.zeros(shape, dtype=np.uint8).tobytes(),
              shape=shape,
              type=array_pb2.Array.ScalarType.UINT8_SCALAR_TYPE,
              byte_order=array_pb2.Array.ByteOrder.UNSPECIFIED_BYTE_ORDER,
          )
      )

  def test_ndarray_from_proto_fails_for_no_byte_order_from_ordered_type(self):
    shape = (3,)
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_from_proto(
          array_pb2.Array(
              data=np.zeros(shape, dtype=np.float32).tobytes(),
              shape=shape,
              type=array_pb2.Array.ScalarType.FLOAT32_SCALAR_TYPE,
              byte_order=array_pb2.Array.ByteOrder.NO_BYTE_ORDER,
          )
      )

  def test_ndarray_from_point_proto(self):
    point_proto_expected = point_pb2.Point(x=0.1, y=0.2, z=0.3)
    point_as_ndarray = proto_conversion.ndarray_from_point_proto(
        point_proto_expected
    )
    point_proto = proto_conversion.ndarray_to_point_proto(point_as_ndarray)
    self.assertEqual(point_proto, point_proto_expected)

  def test_ndarray_to_point_proto(self):
    np_point_expected = np.random.randn(3)
    point_proto = proto_conversion.ndarray_to_point_proto(np_point_expected)
    np_point = proto_conversion.ndarray_from_point_proto(point_proto)
    np.testing.assert_equal(np_point, np_point_expected)

  def test_ndarray_to_point_proto_fails_for_wrong_size(self):
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_to_point_proto(np.random.randn(0))
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_to_point_proto(np.random.randn(2))
    with self.assertRaises(ValueError):
      proto_conversion.ndarray_to_point_proto(np.random.randn(4))

  def test_quaternion_from_proto(self):
    quat_proto_expected = quaternion_pb2.Quaternion(x=0.1, y=0.2, z=0.3, w=0.4)
    quat = proto_conversion.quaternion_from_proto(quat_proto_expected)
    quat_proto = proto_conversion.quaternion_to_proto(quat)
    self.assertEqual(quat_proto, quat_proto_expected)

  def test_quaternion_to_proto(self):
    quat_expected = data_types.Quaternion.random_unit()
    quat_proto = proto_conversion.quaternion_to_proto(quat_expected)
    quat = proto_conversion.quaternion_from_proto(quat_proto)
    self.assertEqual(quat, quat_expected)

  def test_pose_from_proto_fails_for_non_unit_quaterions(self):
    pose_proto_expected = pose_pb2.Pose(
        position=point_pb2.Point(x=0.1, y=0.2, z=0.3),
        orientation=quaternion_pb2.Quaternion(x=0.4, y=0.5, z=0.6, w=0.7),
    )
    # Can't construct a pose with non-normalized quaternion!
    with self.assertRaises(ValueError):
      proto_conversion.pose_from_proto(pose_proto_expected)

  def test_pose_from_proto(self):
    pose_proto_expected = pose_pb2.Pose(
        position=point_pb2.Point(x=0.1, y=0.2, z=0.3),
        orientation=quaternion_pb2.Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
    )
    pose = proto_conversion.pose_from_proto(pose_proto_expected)
    pose_proto = proto_conversion.pose_to_proto(pose)
    self.assertEqual(pose_proto, pose_proto_expected)

  def test_pose_to_proto_normalized(self):
    pose_expected = data_types.Pose3(
        translation=np.random.randn(3), rotation=data_types.Rotation3.random()
    )
    pose_proto = proto_conversion.pose_to_proto(pose_expected)
    pose = proto_conversion.pose_from_proto(pose_proto)
    self.assertEqual(pose, pose_expected)

    pose = data_types.Pose3(
        translation=[1, 2, 3],
        rotation=data_types.Rotation3(
            quat=data_types.Quaternion([0.5, -0.5, 0.5, -0.5])
        ),
    )
    pose_proto_expected = pose_pb2.Pose(
        position=point_pb2.Point(x=1, y=2, z=3),
        orientation=quaternion_pb2.Quaternion(x=0.5, y=-0.5, z=0.5, w=-0.5),
    )
    pose_proto = proto_conversion.pose_to_proto(pose)
    self.assertEqual(pose_proto, pose_proto_expected)

  def test_pose_to_proto_not_normalized(self):
    pose = data_types.Pose3(
        translation=[1, 2, 3],
        rotation=data_types.Rotation3(
            quat=data_types.Quaternion([0, 0, 0, 1.1])
        ),
    )
    pose_proto_expected = pose_pb2.Pose(
        position=point_pb2.Point(x=1, y=2, z=3),
        orientation=quaternion_pb2.Quaternion(x=0, y=0, z=0, w=1),
    )
    pose_proto = proto_conversion.pose_to_proto(pose)
    self.assertEqual(pose_proto, pose_proto_expected)

  def test_pose_roundtrip(self):
    pose_proto = pose_pb2.Pose(
        position=point_pb2.Point(x=-1.32635246, y=-0.20890486, z=-0.16996824),
        orientation=quaternion_pb2.Quaternion(
            x=-0.53663178, y=-0.49717722, z=0.24928427, w=-0.6345853
        ),
    )
    result_proto = proto_conversion.pose_to_proto(
        proto_conversion.pose_from_proto(pose_proto)
    )
    # We expect bit-wise equality
    self.assertEqual(result_proto, pose_proto)

  ndarray_from_matrix_proto_test_cases = [
      dict(
          testcase_name='1x1_zeros',
          array=np.zeros((1, 1)),
          proto=matrix_pb2.Matrixd(rows=1, cols=1, values=[0.0]),
      ),
      dict(
          testcase_name='2x2_values',
          array=np.arange(0, 4).reshape((2, 2)),
          proto=matrix_pb2.Matrixd(rows=2, cols=2, values=[0.0, 2.0, 1.0, 3.0]),
      ),
      dict(
          testcase_name='3x2_values',
          array=np.arange(0, 6).reshape((3, 2)),
          proto=matrix_pb2.Matrixd(
              rows=3, cols=2, values=[0.0, 2.0, 4.0, 1.0, 3.0, 5.0]
          ),
      ),
  ]

  @parameterized.named_parameters(ndarray_from_matrix_proto_test_cases)
  def test_ndarray_to_matrix_proto(
      self, array: np.ndarray, proto: matrix_pb2.Matrixd
  ):
    self.assertEqual(proto_conversion.ndarray_to_matrix_proto(array), proto)

  @parameterized.named_parameters(ndarray_from_matrix_proto_test_cases)
  def test_ndarray_from_matrix_proto(
      self, array: np.ndarray, proto: matrix_pb2.Matrixd
  ):
    got_array = proto_conversion.ndarray_from_matrix_proto(proto)
    np.testing.assert_array_equal(got_array, array)

  @hypothesis.given(
      np_strategies.arrays(
          dtype=np_strategies.floating_dtypes(),
          shape=np_strategies.array_shapes(min_dims=2, max_dims=2),
      )
  )
  def test_ndarray_to_from_matrix_proto_roundtrip(self, array: np.ndarray):
    proto = proto_conversion.ndarray_to_matrix_proto(array)
    np.testing.assert_array_equal(
        proto_conversion.ndarray_from_matrix_proto(proto), array
    )

  def test_ndarray_from_matrix_proto_fails_for_wrong_size(self):
    with self.assertRaisesRegex(
        ValueError, 'matrix is not 3x2, it has 5 values.'
    ):
      proto_conversion.ndarray_from_matrix_proto(
          matrix_pb2.Matrixd(rows=3, cols=2, values=[0.0, 1.0, 2.0, 3.0, 4.0])
      )

  def test_ndarray_to_matrix_proto_fails_for_wrong_size(self):
    with self.assertRaisesRegex(
        ValueError, r'expected a 2D array, got shape \(3, 2, 1\).'
    ):
      proto_conversion.ndarray_to_matrix_proto(
          np.arange(0, 6).reshape((3, 2, 1))
      )


if __name__ == '__main__':
  absltest.main()
