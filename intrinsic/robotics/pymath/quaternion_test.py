# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.robotics.pymath.quaternion."""

from collections import abc

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import text_format
from intrinsic.robotics.messages import quaternion_pb2
from intrinsic.robotics.pymath import math_test
from intrinsic.robotics.pymath import quaternion
from intrinsic.robotics.pymath import vector_util
import numpy as np

# An error of this magnitude should not trigger failures on checks for
# normalized quaternions.
_LESS_THAN_NORM_EPSILON = quaternion.QUATERNION_NORM_EPSILON * 0.5

_QUAT_0 = quaternion.Quaternion.zero()
_QUAT_1 = quaternion.Quaternion.one()
_QUAT_I = quaternion.Quaternion.i()
_QUAT_J = quaternion.Quaternion.j()
_QUAT_K = quaternion.Quaternion.k()
_QUAT_ONES = quaternion.Quaternion([1, 1, 1, 1])
_QUAT_HALF = quaternion.Quaternion([0.5, 0.5, 0.5, 0.5])


def _quaternion_proto(quat_proto_txt):
  """Creates a Quaterniond protobuf from the input prototxt."""
  return text_format.Parse(quat_proto_txt, quaternion_pb2.Quaterniond())


# Named test parameters.
_UNIT_QUATERNIONS = math_test.make_named_unit_quaternions()
_NON_UNIT_QUATERNIONS = math_test.make_named_nonunit_quaternions()
_NON_ZERO_QUATERNIONS = _UNIT_QUATERNIONS + _NON_UNIT_QUATERNIONS
_TINY_QUATERNIONS = math_test.make_named_tiny_quaternions()
_TEST_QUATERNIONS = _TINY_QUATERNIONS + _NON_ZERO_QUATERNIONS


