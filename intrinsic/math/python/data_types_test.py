# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.math.data_types."""

from absl.testing import absltest
from intrinsic.icon.proto import cart_space_pb2
from intrinsic.math.python import data_types
import numpy as np


class TypesTest(absltest.TestCase):

  def test_stiffness_vector_init(self):
    stiffness = data_types.Stiffness(
        linear=[1.0, 2.0, 3.0], torsional=[3.0, 2.0, 1.0]
    )
    self.assertSequenceEqual(
        [1.0, 2.0, 3.0, 3.0, 2.0, 1.0], stiffness.vec.tolist()
    )
    self.assertTrue(
        np.array_equal(
            np.diag([1.0, 2.0, 3.0, 3.0, 2.0, 1.0]), stiffness.matrix6x6
        )
    )

  def test_stiffness_matrix_init(self):
    matrix6x6 = np.asarray([
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        [3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        [5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        [6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
    ])
    stiffness = data_types.Stiffness(
        linear=[1.0, 1.0, 1.0], matrix6x6=matrix6x6
    )
    self.assertSequenceEqual(
        [1.0, 3.0, 5.0, 7.0, 9.0, 11.0], stiffness.vec.tolist()
    )
    self.assertTrue(np.array_equal(matrix6x6, stiffness.matrix6x6))

    # When the shape of matrix6x6 is invalid.
    try:
      stiffness = data_types.Stiffness(matrix6x6=np.identity(2))
    except ValueError as err:
      self.assertEqual('Invalid matrix6x6 shape: (2, 2)', str(err))
    else:
      self.fail('A ValueError is expected when matrix6x6 shape is invalid.')

  def test_vec6_to_pose3(self):
    pose = data_types.vec6_to_pose3([1.0, 2.0, 3.0, 0.5, 0.2, 0.4])

    # Expected quaternion conversion results obtained using
    #   https://quaternions.online
    # with ZYX convention.
    expected = [1.0, 2.0, 3.0, 0.222, 0.144, 0.167, 0.95]
    self.assertSequenceAlmostEqual(expected, pose.vec7.tolist(), places=3)

  def test_pose3_to_vec6_in_axis_angles(self):
    pose3 = data_types.vec6_to_pose3([1.0, 2.0, 3.0, 0.5, 0.2, 0.4])
    expected = [1.0, 2.0, 3.0, 0.45167698, 0.29232736, 0.34036853]
    self.assertSequenceAlmostEqual(
        data_types.pose3_to_vec6_in_axis_angles(pose3), expected, places=3
    )

  def test_to_list(self):
    expected = [3.0]
    self.assertSequenceAlmostEqual(data_types.to_list(3.0), expected, places=5)

    expected = [3.0, 1.0]
    self.assertSequenceAlmostEqual(
        data_types.to_list(np.array([3.0, 1.0])), expected, places=5
    )

    expected = [0, 0, 0, 0, 0, 0, 1]
    self.assertSequenceAlmostEqual(
        data_types.to_list(data_types.Pose3()), expected, places=5
    )

    expected = [1, 2, 3, 0, 0, 0]
    self.assertSequenceAlmostEqual(
        data_types.to_list(data_types.Twist(linear=[1, 2, 3])),
        expected,
        places=5,
    )
    expected = [4, 5, 6, 0, 0, 0]
    self.assertSequenceAlmostEqual(
        data_types.to_list(data_types.Wrench(force=[4, 5, 6])),
        expected,
        places=5,
    )

    stiffness = data_types.Stiffness(
        linear=[1.0, 2.0, 3.0], torsional=[3.0, 2.0, 1.0]
    )
    with self.assertRaises(ValueError):
      data_types.to_list(stiffness)

  def test_pose3_to_transform(self):
    expected_transform = cart_space_pb2.Transform(
        pos=cart_space_pb2.Point(x=0, y=1, z=2),
        rot=cart_space_pb2.Rotation(qx=4, qy=5, qz=6, qw=7),
    )

    pose = data_types.Pose3(
        rotation=data_types.Rotation3(quat=data_types.Quaternion([4, 5, 6, 7])),
        translation=[0, 1, 2],
    )

    returned_transform = data_types.pose3_to_transform(pose)

    self.assertEqual(expected_transform, returned_transform)

  def test_transform_to_pose3(self):
    transform = cart_space_pb2.Transform(
        pos=cart_space_pb2.Point(x=0, y=1, z=2),
        rot=cart_space_pb2.Rotation(qx=4, qy=5, qz=6, qw=7),
    )

    expected_pose = data_types.Pose3(
        rotation=data_types.Rotation3(quat=data_types.Quaternion([4, 5, 6, 7])),
        translation=[0, 1, 2],
    )

    returned_pose = data_types.transform_to_pose3(transform)

    self.assertEqual(expected_pose, returned_pose)


if __name__ == '__main__':
  absltest.main()
