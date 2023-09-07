# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.math.python.math_test module."""

import math

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.math.python import math_test
from intrinsic.math.python import math_types
from intrinsic.math.python import pose3
from intrinsic.math.python import rotation3
from intrinsic.robotics.pymath import vector_util
import numpy as np

_MAKE_TEST_VECTOR_PARAMETERS = (
    (2, None, 1),
    (2, [0, 0.5], 8),
    (3, None, 1),
    (3, [0, 0.333], 30),
    (4, None, 1),
    (4, [-1, 2], 10),
)

_TEST_ERROR_MESSAGE = 'This is a test error message.'

_TEST_ANGLES_IN_DEGREES = (
    0,
    1,
    -1,
    180,
    90,
    360,
    100,
    1800,
    1980,
    1e-6,
    -1e-6,
    180 + 1e-6,
    180 - 1e-6,
    12345,
)
_TEST_ANGLES_IN_RADIANS = [math.radians(a) for a in _TEST_ANGLES_IN_DEGREES]


class MathTest(math_test.TestCase, parameterized.TestCase):

  @parameterized.parameters(*_MAKE_TEST_VECTOR_PARAMETERS)
  def test_make_vectors(self, dimension, values, number_of_random_vectors):
    vectors = math_test.make_test_vectors(
        dimension=dimension,
        values=values,
        number_of_random_vectors=number_of_random_vectors,
        normalize=False,
    )
    num_values = len(values) if values else len(math_test.DEFAULT_TEST_VALUES)
    expected_num_vectors = (
        np.power(num_values, dimension) + number_of_random_vectors
    )
    self.assertLen(vectors, expected_num_vectors)

  @parameterized.parameters(*_MAKE_TEST_VECTOR_PARAMETERS)
  def test_make_vectors_normalized(
      self, dimension, values, number_of_random_vectors
  ):
    vectors = math_test.make_test_vectors(
        dimension=dimension,
        values=values,
        number_of_random_vectors=number_of_random_vectors,
        normalize=True,
    )
    num_values = len(values) if values else len(math_test.DEFAULT_TEST_VALUES)
    expected_max_num_vectors = (
        np.power(num_values, dimension) + number_of_random_vectors
    )
    # This lower bound relies on the values list containing at least two
    # distinct values.
    self.assertGreaterEqual(
        len(vectors), number_of_random_vectors + np.power(2, dimension) - 1
    )
    self.assertLessEqual(len(vectors), expected_max_num_vectors)
    for vector in vectors:
      self.assert_vector_is_normalized(vector)
      self.assertLen(vector, dimension)

  def test_make_named_vectors(self):
    named_vectors = math_test.make_named_vectors()
    logging.debug('%d\n%r', len(named_vectors), named_vectors)
    self.assertNotEmpty(named_vectors)

  def test_make_named_unit_vectors(self):
    named_unit_vectors = math_test.make_named_unit_vectors()
    logging.debug('%d\n%r', len(named_unit_vectors), named_unit_vectors)
    self.assertNotEmpty(named_unit_vectors)
    for name, unit_vector in named_unit_vectors:
      with self.subTest(name=name, unit_vector=unit_vector):
        self.assert_vector_is_normalized(unit_vector)

  def test_make_named_tiny_vectors(self):
    named_tiny_vectors = math_test.make_named_tiny_vectors()
    logging.debug('%d\n%r', len(named_tiny_vectors), named_tiny_vectors)
    self.assertNotEmpty(named_tiny_vectors)
    for name, tiny_vector in named_tiny_vectors:
      with self.subTest(name=name, tiny_vector=tiny_vector):
        self.assertLessEqual(
            np.linalg.norm(tiny_vector), math_test._LESS_THAN_EPSILON * 2.0
        )

  def test_make_named_unit_quaternions(self):
    named_unit_quaternions = math_test.make_named_unit_quaternions()
    logging.debug('%d\n%r', len(named_unit_quaternions), named_unit_quaternions)
    self.assertNotEmpty(named_unit_quaternions)
    for name, unit_quaternion in named_unit_quaternions:
      with self.subTest(name=name, unit_quaternion=unit_quaternion):
        self.assert_quaternion_is_normalized(unit_quaternion)

  def test_make_named_nonunit_quaternions(self):
    named_nonunit_quaternions = math_test.make_named_nonunit_quaternions()
    logging.debug(
        '%d\n%r', len(named_nonunit_quaternions), named_nonunit_quaternions
    )
    self.assertNotEmpty(named_nonunit_quaternions)
    for name, nonunit_quaternion in named_nonunit_quaternions:
      with self.subTest(name=name, nonunit_quaternion=nonunit_quaternion):
        self.assertGreater(np.linalg.norm(nonunit_quaternion.xyzw), 1)

  def test_make_named_tiny_quaternions(self):
    named_tiny_quaternions = math_test.make_named_tiny_quaternions()
    logging.debug('%d\n%r', len(named_tiny_quaternions), named_tiny_quaternions)
    self.assertNotEmpty(named_tiny_quaternions)
    for name, tiny_quaternion in named_tiny_quaternions:
      with self.subTest(name=name, tiny_quaternion=tiny_quaternion):
        self.assertLessEqual(
            np.linalg.norm(tiny_quaternion.xyzw),
            math_test._LESS_THAN_EPSILON * 2.0,
        )

  def test_make_named_rotations(self):
    named_rotations = math_test.make_named_rotations()
    logging.debug('%d\n%r', len(named_rotations), named_rotations)
    self.assertNotEmpty(named_rotations)
    for name, rotation in named_rotations:
      with self.subTest(name=name, rotation=rotation):
        rotation.check_valid()

  def test_make_named_tiny_rotations(self):
    named_tiny_rotations = math_test.make_named_tiny_rotations()
    logging.debug('%d\n%r', len(named_tiny_rotations), named_tiny_rotations)
    self.assertNotEmpty(named_tiny_rotations)
    for name, tiny_rotation in named_tiny_rotations:
      with self.subTest(name=name, tiny_rotation=tiny_rotation):
        tiny_rotation.check_valid()
        self.assertLessEqual(
            tiny_rotation.angle(), math_test._LESS_THAN_EPSILON * 2.0
        )
        self.assert_rotation_close(
            tiny_rotation, rotation3.Rotation3.identity()
        )

  def test_make_named_poses(self):
    named_poses = math_test.make_named_poses()
    logging.debug('%d\n%r', len(named_poses), named_poses)
    self.assertNotEmpty(named_poses)
    for name, pose in named_poses:
      with self.subTest(name=name, pose=pose):
        pose.rotation.check_valid()

  def test_make_named_tiny_poses(self):
    named_tiny_poses = math_test.make_named_tiny_poses()
    logging.debug('%d\n%r', len(named_tiny_poses), named_tiny_poses)
    self.assertNotEmpty(named_tiny_poses)
    for name, tiny_pose in named_tiny_poses:
      with self.subTest(name=name, tiny_pose=tiny_pose):
        tiny_pose.rotation.check_valid()
        self.assertLessEqual(
            tiny_pose.rotation.angle(), math_test._LESS_THAN_EPSILON * 2.0
        )
        self.assert_pose_close(tiny_pose, pose3.Pose3.identity())

  @parameterized.parameters(
      1.0,
      0.0,
      -1.0,
      1.0e-4,
      -1.0e-4,
      1.0e-20,
      -1.0e-20,
      1.0e4,
      -1.0e4,
      1.0e20,
      -1.0e20,
  )
  def test_perturb_value(self, value):
    self.assertEqual(value, self.perturb_value(value, 0))
    self.assert_not_close(
        value,
        self.perturb_value(value, math_test._GREATER_THAN_EPSILON),
        err_msg='Big positive perturbation',
    )
    self.assert_not_close(
        value,
        self.perturb_value(value, -math_test._GREATER_THAN_EPSILON),
        err_msg='Big negative perturbation',
    )
    self.assert_close(
        value,
        self.perturb_value(value, math_test._LESS_THAN_EPSILON),
        err_msg='Tiny positive perturbation',
    )
    self.assert_close(
        value,
        self.perturb_value(value, -math_test._LESS_THAN_EPSILON),
        err_msg='Tiny negative perturbation',
    )
    test_eps = 1e-10
    self.assert_close(
        value,
        self.perturb_value(value, test_eps * 0.5),
        rtol=test_eps,
        atol=test_eps,
        err_msg='Itty bitty epsilon',
    )
    self.assert_not_close(
        value,
        self.perturb_value(value, test_eps * 2),
        rtol=test_eps,
        atol=test_eps,
        err_msg='Itty bitty epsilon',
    )

  @parameterized.parameters(*np.power(10.0, -np.arange(1, 12)))
  def test_assert_close(self, rtol):
    self.assert_close(1, 1, rtol=rtol, atol=0)
    self.assert_close(1, 1 + rtol / 2, rtol=rtol, atol=0)
    self.assert_close(1, 1 - rtol / 2, rtol=rtol, atol=0)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_VALUE_CLOSE_MESSAGE,
        self.assert_close,
        1,
        1 + rtol * 2,
        rtol,
        0,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_VALUE_CLOSE_MESSAGE,
        self.assert_close,
        1,
        1 - rtol * 2,
        rtol,
        0,
    )

  @parameterized.parameters(*np.power(10.0, -np.arange(1, 12)))
  def test_assert_not_close(self, rtol):
    self.assert_not_close(1, 1 + rtol * 2, rtol=rtol, atol=0)
    self.assert_not_close(1, 1 - rtol * 2, rtol=rtol, atol=0)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_VALUE_NOT_CLOSE_MESSAGE,
        self.assert_not_close,
        1,
        1,
        rtol,
        0,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_VALUE_NOT_CLOSE_MESSAGE,
        self.assert_not_close,
        1,
        1 + rtol / 2,
        rtol,
        0,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_VALUE_NOT_CLOSE_MESSAGE,
        self.assert_not_close,
        1,
        1 - rtol / 2,
        rtol,
        0,
    )

  def test_assert_all_less_equal(self):
    epsilon = 1e-6
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_less_equal(-tiny, zero)
    self.assert_all_less_equal(zero, zero)
    self.assert_all_less_equal(zero, tiny)
    self.assert_all_less_equal(zero, ones)
    self.assert_all_less_equal(ones - tiny, ones)
    self.assert_all_less_equal(ones, ones)
    self.assert_all_less_equal(ones, ones + tiny)
    self.assert_all_less_equal(-tiny, 0)
    self.assert_all_less_equal(zero, 0)
    self.assert_all_less_equal(zero, epsilon)
    self.assert_all_less_equal(zero, 1)
    self.assert_all_less_equal(ones - tiny, 1)
    self.assert_all_less_equal(ones, 1)
    self.assert_all_less_equal(ones, 1 + epsilon)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LE_MESSAGE,
        self.assert_all_less_equal,
        ones,
        zero,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LE_MESSAGE,
        self.assert_all_less_equal,
        ones,
        0,
    )
    self.assert_all_less_equal([0, 1], [0, 2])
    self.assert_all_less_equal([0, 1], [1, 2])

  def test_assert_all_less_equal_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_less_equal,
        np.ones(3),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_less_equal,
        np.zeros(2),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_greater_equal(self):
    epsilon = 1e-6
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_greater_equal(zero, -tiny)
    self.assert_all_greater_equal(zero, zero)
    self.assert_all_greater_equal(tiny, zero)
    self.assert_all_greater_equal(ones, zero)
    self.assert_all_greater_equal(ones, ones - tiny)
    self.assert_all_greater_equal(ones, ones)
    self.assert_all_greater_equal(ones + tiny, ones)
    self.assert_all_greater_equal(zero, -epsilon)
    self.assert_all_greater_equal(zero, 0)
    self.assert_all_greater_equal(tiny, 0)
    self.assert_all_greater_equal(ones, 0)
    self.assert_all_greater_equal(ones, 1 - epsilon)
    self.assert_all_greater_equal(ones, 1)
    self.assert_all_greater_equal(ones + tiny, 1)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GE_MESSAGE,
        self.assert_all_greater_equal,
        zero,
        ones,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GE_MESSAGE,
        self.assert_all_greater_equal,
        zero,
        1,
    )
    self.assert_all_greater_equal([1, 1], [0, 1])
    self.assert_all_greater_equal([1, 2], [0, 1])

  def test_assert_all_greater_equal_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_greater_equal,
        np.zeros(3),
        np.ones(3),
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_greater_equal,
        np.zeros(2),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_less(self):
    epsilon = 1e-6
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_less(-tiny, zero)
    self.assert_all_less(zero, tiny)
    self.assert_all_less(zero, ones)
    self.assert_all_less(ones - tiny, ones)
    self.assert_all_less(ones, ones + tiny)
    self.assert_all_less(-tiny, 0)
    self.assert_all_less(zero, epsilon)
    self.assert_all_less(zero, 1)
    self.assert_all_less(ones - tiny, 1)
    self.assert_all_less(ones, 1 + epsilon)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LT_MESSAGE,
        self.assert_all_less,
        zero,
        zero,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LT_MESSAGE,
        self.assert_all_less,
        ones,
        zero,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LT_MESSAGE,
        self.assert_all_less,
        zero,
        0,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_LT_MESSAGE,
        self.assert_all_less,
        ones,
        0,
    )
    self.assert_all_less([0, 1], [1, 2])
    self.assert_all_less([0, 1], [1, 2])

  def test_assert_all_less_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_less,
        np.ones(3),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_less,
        np.zeros(2),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_greater(self):
    epsilon = 1e-6
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_greater(zero, -tiny)
    self.assert_all_greater(tiny, zero)
    self.assert_all_greater(ones, zero)
    self.assert_all_greater(ones, ones - tiny)
    self.assert_all_greater(ones + tiny, ones)
    self.assert_all_greater(zero, -epsilon)
    self.assert_all_greater(tiny, 0)
    self.assert_all_greater(ones, 0)
    self.assert_all_greater(ones, 1 - epsilon)
    self.assert_all_greater(ones + tiny, 1)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GT_MESSAGE,
        self.assert_all_greater,
        zero,
        zero,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GT_MESSAGE,
        self.assert_all_greater,
        zero,
        ones,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GT_MESSAGE,
        self.assert_all_greater,
        zero,
        0,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_GT_MESSAGE,
        self.assert_all_greater,
        zero,
        1,
    )
    self.assert_all_greater([1, 2], [0, 1])

  def test_assert_all_greater_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_greater,
        np.zeros(3),
        np.ones(3),
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_greater,
        np.zeros(2),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_equal(self):
    epsilon = 1e-6
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_equal(zero, zero)
    self.assert_all_equal(ones, ones)
    self.assert_all_equal(tiny, tiny)
    self.assert_all_equal(ones - tiny, ones - tiny)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_EQUAL_MESSAGE,
        self.assert_all_equal,
        zero,
        ones,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_EQUAL_MESSAGE,
        self.assert_all_equal,
        zero,
        1,
    )
    self.assert_all_equal([0, 1], [0, 1])

  def test_assert_all_equal_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_equal,
        np.zeros(3),
        np.ones(3),
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_equal,
        np.zeros(2),
        np.zeros(3),
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_close(self):
    # This epsilon value is smaller than the tolerances in AssertAllClose.
    epsilon = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE * 0.1
    shape = (3, 3)
    zero = np.zeros(shape)
    ones = np.ones(shape)
    tiny = np.full(shape, epsilon)
    self.assert_all_close(zero, zero)
    self.assert_all_close(ones, ones)
    self.assert_all_close(tiny, tiny)
    self.assert_all_close(-tiny, zero)
    self.assert_all_close(ones, ones - tiny)
    self.assert_all_close(zero, tiny)
    self.assert_all_close(ones, 1 + epsilon)
    self.assert_all_close(tiny, 0)
    self.assert_all_close(ones, 1 - epsilon)
    self.assert_all_close(zero, epsilon)
    self.assert_all_close(ones, 1 + epsilon)
    self.assert_all_close(tiny, 3 * tiny)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_CLOSE_MESSAGE,
        self.assert_all_close,
        zero,
        ones,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_ARRAY_CLOSE_MESSAGE,
        self.assert_all_close,
        zero,
        1,
    )
    self.assert_all_close([0, 1], [epsilon, 1])

  def test_assert_all_close_err_msg(self):
    self.assertRaisesRegex(
        AssertionError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_close,
        np.zeros(3),
        np.ones(3),
        math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
        math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
        _TEST_ERROR_MESSAGE,
    )
    self.assertRaisesRegex(
        ValueError,
        _TEST_ERROR_MESSAGE,
        self.assert_all_close,
        np.zeros(2),
        np.zeros(3),
        math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
        math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
        _TEST_ERROR_MESSAGE,
    )

  def test_assert_all_error_message(self):
    shape = (100, 100)
    lhs = np.zeros(shape)
    rhs = np.zeros(shape)
    rhs[10, 10] = 1
    self.assertEqual(
        self._assert_all_error_message(lhs, rhs, (lhs == rhs)),
        '\nmismatch positions = (array([10]), array([10]))\n'
        'mismatch values:\n'
        '  lhs = [0.]\n'
        '  rhs = [1.]\n'
        '  lhs - rhs = [-1.]\n',
    )

  @parameterized.parameters(*_TEST_ANGLES_IN_RADIANS)
  def test_assert_angles_in_radians_close(self, angle):
    for delta_circles in range(-10, 11):
      other_angle = angle + 2 * np.pi * delta_circles
      for epsilon in [
          0,
          math_test._LESS_THAN_EPSILON,
          -math_test._LESS_THAN_EPSILON,
      ]:
        self.assert_angles_in_radians_close(angle, other_angle + epsilon)
        self.assert_angles_in_radians_close(other_angle + epsilon, angle)
        self.assert_angles_in_radians_close(
            angle + epsilon / 2, other_angle - epsilon / 2
        )

  @parameterized.parameters(*_TEST_ANGLES_IN_DEGREES)
  def test_assert_angles_in_degrees_close(self, angle):
    for delta_circles in range(-10, 11):
      other_angle = angle + 360 * delta_circles
      for epsilon in [
          0,
          math_test._LESS_THAN_EPSILON,
          -math_test._LESS_THAN_EPSILON,
      ]:
        self.assert_angles_in_degrees_close(angle, other_angle + epsilon)
        self.assert_angles_in_degrees_close(other_angle + epsilon, angle)
        self.assert_angles_in_degrees_close(
            angle + epsilon / 2, other_angle - epsilon / 2
        )

  @parameterized.parameters(*_TEST_ANGLES_IN_RADIANS)
  def test_assert_angles_in_radians_close_errors(self, angle):
    self.assertRaisesRegex(
        AssertionError,
        math_test.ANGLE_NOT_CLOSE_MESSAGE,
        self.assert_angles_in_radians_close,
        angle,
        angle + np.pi,
    )
    for delta_circles in range(-2, 3):
      other_angle = angle + 2 * np.pi * delta_circles
      self.assert_angles_in_radians_close(angle, other_angle)
      self.assertRaisesRegex(
          AssertionError,
          math_test.ANGLE_NOT_CLOSE_MESSAGE,
          self.assert_angles_in_radians_close,
          angle,
          self.perturb_value(other_angle),
      )

  @parameterized.parameters(*_TEST_ANGLES_IN_DEGREES)
  def test_assert_angles_in_degrees_close_errors(self, angle):
    self.assertRaisesRegex(
        AssertionError,
        math_test.ANGLE_NOT_CLOSE_MESSAGE,
        self.assert_angles_in_radians_close,
        angle,
        angle + 180,
    )
    for delta_circles in range(-2, 3):
      other_angle = angle + 360 * delta_circles
      self.assert_angles_in_degrees_close(angle, other_angle)
      self.assertRaisesRegex(
          AssertionError,
          math_test.ANGLE_NOT_CLOSE_MESSAGE,
          self.assert_angles_in_degrees_close,
          angle,
          self.perturb_value(other_angle),
      )

  @parameterized.parameters(
      (2, 1e-2),
      (2, 1e-6),
      (3, 1e-2),
      (4, 1e-6),
      (5, 1e-3),
      (6, 1e-6),
      (7, 1e-2),
  )
  def test_assert_vector_is_normalized(self, dimension, norm_epsilon):
    """Tests assert_vector_is_normalized function.

    Verifies that only the vectors whose magnitude lie in:
      |vector| in (1 - norm_epsilon, 1 + norm_epsilon)
    are considered normalized by this function.

    Args:
      dimension: Number of components in the vector space.
      norm_epsilon: Error tolerance for magnitude of vector.
    """
    self.assertRaisesRegex(
        AssertionError,
        math_test.NOT_NORMALIZED_MESSAGE,
        self.assert_vector_is_normalized,
        np.ones(dimension),
        norm_epsilon,
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.NOT_NORMALIZED_MESSAGE,
        self.assert_vector_is_normalized,
        np.zeros(dimension),
        norm_epsilon,
    )
    for unit_vector in math_test.make_test_vectors(
        dimension, normalize=True, number_of_random_vectors=4
    ):
      self.assert_vector_is_normalized(unit_vector, norm_epsilon)
      self.assert_vector_is_normalized(
          unit_vector * (1.0 + norm_epsilon * 0.9), norm_epsilon
      )
      self.assert_vector_is_normalized(
          unit_vector * (1.0 - norm_epsilon * 0.9), norm_epsilon
      )
      small_error_vector = (
          vector_util.one_hot_vector(dimension, 0) * norm_epsilon * 0.9
      )
      self.assert_vector_is_normalized(
          unit_vector + small_error_vector, norm_epsilon
      )
      self.assertRaisesRegex(
          AssertionError,
          math_test.NOT_NORMALIZED_MESSAGE,
          self.assert_vector_is_normalized,
          unit_vector * (1.0 + norm_epsilon * 1.1),
          norm_epsilon,
      )
      self.assertRaisesRegex(
          AssertionError,
          math_test.NOT_NORMALIZED_MESSAGE,
          self.assert_vector_is_normalized,
          unit_vector * (1.0 - norm_epsilon * 1.1),
          norm_epsilon,
      )

  def test_check_eq_and_ne_for_equal_values(self):
    self.check_eq_and_ne_for_equal_values('foo', 'foo')
    self.check_eq_and_ne_for_equal_values(1, 1)
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_EQ_MESSAGE,
        self.check_eq_and_ne_for_equal_values,
        1,
        2,
    )

    class BadEq(object):
      """A test class with invalid __eq__ function."""

      def __init__(self, value):
        self.value = value

      def __eq__(self, other):
        return self.value <= other.value

      def __ne__(self, other):
        return self.value != other.value

    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_EQ_MESSAGE,
        self.check_eq_and_ne_for_equal_values,
        BadEq(1),
        BadEq(2),
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_EQ_MESSAGE,
        self.check_eq_and_ne_for_unequal_values,
        BadEq(1),
        BadEq(2),
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_EQ_MESSAGE,
        self.check_eq_and_ne_for_unequal_values,
        BadEq(2),
        BadEq(1),
    )

  def test_check_eq_and_ne_for_unequal_values(self):
    self.check_eq_and_ne_for_unequal_values('foo', 'bar')
    self.check_eq_and_ne_for_unequal_values(1, 2)

    class BadNe(object):
      """A test class with invalid __ne__ function."""

      def __init__(self, value):
        self.value = value

      def __eq__(self, other):
        return True

      def __ne__(self, other):
        return self.value < other.value

    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_NE_MESSAGE,
        self.check_eq_and_ne_for_unequal_values,
        BadNe(1),
        BadNe(2),
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_NE_MESSAGE,
        self.check_eq_and_ne_for_equal_values,
        BadNe(1),
        BadNe(2),
    )
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_NE_MESSAGE,
        self.check_eq_and_ne_for_equal_values,
        BadNe(2),
        BadNe(1),
    )

  def test_check_hash_for_equal_values(self):
    self.check_hash_for_equal_values('foo', 'foo')
    self.check_hash_for_equal_values(1, 1)

    class DifferentHash(object):
      """A test class that returns a different hash value on each call."""

      def __init__(self):
        self.hash = 1

      def __hash__(self):
        self.hash += 1
        return self.hash

    bad_object = DifferentHash()
    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_EQ_HASH_MESSAGE,
        self.check_hash_for_equal_values,
        bad_object,
        bad_object,
    )

  def test_check_hash_for_unequal_values(self):
    self.check_hash_for_unequal_values('foo', 'bar')
    self.check_hash_for_unequal_values(1, 2)

    class SameHash(object):
      """A test class that returns the same hash value for every call."""

      def __hash__(self):
        return 1

    self.assertRaisesRegex(
        AssertionError,
        math_test.ASSERT_NE_HASH_MESSAGE,
        self.check_hash_for_unequal_values,
        SameHash(),
        SameHash(),
    )


if __name__ == '__main__':
  absltest.main()
