# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""intrinsic.math.python.TestCase - Base class for tests in intrinsic.math.python (python3).

make_named_<object> - Generates lists of named objects for parameterized tests.

make_test_vectors - Generates a set of n-dimensional test vectors.

TestCase - Base class for tests in pymath.

This class defines array comparison functions that are provided in
third_party/tensorflow/python/framework/test_util.py
but it does not bring in all of the tensorflow dependencies.
"""

import operator
import random
from typing import List, Optional, Text, Tuple

from absl import logging
from absl.testing import absltest
from intrinsic.math.python import math_types
from intrinsic.math.python import pose3
from intrinsic.math.python import quaternion
from intrinsic.math.python import rotation3
from intrinsic.robotics.pymath import vector_util
import numpy as np

# ---------------------------------------------------------------------------
# PyType Definitions
NamedVectorType = Tuple[Text, np.ndarray]
NamedQuaternionType = Tuple[Text, quaternion.Quaternion]
NamedRotationType = Tuple[Text, rotation3.Rotation3]
NamedPoseInputType = Tuple[Text, rotation3.Rotation3, np.ndarray]
NamedPoseType = Tuple[Text, pose3.Pose3]
# ---------------------------------------------------------------------------
# Regular expression patterns for assertRaisesRegexp.
ASSERT_VALUE_CLOSE_MESSAGE = 'Values do not satisfy lhs close to rhs'
ASSERT_VALUE_NOT_CLOSE_MESSAGE = 'Values do not satisfy lhs not close to rhs'
NOT_NORMALIZED_MESSAGE = 'is not normalized within'
ASSERT_ARRAY_LE_MESSAGE = 'Arrays do not satisfy lhs <= rhs'
ASSERT_ARRAY_LT_MESSAGE = 'Arrays do not satisfy lhs < rhs'
ASSERT_ARRAY_GE_MESSAGE = 'Arrays do not satisfy lhs >= rhs'
ASSERT_ARRAY_GT_MESSAGE = 'Arrays do not satisfy lhs > rhs'
ASSERT_ARRAY_CLOSE_MESSAGE = 'Arrays do not satisfy lhs close to rhs'
ASSERT_ARRAY_EQUAL_MESSAGE = 'Arrays are not equal'
ASSERT_EMPTY_MESSAGE = 'is not empty'
ASSERT_NOT_EMPTY_MESSAGE = 'is empty'
ASSERT_CONTAINS_MESSAGE = 'does not contain'
ASSERT_NOT_CONTAINS_MESSAGE = 'contains'
ASSERT_INTERSECTS_MESSAGE = 'does not intersect'
ASSERT_NOT_INTERSECTS_MESSAGE = 'intersects'
ANGLE_NOT_CLOSE_MESSAGE = 'Angles are not equivalent within tolerance'
ROTATION_NOT_CLOSE_MESSAGE = 'Rotations are not equivalent within tolerance'
POSE_NOT_CLOSE_MESSAGE = 'Poses are not equivalent within tolerance'
INTERVAL_NOT_CLOSE_MESSAGE = 'Intervals are not equivalent within tolerance'
ASSERT_EQ_MESSAGE = 'The __eq__ function returned an invalid result.'
ASSERT_NE_MESSAGE = 'The __ne__ function returned an invalid result.'
ASSERT_EQ_HASH_MESSAGE = 'Values are equal but hash values are not equal.'
ASSERT_NE_HASH_MESSAGE = 'Values are not equal but hash values are equal.'

# Epsilon value that is smaller than all test thresholds.  Used to generate test
# vectors that test True for close but not equal.
_LESS_THAN_EPSILON = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE * 0.1

# Epsilon value that is greater than all test thresholds.  Used to generate test
# vectors that test False for close.
_GREATER_THAN_EPSILON = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE * 10.0

# Default values used to generate test vectors.
DEFAULT_TEST_VALUES = [0.0, 1.0, -1.0]

# ---------------------------------------------------------------------------
# Functions that generated named test inputs for parameterized tests.
# Each function returns a list of pairs of (name, value).
#
#   make_named_vectors
#   make_named_unit_vectors
#   make_named_tiny_vectors
#   make_named_unit_quaternions
#   make_named_nonunit_quaternions
#   make_named_tiny_quaternions
#   make_named_rotations
#   make_named_tiny_rotations
#   make_named_pose_inputs
#   make_named_poses
#   make_named_tiny_poses


def _make_named_input(test_input):
  """Attaches a name to a test input.

  Attaches a generated name to a test input.  This is useful for adding
  generated test inputs to a set of canonical inputs in a test.

  Args:
    test_input: Test input value.

  Returns:
    (name, test_input) - The test input with a string name.
  """
  return ('%s' % test_input, test_input)


def _add_negative_named_values(named_values):
  """Adds negatives of all named values to the list."""
  return named_values + [
      (('-%s' % name), -value) for name, value in named_values
  ]


def make_named_vectors() -> List[NamedVectorType]:
  """Creates a list of name,vector pairs with known values."""
  named_vectors = [
      ('x', np.array((1.0, 0.0, 0.0))),
      ('y', np.array((0.0, 1.0, 0.0))),
      ('z', np.array((0.0, 0.0, 1.0))),
      ('xy', np.array((1.0, -1.0, 0.0))),
      ('yz', np.array((0.0, 1.0, -1.0))),
      ('zx', np.array((-1.0, 0.0, 1.0))),
      ('111', np.array((1.0, 1.0, 1.0))),
      ('123', np.array((1.0, 2.0, 3.0))),
      ('124', np.array((1.0, -2.0, 4.0))),
      ('357', np.array((3.0, 5.0, 7.0))),
      ('10s', np.array((10.0, 100.0, 1000.0))),
  ]
  named_vectors = _add_negative_named_values(named_vectors)
  named_vectors += [('0', np.zeros(3))]
  return named_vectors


def make_named_unit_vectors() -> List[NamedVectorType]:
  """Creates a list of (name, unit_vector) pairs."""
  named_vectors = []
  for name, v in make_named_vectors():
    v_norm = np.linalg.norm(v)
    if v_norm > vector_util.DEFAULT_ZERO_EPSILON:
      v = v / v_norm
      named_vectors += [(name, v)]
  return named_vectors


def make_named_tiny_vectors() -> List[NamedVectorType]:
  """Creates a list of (name, vector) pairs with tiny magnitude."""
  named_vectors = [('(0)', np.zeros(3))]
  named_vectors += [
      (('%s_eps' % name), _LESS_THAN_EPSILON * np.asarray(v))
      for name, v in make_named_unit_vectors()
  ]
  return named_vectors


def make_named_nonunit_quaternions() -> List[NamedQuaternionType]:
  """Creates a list of (name, Quaternion) pairs with magnitude != 0 or 1."""
  return [
      ('1111', quaternion.Quaternion([1, 1, 1, 1])),
      ('1234', quaternion.Quaternion([1, 2, 3, 4])),
      ('1100', quaternion.Quaternion([1, 1, 0, 0])),
      ('1001', quaternion.Quaternion([1, 0, 0, 1])),
      ('0101', quaternion.Quaternion([0, 1, 0, 1])),
      ('0011', quaternion.Quaternion([0, 0, 1, 1])),
      ('Odds', quaternion.Quaternion([0, 1, 0, 1])),
      ('PlusMinus', quaternion.Quaternion([1, -1, 1, -1])),
      ('Evens', quaternion.Quaternion([1, 0, 1, 0])),
      ('Count', quaternion.Quaternion(np.arange(1, 5))),
      ('Range', quaternion.Quaternion(np.arange(-2, -1, 0.25))),
      ('10s', quaternion.Quaternion([1, 10, 100, 1000])),
  ]


def make_named_tiny_quaternions() -> List[NamedQuaternionType]:
  """Creates a list of (name, Quaternion) pairs with tiny magnitude."""
  named_quaternions = [('0', quaternion.Quaternion([0, 0, 0, 0]))]
  named_quaternions += [
      (('%s_eps' % name), _LESS_THAN_EPSILON * q)
      for name, q in make_named_unit_quaternions()
  ]
  named_quaternions += [
      (('%s_eps' % name), _LESS_THAN_EPSILON * q.normalize())
      for name, q in make_named_nonunit_quaternions()
  ]
  return named_quaternions


def make_named_unit_quaternions() -> List[NamedQuaternionType]:
  """Creates a list of (name, unit Quaternion) pairs."""
  return [
      ('1', quaternion.Quaternion.one()),
      ('ijk120', quaternion.Quaternion([0.5, 0.5, 0.5, 0.5])),
      _make_named_input(quaternion.Quaternion([0.5, -0.5, 0.5, 0.5])),
      _make_named_input(quaternion.Quaternion([0.5, 0.5, -0.5, 0.5])),
      _make_named_input(quaternion.Quaternion([-0.1, 0.7, -0.5, 0.5])),
      _make_named_input(quaternion.Quaternion([0.6, 0, -0.8, 0])),
  ]


def make_named_rotations() -> List[NamedRotationType]:
  """Creates a list of (name, Rotation3) pairs."""
  return [
      (name, rotation3.Rotation3(quat))
      for name, quat in make_named_unit_quaternions()
      + make_named_nonunit_quaternions()
  ]


def make_named_tiny_rotations() -> List[NamedRotationType]:
  """Creates a list of (name, Rotation3) pairs with tiny angle."""
  eps_angle = _LESS_THAN_EPSILON
  return [
      ('1', rotation3.Rotation3()),
      ('i_eps', rotation3.Rotation3.from_axis_angle([1, 0, 0], eps_angle)),
      ('j_neps', rotation3.Rotation3.from_axis_angle([0, 1, 0], -eps_angle)),
      ('k_eps', rotation3.Rotation3.from_axis_angle([0, 0, 1], eps_angle)),
      ('ijk_eps', rotation3.Rotation3.from_axis_angle([1, 1, 1], eps_angle)),
      ('ijk_neps', rotation3.Rotation3.from_axis_angle([1, 1, 1], -eps_angle)),
      ('ij_eps', rotation3.Rotation3.from_axis_angle([1, -1, 0], eps_angle)),
      ('jk_eps', rotation3.Rotation3.from_axis_angle([0, 1, -1], eps_angle)),
      ('ki_eps', rotation3.Rotation3.from_axis_angle([-1, 0, 1], eps_angle)),
      ('123_eps', rotation3.Rotation3.from_axis_angle([1, 2, 3], eps_angle)),
  ]


def make_named_pose_inputs() -> List[NamedPoseInputType]:
  """Creates a list of (name, Rotation3, vector) triples."""
  named_rotations = make_named_rotations()
  named_vectors = make_named_vectors() * 2
  random.shuffle(named_vectors)
  named_pose_inputs = [(
      'identity',
      rotation3.Rotation3.identity(),
      np.zeros(3),
  )]
  for r, v in zip(named_rotations, named_vectors):
    name = '(%s, %s)' % (r[0], v[0])
    named_pose_inputs.append((name, r[1], v[1]))
  return named_pose_inputs


def make_named_poses() -> List[NamedPoseType]:
  """Creates a list of (name, Pose3) pairs."""
  named_pose_inputs = make_named_pose_inputs()
  return [(name, pose3.Pose3(q, v)) for name, q, v in named_pose_inputs]


def make_named_tiny_poses() -> List[NamedPoseType]:
  """Creates a list of (name, Pose3) pairs with tiny perturbation."""
  tiny_rotations = make_named_tiny_rotations()
  tiny_vectors = make_named_tiny_vectors()
  random.shuffle(tiny_vectors)
  named_poses = []
  for (rotation_name, rotation), (vector_name, vector) in zip(
      tiny_rotations, tiny_vectors
  ):
    pose_name = '(%s, %s)' % (rotation_name, vector_name)
    pose = pose3.Pose3(rotation, vector)
    named_poses.append((pose_name, pose))
  return named_poses


def make_test_vectors(
    dimension: int,
    values: Optional[math_types.VectorType] = None,
    number_of_random_vectors: int = 0,
    normalize: bool = False,
) -> np.ndarray:
  """Creates a set of vectors with some fixed and some random values.

  Generates test vectors with all combinations of the input values.  For
  example, if the input values are [-1, 1] and the dimension is 2, this function
  will generate [-1, -1], [-1, 1], [1, -1], [1, 1].

  Random vectors are created with independent normally distributed component
  values with mu=0, sigma=1.

  If normalize is True, zero vectors will be removed and all vectors will be
  scaled to magnitude 1.0.

  Exact duplicates are removed from the set.

  Args:
    dimension: Number of components in each vector.
    values: Component values for fixed vectors.  Defaults are [-1, 0, 1].
    number_of_random_vectors: Number of purely random vectors to create.
    normalize: Indicates whether to normalize vectors.

  Returns:
    n x dimension numpy array representing n vectors.
  """
  values = np.asarray(values or DEFAULT_TEST_VALUES, dtype=np.float64).flatten()
  logging.debug('values: %s %s', values.shape, values)
  values_grid = np.repeat([values], dimension, axis=0)
  vectors = np.array(np.meshgrid(*values_grid)).T.reshape(-1, dimension)
  if number_of_random_vectors > 0:
    vectors = np.vstack(
        (vectors, np.random.normal(size=(number_of_random_vectors, dimension)))
    )
  if normalize:
    # Remove zero vectors.
    vectors = vectors[np.where(np.any(vectors, axis=1))]
    # Scale vectors to magnitude 1.0.
    vectors /= np.linalg.norm(vectors, axis=1)[:, np.newaxis]
  # Remove duplicates.  This sorts the vectors.
  vectors = np.unique(vectors, axis=0)
  logging.debug('test vectors: %s  First 20:\n%s', vectors.shape, vectors[:20])
  return vectors


# ===========================================================================
# TestCase class
# ===========================================================================


class TestCase(absltest.TestCase):
  """Base class for tests in pymath library.

  Assertions for array comparisons:
    assert_all_less_equal
    assert_all_greater_equal
    assert_all_less
    assert_all_greater
    assert_all_equal
    assert_all_close

    All array comparison functions take arguments:
      lhs: Left hand side argument of the comparison
      rhs: Right hand side argument of the comparison
      err_msg: String message to be displayed in the case of assertion failure.

    The lhs and rhs arguments may be arrays or scalars.

    If one of lhs or rhs is a scalar, it will be converted to an array with the
    same shape as the other argument.

    If both of lhs and rhs are arrays, they must have the same shape.

  Assertions for bound checks:
    assert_value_in_interval
    assert_vector_is_normalizedzed
  """

  longMessage = True

  def perturb_value(
      self, value: float, perturbation=_GREATER_THAN_EPSILON
  ) -> float:
    """Perturbs the value so that it will return False for isclose.

    Adds sufficient relative and absolute error to the value so that
      isclose(value, perturbed_value, rtol=epsilon, atol=epsilon) will return
      False for epsilon > |perturbation| * 2 and
      True for epsilon < |perturbation| / 2.

    Perturbation value can be positive or negative.

    Absolute value of perturbation should be less than one.

    Args:
      value: Value to be perturbed.
      perturbation: Amount of relative and absolute error to introduce.

    Returns:
      Perturbed value.
    """
    return value + perturbation * (1.0 + abs(value))

  def assert_close(
      self,
      lhs: float,
      rhs: float,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that lhs is near to rhs within tolerances.

    Args:
      lhs: Left hand side scalar value.
      rhs: Right hand side scalar value.
      rtol: relative error tolerance, passed through to np.isclose.
      atol: absolute error tolerance, passed through to np.isclose.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the comparison fails.
    """
    self.assertTrue(
        np.isclose(lhs, rhs, rtol=rtol, atol=atol),
        '%s: %g != %g (delta=%g) within rtol=%g, atol=%g %s'
        % (
            ASSERT_VALUE_CLOSE_MESSAGE,
            lhs,
            rhs,
            rhs - lhs,
            rtol,
            atol,
            err_msg,
        ),
    )

  def assert_not_close(
      self,
      lhs: float,
      rhs: float,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that lhs is not near to rhs within tolerances.

    Args:
      lhs: Left hand side scalar value.
      rhs: Right hand side scalar value.
      rtol: relative error tolerance, passed through to np.isclose.
      atol: absolute error tolerance, passed through to np.isclose.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the comparison fails.
    """
    self.assertFalse(
        np.isclose(lhs, rhs, rtol=rtol, atol=atol),
        '%s: %g == %g (delta=%g) within rtol=%g, atol=%g %s'
        % (
            ASSERT_VALUE_NOT_CLOSE_MESSAGE,
            lhs,
            rhs,
            rhs - lhs,
            rtol,
            atol,
            err_msg,
        ),
    )

  def _assert_all_error_message(
      self,
      lhs: np.ndarray,
      rhs: np.ndarray,
      match: np.ndarray,
      err_msg: Text = '',
  ) -> Text:
    """Generates an error message describing mismatch locations.

    For example, if there is a single mismatch at position 10,10, where
    lhs[10][10] = 0 and rhs[10][10] = 1, this message will be generated:

       mismatch positions = (array([10]), array([10]))
       mismatch values:
         lhs = [ 0.]
         rhs = [ 1.]
         lhs - rhs = [ -1.]

    This is useful for finding sparse mismatches and near matches in large
    arrays.

    Args:
      lhs: Left hand side array argument.
      rhs: Right hand side array argument, the same shape as lhs.
      match: An array of boolean values indicating which values of lhs and rhs
        satisfy an operation.
      err_msg: Error message string appended to exception error message.

    Returns:
      An error message describing mismatch locations.
    """
    if np.all(match):
      return ''
    else:
      where_different = np.where(np.logical_not(match))
      x = lhs[where_different]
      y = rhs[where_different]
      return (
          '\nmismatch positions = %s\n'
          'mismatch values:\n'
          '  lhs = %s\n'
          '  rhs = %s\n'
          '  lhs - rhs = %s\n%s' % (where_different, x, y, x - y, err_msg)
      )

  def _assert_all(
      self,
      lhs: np.ndarray,
      rhs: np.ndarray,
      match: np.ndarray,
      op,
      header: Text,
      err_msg: Text = '',
  ) -> None:
    """Builds a detailed error message and calls the numpy assertion.

    This utility function is used by all of the array comparison assertions.  It
    generates a detailed error message showing the location and array values of
    any mismatches.

    Args:
      lhs: Left hand side array argument.
      rhs: Right hand side array argument, the same shape as lhs.
      match: An array of boolean values indicating which values of lhs and rhs
        satisfy the operation.
      op: Comparison operation on values (e.g. operator.__lt__).
      header: Header string used in numpy error messages.
      err_msg: Error message string appended to numpy error messages.
    """
    np.testing.assert_array_compare(
        op,
        lhs,
        rhs,
        err_msg=self._assert_all_error_message(lhs, rhs, match, err_msg),
        header=header,
        equal_inf=False,
    )

  def assert_equal_shape(
      self, lhs: np.ndarray, rhs: np.ndarray, err_msg: Text = ''
  ) -> None:
    """Asserts that the two numpy arrays have the same shape.

    Args:
      lhs: Left hand side numpy array argument.
      rhs: Right hand side numpy array argument.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arrays do not have the same shape.
    """
    self.assertEqual(
        lhs.shape,
        rhs.shape,
        msg='Shape mismatch: lhs.shape = %s, rhs.shape = %s. %s'
        % (lhs.shape, rhs.shape, err_msg),
    )

  def assert_all_less_equal(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      err_msg: Text = '',
  ) -> None:
    """Asserts that all elements of lhs are <= corresponding elements of rhs.

      lhs[i] <= rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    self._assert_all(
        lhs,
        rhs,
        match=(lhs <= rhs),
        op=operator.__le__,
        header=ASSERT_ARRAY_LE_MESSAGE,
        err_msg=err_msg,
    )

  def assert_all_greater_equal(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      err_msg: Text = '',
  ) -> None:
    """Asserts that all elements of lhs are >= corresponding elements of rhs.

      lhs[i] >= rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    self._assert_all(
        lhs,
        rhs,
        match=(lhs >= rhs),
        op=operator.__ge__,
        header=ASSERT_ARRAY_GE_MESSAGE,
        err_msg=err_msg,
    )

  def assert_all_less(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      err_msg: Text = '',
  ) -> None:
    """Asserts that all elements of lhs are < corresponding elements of rhs.

      lhs[i] < rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    self._assert_all(
        lhs,
        rhs,
        match=(lhs < rhs),
        op=operator.__lt__,
        header=ASSERT_ARRAY_LT_MESSAGE,
        err_msg=err_msg,
    )

  def assert_all_greater(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      err_msg: Text = '',
  ) -> None:
    """Asserts that all elements of lhs are > corresponding elements of rhs.

      lhs[i] > rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    self._assert_all(
        lhs,
        rhs,
        match=(lhs > rhs),
        op=operator.__gt__,
        header=ASSERT_ARRAY_GT_MESSAGE,
        err_msg=err_msg,
    )

  def assert_all_equal(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      err_msg: Text = '',
  ) -> None:
    """Asserts that elements of lhs are equal to corresponding elements of rhs.

      lhs[i] == rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    np.testing.assert_array_equal(
        lhs,
        rhs,
        err_msg=self._assert_all_error_message(
            lhs, rhs, match=(lhs == rhs), err_msg=err_msg
        ),
    )

  def assert_all_close(
      self,
      lhs: math_types.VectorOrValueType,
      rhs: math_types.VectorOrValueType,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that elements of lhs are near to corresponding elements of rhs.

      lhs[i] ~ rhs[i] for all i

    Each of lhs or rhs can either be a scalar value or an array.  If they are
    both arrays, they must have the same shape.

    Args:
      lhs: Left hand side scalar value or array.
      rhs: Right hand side scalar value or array.
      rtol: relative error tolerance, passed through to np.isclose.
      atol: absolute error tolerance, passed through to np.isclose.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the arguments are not compatible or the comparison
       fails.
    """
    lhs, rhs = math_types.get_matching_arrays(lhs, rhs, err_msg=err_msg)
    close = np.isclose(lhs, rhs, rtol=rtol, atol=atol)
    np.testing.assert_allclose(
        lhs,
        rhs,
        rtol=rtol,
        atol=atol,
        err_msg=ASSERT_ARRAY_CLOSE_MESSAGE
        + self._assert_all_error_message(
            lhs, rhs, match=close, err_msg=err_msg
        ),
    )

  def assert_angles_close(
      self,
      angle_1: float,
      angle_2: float,
      circle_angle: float,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that two angles are nearly equivalent.

    The circle_angle argument defines the units of the angles.  A value of 2*pi
    indicates the units of the angles are radians.  A value of 360 indicates the
    units of the angles are degrees.

    (angle + circle_angle) and (angle - circle_angle) are equivalent to angle.

    Args:
      angle_1: First angle.
      angle_2: Second angle.
      circle_angle: Total angle of a circle.  Should be 2*pi if the angles are
        in radians and 360 if the angles are in degrees
      rtol: relative error tolerance, passed through to np.isclose.
      atol: absolute error tolerance, passed through to np.isclose.
      err_msg: Error message displayed if the assertion fails.
    """
    if np.isclose(angle_1, angle_2, rtol=rtol, atol=atol):
      return
    half_circle = circle_angle * 0.5
    # The angle difference rotated to [-pi, pi] or [-180, 180].
    delta_angle = (
        np.remainder((angle_2 - angle_1) + half_circle, circle_angle)
        - half_circle
    )
    np.testing.assert_allclose(
        delta_angle,
        0.0,
        rtol=rtol,
        atol=atol,
        err_msg=(
            '%s %g != %g %s'
            % (ANGLE_NOT_CLOSE_MESSAGE, angle_1, angle_2, err_msg)
        ),
    )

  def assert_angles_in_radians_close(
      self,
      angle_1: float,
      angle_2: float,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Checks that two angles, represented in radians, are equivalent."""
    return self.assert_angles_close(
        angle_1,
        angle_2,
        circle_angle=2 * np.pi,
        rtol=rtol,
        atol=atol,
        err_msg=err_msg,
    )

  def assert_angles_in_degrees_close(
      self,
      angle_1: float,
      angle_2: float,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Checks that two angles, represented in degrees, are equivalent."""
    return self.assert_angles_close(
        angle_1,
        angle_2,
        circle_angle=360,
        rtol=rtol,
        atol=atol,
        err_msg=err_msg,
    )

  def assert_vector_is_normalized(
      self,
      vector: math_types.VectorType,
      norm_epsilon: float = vector_util.DEFAULT_NORM_EPSILON,
      err_msg: Text = '',
  ) -> None:
    """Asserts that |vector| = 1.0 within norm_epsilon.

    If the assertion fails, it will result in an error message that matches
    the regular expression described in NOT_NORMALIZED_MESSAGE.

    Args:
      vector: A one-dimensional array of values that should have magnitude 1.
      norm_epsilon: Tolerance on the error of the magnitude.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the vector is not normalized.
    """
    self.assertTrue(
        vector_util.is_vector_normalized(vector, norm_epsilon),
        msg='Vector is not normalized within %g: |%r| = %g %s'
        % (norm_epsilon, (vector,), np.linalg.norm(vector), err_msg),
    )

  def assert_quaternion_is_normalized(
      self,
      quat: quaternion.Quaternion,
      norm_epsilon: float = vector_util.DEFAULT_NORM_EPSILON,
      err_msg: Text = '',
  ) -> None:
    """Asserts that |quat| = 1.0 within norm_epsilon.

    If the assertion fails, it will result in an error message that matches
    the pattern in QUATERNION_NOT_NORMALIZED_MESSAGE.

    Args:
      quat: A Quaternion that should have magnitude 1.
      norm_epsilon: Tolerance on the error of the magnitude.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the quaternion is not normalized.
    """
    self.assertTrue(
        quat.is_normalized(norm_epsilon),
        '%s: |%r| = %g not within %g of 1.0  %s'
        % (
            quaternion.QUATERNION_NOT_NORMALIZED_MESSAGE,
            (quat,),
            np.linalg.norm(quat.xyzw),
            norm_epsilon,
            err_msg,
        ),
    )

  def assert_rotation_close(
      self,
      rotation_1: rotation3.Rotation3,
      rotation_2: rotation3.Rotation3,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that the two rotations are approximately equivalent.

    If the assertion fails, it will result in an error message that matches
    the pattern in ROTATION_NOT_CLOSE_MESSAGE.

    Args:
      rotation_1: First rotation in comparison.
      rotation_2: Second rotation in comparison.
      rtol: relative error tolerance, passed through to np.allclose.
      atol: absolute error tolerance, passed through to np.allclose.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the two rotations are not equivalent within epsilon.
    """
    logging.debug(
        '\nrotation_1: %r\nrotation_2: %r\ndelta rotation: %r',
        rotation_1,
        rotation_2,
        rotation_2.inverse() * rotation_1,
    )
    self.assertTrue(
        rotation_1.almost_equal(rotation_2, rtol=rtol, atol=atol),
        '%s: %r =! %r with rtol=%g, atol=%g delta=%r %s'
        % (
            ROTATION_NOT_CLOSE_MESSAGE,
            rotation_1,
            rotation_2,
            rtol,
            atol,
            rotation_2.inverse() * rotation_1,
            err_msg,
        ),
    )

  def assert_pose_close(
      self,
      pose_1: pose3.Pose3,
      pose_2: pose3.Pose3,
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
      err_msg: Text = '',
  ) -> None:
    """Asserts that the two poses are approximately equivalent.

    If the assertion fails, it will result in an error message that matches
    the pattern in POSE_NOT_CLOSE_MESSAGE.

    Args:
      pose_1: First pose in comparison.
      pose_2: Second pose in comparison.
      rtol: relative error tolerance, passed through to np.allclose.
      atol: absolute error tolerance, passed through to np.allclose.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If the two poses are not equivalent within epsilon.
    """
    logging.debug(
        '\npose_1: %r\npose_2: %r\ndelta pose: %r',
        pose_1,
        pose_2,
        pose_2.inverse().multiply(pose_1),
    )
    self.assertTrue(
        pose_1.almost_equal(pose_2, rtol=rtol, atol=atol),
        '%s: %r =! %r with rtol=%g, atol=%g delta=%r %s'
        % (
            POSE_NOT_CLOSE_MESSAGE,
            pose_1,
            pose_2,
            rtol,
            atol,
            pose_2.inverse().multiply(pose_1),
            err_msg,
        ),
    )

  # --------------------------------------------------------------------------
  # Geometric assertions.
  # --------------------------------------------------------------------------

  def assert_empty(self, obj, empty: bool = True, err_msg='') -> None:
    """Asserts that obj.empty == empty."""
    self.assertEqual(
        obj.empty,
        empty,
        msg='%s %s\n%s'
        % (
            obj,
            (ASSERT_EMPTY_MESSAGE if empty else ASSERT_NOT_EMPTY_MESSAGE),
            err_msg,
        ),
    )

  def assert_not_empty(self, obj, err_msg='') -> None:
    """Asserts that obj.empty is False."""
    self.assert_empty(obj, empty=False, err_msg=err_msg)

  def assert_contains(
      self, obj1, obj2, contains: bool = True, err_msg=''
  ) -> None:
    """Asserts that obj1.contains(obj2) == contains."""
    self.assertEqual(
        obj1.contains(obj2),
        contains,
        msg='%s %s %s\n%s'
        % (
            obj1,
            (
                ASSERT_CONTAINS_MESSAGE
                if contains
                else ASSERT_NOT_CONTAINS_MESSAGE
            ),
            obj2,
            err_msg,
        ),
    )

  def assert_not_contains(self, obj1, obj2, err_msg='') -> None:
    """Asserts that obj1.contains(obj2) is False."""
    self.assert_contains(obj1, obj2, contains=False, err_msg=err_msg)

  def assert_intersects(
      self, obj1, obj2, intersects: bool = True, err_msg=''
  ) -> None:
    """Asserts that obj1.intersects(obj2) == intersects."""
    self.assertEqual(
        obj1.intersects(obj2),
        intersects,
        msg='%s %s %s\n%s'
        % (
            obj1,
            (
                ASSERT_INTERSECTS_MESSAGE
                if intersects
                else ASSERT_NOT_INTERSECTS_MESSAGE
            ),
            obj2,
            err_msg,
        ),
    )

  def assert_not_intersects(self, obj1, obj2, err_msg='') -> None:
    """Asserts that obj1.intersects(obj2) is False."""
    self.assert_intersects(obj1, obj2, intersects=False, err_msg=err_msg)

  # --------------------------------------------------------------------------
  # Checks for validity of standard functions.
  # --------------------------------------------------------------------------

  def check_eq_and_ne_for_equal_values(
      self, value1, value2, err_msg: Text = ''
  ) -> None:
    """Asserts that __eq__ and __ne__ are correct for two equal values.

    Validates symmetry and definitions for the functions: __eq__ and __ne__ for
    two arguments that are known to be equal.

    Args:
      value1: First value to be compared.
      value2: Second value to be compared, equal to value1.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If either test fails..
    """
    self.assertEqual(
        value1,
        value2,
        '%s: %r == %r  %s' % (ASSERT_EQ_MESSAGE, value1, value2, err_msg),
    )
    self.assertEqual(
        value2,
        value1,
        '%s: %r == %r  %s' % (ASSERT_EQ_MESSAGE, value2, value1, err_msg),
    )
    # ------------------------------------------------------------------------
    # These lines explicitly validate the definition of __ne__.
    # pylint: disable=g-generic-assert
    self.assertFalse(
        value1 != value2,
        '%s: %r != %r  %s' % (ASSERT_NE_MESSAGE, value1, value2, err_msg),
    )
    self.assertFalse(
        value2 != value1,
        '%s: %r != %r  %s' % (ASSERT_NE_MESSAGE, value2, value1, err_msg),
    )
    # pylint: enable=g-generic-assert
    # ------------------------------------------------------------------------

  def check_eq_and_ne_for_unequal_values(
      self, value1, value2, err_msg: Text = ''
  ) -> None:
    """Asserts that __eq__ and __ne__ are correct for two unequal values.

    Validates symmetry and definitions for the functions: __eq__ and __ne__ for
    two arguments that are known to be unequal.

    Args:
      value1: First value to be compared.
      value2: Second value to be compared, not equal to value1.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If either test fails..
    """
    self.assertNotEqual(
        value1,
        value2,
        '%s: %r != %r  %s' % (ASSERT_NE_MESSAGE, value1, value2, err_msg),
    )
    self.assertNotEqual(
        value2,
        value1,
        '%s: %r != %r  %s' % (ASSERT_NE_MESSAGE, value2, value1, err_msg),
    )
    # ------------------------------------------------------------------------
    # These lines explicitly validate the definition of __eq__.
    # pylint: disable=g-generic-assert
    self.assertFalse(
        value1 == value2,
        '%s: %r == %r  %s' % (ASSERT_EQ_MESSAGE, value1, value2, err_msg),
    )
    self.assertFalse(
        value2 == value1,
        '%s: %r == %r  %s' % (ASSERT_EQ_MESSAGE, value2, value1, err_msg),
    )
    # pylint: enable=g-generic-assert
    # ------------------------------------------------------------------------

  def check_hash_for_equal_values(
      self, value1, value2, err_msg: Text = ''
  ) -> None:
    """Asserts that the hash values for two equal values are equal.

    The first assertion tests that the function is being called correctly.
    The second assertion tests that the hash function is defined correctly.

    Args:
      value1: First value to be compared.
      value2: Second value to be compared.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If either test fails..
    """
    self.check_eq_and_ne_for_equal_values(value1, value2, err_msg)
    self.assertEqual(
        hash(value1),
        hash(value2),
        '%s: %r == %r  %s' % (ASSERT_EQ_HASH_MESSAGE, value1, value2, err_msg),
    )

  def check_hash_for_unequal_values(
      self, value1, value2, err_msg: Text = ''
  ) -> None:
    """Asserts that the hash values for two unequal values are not equal.

    This function should only be called with DETERMINISTIC TEST VALUES in order
    to avoid intermittent test failures, as hash values are not guaranteed to be
    unique.

    The first assertion tests that the function is being called correctly.
    The second assertion tests that the hash function is defined correctly.

    Args:
      value1: First value to be compared.
      value2: Second value to be compared.
      err_msg: Error message displayed if the assertion fails.

    Raises:
      AssertionError: If either test fails..
    """
    self.check_eq_and_ne_for_unequal_values(value1, value2, err_msg)
    self.assertNotEqual(
        hash(value1),
        hash(value2),
        '%s: %r != %r  %s' % (ASSERT_NE_HASH_MESSAGE, value1, value2, err_msg),
    )