class QuaternionTest(parameterized.TestCase, math_test.TestCase):

  @parameterized.named_parameters(
      ('Zero', [0, 0, 0, 0]),
      ('Identity', [0, 0, 0, 1]),
      ('Twos', np.array([2, 2, 2, 2])),
      ('Half', (0.5, 0.5, -0.5, -0.5)),
      ('Count', range(4)),
      ('Range', np.arange(-2, -1, 0.25)),
  )
  def test_init(self, xyzw):
    """Tests Quaternion.__init__ and x, y, z, w properties."""
    x, y, z, w = xyzw
    q = quaternion.Quaternion(xyzw=xyzw)
    self.assertEqual(q.x, x)
    self.assertEqual(q.y, y)
    self.assertEqual(q.z, z)
    self.assertEqual(q.w, w)
    self.assert_all_equal(q.xyzw, xyzw)

  def test_init_default(self):
    self.assertEqual(quaternion.Quaternion(), quaternion.Quaternion.zero())

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_init_normalized(self, quat):
    """Tests Quaternion.__init__ and x, y, z, w properties."""
    q_normalized_init = quaternion.Quaternion(xyzw=quat.xyzw, normalize=True)
    q_normalized = quat.normalize()
    self.assertEqual(q_normalized_init, q_normalized)

  @parameterized.named_parameters(
      ('too many', np.arange(5)),
      ('too few', np.arange(3)),
  )
  def test_init_error_components(self, components):
    """Tests Quaternion.__init__ exceptions."""
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        quaternion.Quaternion,
        components,
    )

  def test_init_error_values(self):
    """Tests Quaternion.__init__ exceptions."""
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_INFINITE_VALUES_MESSAGE,
        quaternion.Quaternion,
        [0, 0, 1, np.inf],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_VALUES_MESSAGE,
        quaternion.Quaternion,
        [0, 0, 1, np.nan],
    )

  @parameterized.named_parameters(
      ('zero', np.zeros(4)),
      ('tiny', np.full(4, 1e-12)),
      ('-tiny', np.full(4, -1e-12)),
  )
  def test_init_error_cant_normalize(self, components):
    """Tests Quaternion.__init__ exceptions."""
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_ZERO_MESSAGE,
        quaternion.Quaternion,
        components,
        True,
    )

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_xyzw(self, quat):
    initial_xyzw = quat.xyzw.copy()
    quat_copy = quaternion.Quaternion(initial_xyzw)
    self.assertEqual(quat_copy, quat)
    self.assert_all_equal(quat.xyzw, initial_xyzw)
    self.assert_all_equal(quat_copy.xyzw, initial_xyzw)
    quat.xyzw[0] = 123456
    quat_copy.xyzw[1] = 123456
    self.assertEqual(quat_copy, quat)
    self.assert_all_equal(quat.xyzw, initial_xyzw)
    self.assert_all_equal(quat_copy.xyzw, initial_xyzw)
    initial_xyzw[2] = 123456
    self.assertEqual(quat_copy, quat)

  def test_real(self):
    self.assertEqual(_QUAT_1.real, 1.0)
    self.assertEqual((-_QUAT_1).real, -1.0)
    self.assertEqual(_QUAT_I.real, 0.0)
    self.assertEqual(_QUAT_J.real, 0.0)
    self.assertEqual(_QUAT_K.real, 0.0)

  def test_imag(self):
    self.assertLen(_QUAT_1.imag, 3)
    self.assert_all_equal(_QUAT_1.imag, 0.0)
    self.assert_all_equal(_QUAT_I.imag, [1.0, 0.0, 0.0])
    self.assert_all_equal(_QUAT_J.imag, [0.0, 1.0, 0.0])
    self.assert_all_equal(_QUAT_K.imag, [0.0, 0.0, 1.0])

  @parameterized.parameters(
      (_QUAT_1, _QUAT_1),
      (_QUAT_0, _QUAT_0),
      (_QUAT_I, -_QUAT_I),
      (_QUAT_J, -_QUAT_J),
      (_QUAT_K, -_QUAT_K),
      (
          quaternion.Quaternion([1, 2, 3, 4]),
          quaternion.Quaternion([-1, -2, -3, 4]),
      ),
  )
  def test_conjugate(self, quat, quat_conjugate):
    """Tests Quaternion.conjugate property."""
    self.assertEqual(quat.conjugate, quat_conjugate)
    self.assertEqual(quat, quat_conjugate.conjugate)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_norm_squared(self, quat):
    norm = quat.norm()
    norm_squared = quat.norm_squared()
    self.assertAlmostEqual(norm**2, norm_squared)
    self.assertAlmostEqual((quat * quat).norm(), norm_squared)

  @parameterized.parameters(
      (_QUAT_1, _QUAT_1),
      (_QUAT_I, -_QUAT_I),
      (_QUAT_J, -_QUAT_J),
      (_QUAT_K, -_QUAT_K),
      (
          quaternion.Quaternion([-0.5, 0.5, -0.5, 0.5]),
          quaternion.Quaternion([0.5, -0.5, 0.5, 0.5]),
      ),
      (
          quaternion.Quaternion([-2, -2, 2, -2]),
          quaternion.Quaternion([0.125, 0.125, -0.125, -0.125]),
      ),
  )
  def test_inverse(self, quat, quat_inverse):
    """Checks that the inverse functions are correct.

    Args:
      quat: A Quaternion to be evaluated.
      quat_inverse: The expected inverse.
    """
    logging.debug('quat=%s, quat_inverse=%s', quat, quat_inverse)
    self.assertEqual(quat_inverse, quat.inverse())
    self.assertEqual(quat, quat_inverse.inverse())
    self.assertEqual(quat * quat_inverse, _QUAT_1)
    self.assertEqual(quat_inverse * quat, _QUAT_1)

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_inverse_close(self, quat):
    quat_inverse = quat.inverse()
    self.assertAlmostEqual(quat * quat_inverse, _QUAT_1)
    self.assertAlmostEqual(quat_inverse * quat, _QUAT_1)

  @parameterized.named_parameters(*_TINY_QUATERNIONS)
  def test_inverse_errors(self, quat):
    """Checks that the inverse raises correct exceptions on zero quaternions."""
    logging.debug('quat=%s', quat)
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.inverse
    )

  @parameterized.named_parameters(*_UNIT_QUATERNIONS)
  def test_inverse_unit(self, quat):
    self.assertEqual(quat.norm(), 1.0)
    self.assertEqual(quat.inverse(), quat.conjugate)
    self.assertTrue(quat.is_normalized())
    self.assert_quaternion_is_normalized(quat)

  def test_equal(self):
    self.assertEqual(_QUAT_I, _QUAT_I)
    self.assertEqual(_QUAT_J, _QUAT_J)
    self.assertNotEqual(_QUAT_I, _QUAT_J)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_eq(self, quat):
    self.check_eq_and_ne_for_equal_values(quat, quat)
    self.check_eq_and_ne_for_equal_values(
        quat, quaternion.Quaternion(quat.xyzw.copy())
    )

  def test_eq_other_type(self):
    self.assertNotEqual(_QUAT_I, 'string')

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_ne(self, quat):
    for _, delta in _NON_ZERO_QUATERNIONS:
      with self.subTest(delta=delta):
        self.check_eq_and_ne_for_unequal_values(quat, quat + delta)
        self.check_eq_and_ne_for_unequal_values(quat, quat - delta)
        self.check_eq_and_ne_for_unequal_values(quat, quat + delta * 1e-6)
        self.check_eq_and_ne_for_unequal_values(quat, quat - delta * 1e-6)

  def test_hash(self):
    self.assertFalse(issubclass(quaternion.Quaternion, abc.Hashable))

  @parameterized.parameters(
      (_QUAT_I, _QUAT_J, _QUAT_K),
      (_QUAT_J, _QUAT_K, _QUAT_I),
      (_QUAT_K, _QUAT_I, _QUAT_J),
      (_QUAT_I, _QUAT_K, -_QUAT_J),
      (_QUAT_J, _QUAT_I, -_QUAT_K),
      (_QUAT_K, _QUAT_J, -_QUAT_I),
      (_QUAT_I, _QUAT_I, -_QUAT_1),
      (_QUAT_J, _QUAT_J, -_QUAT_1),
      (_QUAT_K, _QUAT_K, -_QUAT_1),
      (_QUAT_ONES, _QUAT_ONES, quaternion.Quaternion([2, 2, 2, -2])),
      (
          quaternion.Quaternion([1, 2, 0, 0]),
          quaternion.Quaternion([0, 1, -3, 0]),
          quaternion.Quaternion([-6, 3, 1, -2]),
      ),
      (
          quaternion.Quaternion([1, 0, 2, 0]),
          quaternion.Quaternion([1, 3, 5, 7]),
          quaternion.Quaternion([1.0, -3.0, 17.0, -11.0]),
      ),
      (
          quaternion.Quaternion([1, 0, 0.5, 2]),
          quaternion.Quaternion([0, -1, 0.25, 0]),
          quaternion.Quaternion([0.5, -2.25, -0.5, -0.125]),
      ),
  )
  def test_multiply(self, op1, op2, product):
    """Verifies quaternion product."""
    self.assertEqual(op1 * op2, product)
    self.assertEqual(op2.conjugate * op1.conjugate, product.conjugate)
    self.assertEqual(-op1 * op2, -product)
    self.assertEqual(op1 * -op2, -product)
    self.assertEqual(-op1 * -op2, product)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_matrices(self, quat1):
    for _, quat2 in _TEST_QUATERNIONS:
      with self.subTest(quat2=quat2):
        product = quat1 * quat2
        self.assertAlmostEqual(
            quaternion.Quaternion(
                np.matmul(quat1.left_multiplication_matrix(), quat2.xyzw)
            ),
            product,
        )
        self.assertAlmostEqual(
            quaternion.Quaternion(
                np.matmul(quat2.right_multiplication_matrix(), quat1.xyzw)
            ),
            product,
        )

  @parameterized.parameters(
      (_QUAT_1, 2, [0, 0, 0, 2]),
      (_QUAT_I, -1, [-1, 0, 0, 0]),
      (_QUAT_J, 3, [0, 3, 0, 0]),
      (_QUAT_K, 0.5, [0, 0, 0.5, 0]),
      (_QUAT_ONES, 0.1, [0.1, 0.1, 0.1, 0.1]),
  )
  def test_multiply_scalar(self, quat, scalar, product_xyzw):
    """Verifies quaternion product with a scalar."""
    product = quaternion.Quaternion(product_xyzw)
    self.assertEqual(quat * scalar, product)
    self.assertEqual(scalar * quat, product)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_multiply_zero(self, quat):
    self.assertEqual(quat * _QUAT_0, _QUAT_0)
    self.assertEqual(_QUAT_0 * quat, _QUAT_0)
    self.assertEqual(quat * 0.0, _QUAT_0)
    self.assertEqual(quat * 0, _QUAT_0)
    self.assertEqual(0.0 * quat, _QUAT_0)
    self.assertEqual(0 * quat, _QUAT_0)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_multiply_one(self, quat):
    self.assertEqual(quat * _QUAT_1, quat)
    self.assertEqual(_QUAT_1 * quat, quat)
    self.assertEqual(quat * 1.0, quat)
    self.assertEqual(quat * 1, quat)
    self.assertEqual(1.0 * quat, quat)
    self.assertEqual(1 * quat, quat)

  @parameterized.parameters(
      (_QUAT_I, _QUAT_J, -_QUAT_K),
      (_QUAT_J, _QUAT_K, -_QUAT_I),
      (_QUAT_K, _QUAT_I, -_QUAT_J),
      (_QUAT_I, _QUAT_K, _QUAT_J),
      (_QUAT_J, _QUAT_I, _QUAT_K),
      (_QUAT_K, _QUAT_J, _QUAT_I),
      (_QUAT_I, _QUAT_I, _QUAT_1),
      (_QUAT_J, _QUAT_J, _QUAT_1),
      (_QUAT_K, _QUAT_K, _QUAT_1),
      (
          quaternion.Quaternion([1, -1, 1, -1]),
          quaternion.Quaternion([-1, 1, 1, -1]),
          _QUAT_J,
      ),
  )
  def test_divide(self, op1, op2, quotient):
    """Verifies quaternion quotient."""
    self.assertEqual(op1 / op2, quotient)
    self.assertEqual(-op1 / op2, -quotient)
    self.assertEqual(op1 / -op2, -quotient)
    self.assertEqual(-op1 / -op2, quotient)

  @parameterized.parameters(
      (_QUAT_1, 0.5, [0, 0, 0, 2]),
      (_QUAT_I, -1, [-1, 0, 0, 0]),
      (_QUAT_J, 0.25, [0, 4, 0, 0]),
      (_QUAT_K, 2, [0, 0, 0.5, 0]),
      (_QUAT_ONES, 10.0, [0.1, 0.1, 0.1, 0.1]),
  )
  def test_divide_scalar(self, quat, scalar, product_xyzw):
    """Verifies quaternion product with a scalar."""
    product = quaternion.Quaternion(product_xyzw)
    self.assertEqual(quat / scalar, product)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_divide_zero(self, quat):
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.divide, _QUAT_0
    )
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.divide, 0
    )
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.divide, 0.0
    )

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_divide_one(self, quat):
    self.assertEqual(quat / _QUAT_1, quat)
    self.assertEqual(quat / 1.0, quat)
    self.assertEqual(quat / 1, quat)
    self.assertEqual(1.0 / quat, quat.inverse())
    self.assertAlmostEqual(quat / quat, _QUAT_1)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_add(self, quat):
    self.assertEqual(quat + quat, 2 * quat)
    self.assertEqual(
        quat + _QUAT_I, quaternion.Quaternion(quat.xyzw + [1, 0, 0, 0])
    )
    self.assertEqual(
        quat + _QUAT_J, quaternion.Quaternion(quat.xyzw + [0, 1, 0, 0])
    )
    self.assertEqual(
        quat + _QUAT_K, quaternion.Quaternion(quat.xyzw + [0, 0, 1, 0])
    )
    self.assertEqual(
        quat + _QUAT_1, quaternion.Quaternion(quat.xyzw + [0, 0, 0, 1])
    )

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_add_zero(self, quat):
    self.assertEqual(quat + _QUAT_0, quat)
    self.assertEqual(_QUAT_0 + quat, quat)
    self.assertEqual(quat + -quat, _QUAT_0)
    self.assertEqual(-quat + quat, _QUAT_0)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_sub(self, quat):
    self.assertEqual(quat - (-quat), 2 * quat)
    self.assertEqual(
        quat - _QUAT_I, quaternion.Quaternion(quat.xyzw + [-1, 0, 0, 0])
    )
    self.assertEqual(
        quat - _QUAT_J, quaternion.Quaternion(quat.xyzw + [0, -1, 0, 0])
    )
    self.assertEqual(
        quat - _QUAT_K, quaternion.Quaternion(quat.xyzw + [0, 0, -1, 0])
    )
    self.assertEqual(
        quat - _QUAT_1, quaternion.Quaternion(quat.xyzw + [0, 0, 0, -1])
    )

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_sub_zero(self, quat):
    self.assertEqual(quat - _QUAT_0, quat)
    self.assertEqual(_QUAT_0 - quat, -quat)
    self.assertEqual(quat - quat, _QUAT_0)

  @parameterized.parameters(
      ([1, 0, 0, 0], [1, 0, 0, 0]),
      ([-1, 0, 0, 0], [-1, 0, 0, 0]),
      ([1, 1, -1, 1], [0.5, 0.5, -0.5, 0.5]),
      ([10, -10, 10, 10], [0.5, -0.5, 0.5, 0.5]),
  )
  def test_normalize(self, xyzw, xyzw_normalized):
    q = quaternion.Quaternion(xyzw)
    q_normalized = quaternion.Quaternion(xyzw_normalized)
    self.assertAlmostEqual(q.normalize(), q_normalized)

  @parameterized.named_parameters(*_UNIT_QUATERNIONS)
  def test_normalize_unit_exact(self, q):
    self.assertEqual(q.norm(), 1)
    self.assertEqual(q, q.normalize())

  @parameterized.parameters(
      2 * _QUAT_I,
      3 * _QUAT_J,
      4 * _QUAT_K,
      0.25 * _QUAT_1,
      _QUAT_ONES,
  )
  def test_normalize_non_unit(self, q):
    self.assertAlmostEqual(q, q.norm() * q.normalize())
    self.assertAlmostEqual(q, q.normalize() * q.norm())
    self.assertAlmostEqual(q.normalize().norm(), 1)

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_normalize_close(self, quat):
    quat_normalized = quat.normalize()
    self.assertAlmostEqual(quat_normalized.norm(), 1.0)
    self.assertAlmostEqual(quat.norm() * quat_normalized, quat)

  @parameterized.named_parameters(*_TINY_QUATERNIONS)
  def test_normalize_errors(self, quat):
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.normalize
    )

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_check_non_zero(self, quat):
    quat.check_non_zero()

  @parameterized.named_parameters(*_TINY_QUATERNIONS)
  def test_check_non_zero_errors(self, quat):
    self.assertRaisesRegex(
        ValueError, quaternion.QUATERNION_ZERO_MESSAGE, quat.check_non_zero
    )

  @parameterized.named_parameters(*_UNIT_QUATERNIONS)
  def test_check_normalized(self, q_unit):
    logging.debug('q_unit=%s', q_unit)
    self.assertEqual(q_unit.norm(), 1.0)
    q_unit.check_normalized()

  @parameterized.named_parameters(*_NON_ZERO_QUATERNIONS)
  def test_check_normalized_close(self, quat):
    quat_normalized = quat.normalize()
    logging.debug('quat=%s, quat_normalized=%s', quat, quat_normalized)
    self.assertAlmostEqual(quat_normalized.norm(), 1.0)
    quat_normalized.check_normalized()
    (quat_normalized * (1 + _LESS_THAN_NORM_EPSILON)).check_normalized()
    (quat_normalized * (1 - _LESS_THAN_NORM_EPSILON)).check_normalized()
    # If the norm is off by more than twice the epsilon value, it should trigger
    # the exception.
    self.assertRaisesRegex(
        ValueError,
        quaternion.QUATERNION_NOT_NORMALIZED_MESSAGE,
        (
            quat_normalized * (1 + 2 * quaternion.QUATERNION_NORM_EPSILON)
        ).check_normalized,
    )
    self.assertRaisesRegex(
        ValueError,
        quaternion.QUATERNION_NOT_NORMALIZED_MESSAGE,
        (
            quat_normalized * (1 - 2 * quaternion.QUATERNION_NORM_EPSILON)
        ).check_normalized,
    )

  @parameterized.named_parameters(*_NON_UNIT_QUATERNIONS + _TINY_QUATERNIONS)
  def test_check_normalized_errors(self, q_non_unit):
    logging.debug('q_non_unit=%s', q_non_unit)
    self.assertRaisesRegex(
        ValueError,
        quaternion.QUATERNION_NOT_NORMALIZED_MESSAGE,
        q_non_unit.check_normalized,
    )

  def test_quaternion_str(self):
    """Test function for Quaternion.__str__ function.

    Verifies output of Quaternion.__str__.

    Tests:
      Quaternion.__str__
    """
    quat = quaternion.Quaternion([0.125, -0.25, 0.375, 0.48828125])
    expected_quat_string = '[0.125i + -0.25j + 0.375k + 0.4883]'
    logging.info('Quaternion.__str__ = %s', quat)
    self.assertEqual(str(quat), expected_quat_string)
    self.assertEqual(quat.__str__(), expected_quat_string)

  def test_quaternion_repr(self):
    """Test function for Quaternion.__repr__ function.

    Verifies output of Quaternion.__repr__.

    Tests:
      Quaternion.__repr__
    """
    quat = quaternion.Quaternion([0.125, -0.25, 0.375, 0.48828125])
    logging.info('Quaternion.__repr__ = %r', quat)
    self.assertEqual(
        quat.__repr__(), 'Quaternion([0.125, -0.25, 0.375, 0.48828125])'
    )

  def test_one(self):
    self.assertEqual(_QUAT_1, quaternion.Quaternion([0, 0, 0, 1]))
    self.assertEqual(_QUAT_1.real, 1.0)
    self.assert_all_equal(_QUAT_1.imag, 0.0)
    self.assertEqual(_QUAT_1, _QUAT_1.inverse())
    self.assertEqual(_QUAT_1, _QUAT_1.conjugate)

  def test_zero(self):
    self.assert_all_equal(_QUAT_0.xyzw, 0.0)
    self.assertEqual(_QUAT_0, _QUAT_0.conjugate)

  def test_random_unit(self):
    cumulative_quaternion = quaternion.Quaternion.one()
    for _ in range(100):
      random_quaternion = quaternion.Quaternion.random_unit()
      self.assertAlmostEqual(random_quaternion.norm(), 1.0)
      cumulative_quaternion *= random_quaternion
    self.assertAlmostEqual(cumulative_quaternion.norm(), 1.0)

  def test_random_seeded(self):
    rng_a = vector_util.default_rng(seed=1)
    rng_a2 = vector_util.default_rng(seed=1)
    rng_b = vector_util.default_rng(seed=2)
    rng_c = vector_util.default_rng()
    for _ in range(10):
      qa = quaternion.Quaternion.random_unit(rng=rng_a)
      self.assertEqual(qa, quaternion.Quaternion.random_unit(rng=rng_a2))
      self.assertNotEqual(qa, quaternion.Quaternion.random_unit(rng=rng_b))
      self.assertNotEqual(qa, quaternion.Quaternion.random_unit(rng=rng_c))
      self.assertNotEqual(qa, quaternion.Quaternion.random_unit())

  @parameterized.parameters(0, 1, -1, _LESS_THAN_NORM_EPSILON, 1e6)
  def test_from_real(self, w):
    """Tests Quaternion.from_real factory function."""
    q = quaternion.Quaternion.from_real(w)
    self.assertEqual(q.x, 0)
    self.assertEqual(q.y, 0)
    self.assertEqual(q.z, 0)
    self.assertEqual(q.w, w)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_from_imaginary(self, quat):
    """Tests Quaternion.from_imaginary factory function."""
    q = quaternion.Quaternion.from_imaginary(quat.imag)
    self.assert_all_equal(q.imag, quat.imag)
    self.assertEqual(q.w, 0)

  @parameterized.named_parameters(*_TEST_QUATERNIONS)
  def test_from_real_imaginary(self, quat):
    """Tests Quaternion.from_imaginary factory function."""
    q = quaternion.Quaternion.from_real_imaginary(
        real=quat.real, imaginary=quat.imag
    )
    self.assert_all_equal(q.imag, quat.imag)
    self.assertEqual(q.real, quat.real)
    self.assertEqual(q, quat)

  @parameterized.parameters(
      (_QUAT_0, _quaternion_proto('')),
      (_QUAT_1, _quaternion_proto('w: 1')),
      (_QUAT_I, _quaternion_proto('x: 1')),
      (_QUAT_J, _quaternion_proto('y: 1')),
      (_QUAT_K, _quaternion_proto('z: 1')),
      (_QUAT_HALF, _quaternion_proto('x: 0.5 y: 0.5 z: 0.5 w: 0.5')),
      (
          quaternion.Quaternion([-0.1, 0.7, -0.5, 0.5]),
          _quaternion_proto('x: -0.1 y: 0.7 z: -0.5 w: 0.5'),
      ),
  )
  def test_to_and_from_proto(self, quat, quat_proto):
    self.assertEqual(quat, quaternion.Quaternion.from_proto(quat_proto))
    self.assertEqual(quat, quaternion.Quaternion.from_proto(quat.to_proto()))
    proto_out = quaternion_pb2.Quaterniond()
    quat.to_proto(proto_out)
    self.assertEqual(quat, quaternion.Quaternion.from_proto(proto_out))
    self.assertEqual(id(proto_out), id(quat.to_proto(proto_out)))
    self.assertNotEqual(id(proto_out), id(quat.to_proto()))


if __name__ == '__main__':
  absltest.main()
