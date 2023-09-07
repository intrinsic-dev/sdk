# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.robotics.pymath.vector_util module (python3)."""

import math

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.robotics.pymath import math_test
from intrinsic.robotics.pymath import vector_util
import numpy as np

# Minimum values for expected value and standard deviation of the binomial
# distribution to give confidence that the normal approximation is adequate.
_MIN_BINOMIAL_MU = 20
_MIN_BINOMIAL_SIGMA = 3

# Maximum test failure chance the tolerable chance for an individual test to
# succeed.  It is selected to keep overall failure chance close to 1e-9.
_MAX_TEST_FAILURE_CHANCE = 1e-12

# Maximum z-value expected from tests is calculated from a tolerance for test
# failure probability.
_MAX_ABS_Z_VALUE = 7  # -stats.norm.ppf(_MAX_TEST_FAILURE_CHANCE / 2)

RANDOM_UNIT_N = {
    2: vector_util.random_unit_2,
    3: vector_util.random_unit_3,
    4: vector_util.random_unit_4,
}


def _min_max_abs_z(num_tests):
  """Returns the required minimum absolute value of z for the number of tests.

  If num_tests tests are run, we expect the result of at least one of them to
  lie outside a neighborhood around z=zero.  This function determines the width
  of that neighborhood which gives a cumulative probability of failure no
  greater than _MAX_TEST_FAILURE_CHANCE.

  Args:
    num_tests: Number of independent tests.

  Returns:
    Expected minimum of maximum absolute z values for tests.
  """
  z = 1e-13
  if num_tests >= 1000:
    z = 1
  elif num_tests >= 100:
    z = 0.5
  elif num_tests >= 10:
    z = 0.02
  elif num_tests >= 5:
    z = 0.002

  # Actual calculation was from Gaussian distribution.  It has been replaced by
  # a handful of precalculated values to remove a dependency on scipy.stats.
  #
  # max_individual_fail_chance = math.pow(_MAX_TEST_FAILURE_CHANCE,
  #                                       1.0 / num_tests)
  # z = -stats.norm.ppf((1 - max_individual_fail_chance) / 2)

  # Adjust z downwards because the actual distribution is not always Gaussian.
  z = min(z / 2, 1)
  logging.debug('num_tests= %d, z= %g', num_tests, z)
  return z


def _cone_area_ratio_2(cone_angle):
  """Returns the fraction of a circle contained in an arc.

  The arc is a 2D "cone" segment of a circle described by a half-angle.

  Args:
    cone_angle: The angle between the arc center and one endpoint.

  Returns:
    The fraction of the circle's circumference that is contained in the arc
    described by a 2D cone, a value in [0, 1].
  """
  return cone_angle / math.pi


def _cone_area_ratio_3(cone_angle):
  """Returns the fraction of a sphere contained in a 3D cone.

  Args:
    cone_angle: The angle between the center axis and the side of the cone.

  Returns:
    The fraction of the sphere's surface that is contained by the 3D cone, a
    value in [0, 1].
  """
  return (1.0 - math.cos(cone_angle)) * 0.5


def _cone_area_ratio_4(cone_angle):
  """Returns the fraction of a hypersphere contained in a 4D cone.

  Args:
    cone_angle: The angle between the center axis and the side of the 4D cone.

  Returns:
    The fraction of the hypersphere's surface that is contained by the 4D cone,
    a value in [0, 1].
  """
  return (cone_angle - math.cos(cone_angle) * math.sin(cone_angle)) / math.pi


class VectorUtilTest(math_test.TestCase, parameterized.TestCase):

  def test_one_hot_vector(self):
    self.assert_all_equal(vector_util.one_hot_vector(1, 0), [1])
    self.assert_all_equal(vector_util.one_hot_vector(2, 1), [0, 1])
    self.assert_all_equal(vector_util.one_hot_vector(3, 1), [0, 1, 0])
    self.assert_all_equal(vector_util.one_hot_vector(3, -1), [0, 0, 1])

  def test_one_hot_vector_invalid(self):
    self.assertRaisesRegex(
        ValueError,
        'negative dimensions are not allowed',
        vector_util.one_hot_vector,
        -1,
        0,
    )
    self.assertRaisesRegex(
        IndexError,
        'index .* is out of bounds for axis',
        vector_util.one_hot_vector,
        2,
        2,
    )
    self.assertRaisesRegex(
        IndexError,
        'index .* is out of bounds for axis',
        vector_util.one_hot_vector,
        2,
        -3,
    )

  @parameterized.parameters(
      ((0, 0, 1), 3),
      ([1, 0, 0], 3),
      (np.zeros(3), 3),
      (np.ones(3), 3),
      ((0, 0, 1, 0), 4),
      ([0, 1, 0, 0], 4),
      (np.zeros(4), 4),
      (np.ones(4), 4),
      ([0, 1], 2),
      (np.zeros(2), 2),
      (np.ones(2), 2),
      ([0, 0, 1, 0, 0], 5),
      (np.zeros(5), 5),
      (np.ones(5), 5),
  )
  def test_as_finite_vector(self, values, dimension):
    self.assert_all_equal(vector_util.as_finite_vector(values=values), values)
    self.assert_all_equal(
        vector_util.as_finite_vector(values=values, dimension=dimension), values
    )
    self.assert_all_equal(
        vector_util.as_finite_vector(
            values=values, dimension=dimension, dtype=np.float64
        ),
        values,
    )
    for dtype in (np.float64, np.int32, np.float32):
      vector_dtype = vector_util.as_finite_vector(values=values, dtype=dtype)
      self.assert_all_equal(vector_dtype, values)
      self.assertEqual(vector_dtype.dtype, dtype)
      self.assert_all_equal(
          vector_util.as_finite_vector(
              values=values, dimension=dimension, dtype=dtype
          ),
          values,
      )

  @parameterized.parameters(
      ((-1, 0, 1), 3),
      ([1, 0, 0], 3),
      (np.ones(3), 3),
      ((0, 0, 1, 0), 4),
      ([0, 1, -1, 1], 4),
      (np.ones(4), 4),
      ([0, 1], 2),
      (np.ones(2), 2),
      ([-2, 0, 1, 0, 3], 5),
      (np.ones(5), 5),
  )
  def test_as_finite_vector_normalize(self, values, dimension):
    vector = vector_util.as_finite_vector(values=values)
    vector_normalized = vector_util.as_finite_vector(
        values=values, normalize=True
    )
    self.assert_all_close(vector, vector_normalized * np.linalg.norm(vector))

  def test_as_finite_vector_errors(self):
    self.assertEmpty(vector_util.as_finite_vector([], 0))
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_finite_vector,
        [],
        -1,
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_finite_vector,
        [0, 0],
        3,
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_finite_vector,
        [0, 0, 0, 0],
        3,
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_VALUES_MESSAGE,
        vector_util.as_finite_vector,
        [np.nan, 0, 0],
        3,
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_INFINITE_VALUES_MESSAGE,
        vector_util.as_finite_vector,
        [0, 0, np.inf],
        3,
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_ZERO_MESSAGE,
        vector_util.as_finite_vector,
        [0, 0, 0],
        3,
        True,
    )

  def test_as_vector2(self):
    dimension = 2
    v = np.ones(dimension)
    v0 = np.zeros(dimension)
    self.assert_all_equal(vector_util.as_vector2(v), v)
    self.assert_all_equal(vector_util.as_vector2(v0), v0)
    self.assert_all_equal(vector_util.as_vector2([1, 1]), v)
    self.assert_all_equal(vector_util.as_vector2((1, 1)), v)
    self.assert_all_equal(vector_util.as_vector2([0, 0]), v0)
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector2,
        [0],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector2,
        [0, 1, 2],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_VALUES_MESSAGE,
        vector_util.as_vector2,
        [np.nan, 0],
    )
    self.assertRaisesRegex(
        ValueError,
        'could not convert string to float:',
        vector_util.as_vector2,
        [0, 'hello'],
    )
    # as_unit_vector
    self.assert_all_equal(
        vector_util.as_unit_vector2(v), vector_util.normalize_vector(v)
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_ZERO_MESSAGE,
        vector_util.as_unit_vector2,
        v0,
    )

  def test_as_vector3(self):
    dimension = 3
    v = np.ones(dimension)
    v0 = np.zeros(dimension)
    self.assert_all_equal(vector_util.as_vector3(v), v)
    self.assert_all_equal(vector_util.as_vector3(v0), v0)
    self.assert_all_equal(vector_util.as_vector3([1, 1, 1]), v)
    self.assert_all_equal(vector_util.as_vector3((1, 1, 1)), v)
    self.assert_all_equal(vector_util.as_vector3([0, 0, 0]), v0)
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector3,
        [0, 0],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector3,
        [0, 0, 1, 2],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_VALUES_MESSAGE,
        vector_util.as_vector3,
        [np.nan, 0, 0],
    )
    self.assertRaisesRegex(
        ValueError,
        'could not convert string to float:',
        vector_util.as_vector3,
        [0, 'hello', 0],
    )
    # as_unit_vector
    self.assert_all_equal(
        vector_util.as_unit_vector3(v), vector_util.normalize_vector(v)
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_ZERO_MESSAGE,
        vector_util.as_unit_vector3,
        v0,
    )

  def test_as_vector4(self):
    dimension = 4
    v = np.ones(dimension)
    v0 = np.zeros(dimension)
    self.assert_all_equal(vector_util.as_vector4(v), v)
    self.assert_all_equal(vector_util.as_vector4(v0), v0)
    self.assert_all_equal(vector_util.as_vector4([1, 1, 1, 1]), v)
    self.assert_all_equal(vector_util.as_vector4((1, 1, 1, 1)), v)
    self.assert_all_equal(vector_util.as_vector4([0, 0, 0, 0]), v0)
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector4,
        [0, 0, 0],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        vector_util.as_vector4,
        [0, 0, 1, 2, 3],
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_VALUES_MESSAGE,
        vector_util.as_vector4,
        [np.nan, 0, 0, 0],
    )
    self.assertRaisesRegex(
        ValueError,
        'could not convert string to float:',
        vector_util.as_vector4,
        [0, 'hello', 0, 0],
    )
    # as_unit_vector
    self.assert_all_equal(
        vector_util.as_unit_vector4(v), vector_util.normalize_vector(v)
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_ZERO_MESSAGE,
        vector_util.as_unit_vector4,
        v0,
    )

  @parameterized.parameters(
      (2, 1e-2),
      (2, 1e-6),
      (3, 1e-3),
      (4, 1e-5),
      (5, 1e-4),
      (6, 1e-2),
      (7, 1e-3),
  )
  def test_is_vector_normalized(self, dimension, norm_epsilon):
    """Tests is_vector_normalized function.

    Verifies that only the vectors whose magnitude lie in:
      |vector| in (1 - norm_epsilon, 1 + norm_epsilon)
    are considered normalized by this function.

    If norm_epsilon is zero, only vectors that have magnitude precisely 1.0 will
    be considered normalized.

    Args:
      dimension: Number of components in the vector space.
      norm_epsilon: Error tolerance for magnitude of vector.
    """
    self.assertFalse(
        vector_util.is_vector_normalized(np.ones(dimension), norm_epsilon)
    )
    self.assertFalse(
        vector_util.is_vector_normalized(np.zeros(dimension), norm_epsilon)
    )
    for unit_vector in math_test.make_test_vectors(
        dimension, normalize=True, number_of_random_vectors=4
    ):
      self.assertAlmostEqual(np.linalg.norm(unit_vector), 1.0)
      self.assertTrue(
          vector_util.is_vector_normalized(unit_vector, norm_epsilon)
      )
      # Scaling by a factor in (1 - norm_epsilon, 1 + norm_epsilon)
      # or adding a delta vector with magnitude less than norm_epsilon
      # should result in a vector that is still considered "normalized".
      self.assertTrue(
          vector_util.is_vector_normalized(
              unit_vector * (1.0 + norm_epsilon * 0.9), norm_epsilon
          )
      )
      self.assertTrue(
          vector_util.is_vector_normalized(
              unit_vector * (1.0 - norm_epsilon * 0.9), norm_epsilon
          )
      )
      small_error_vector = (
          vector_util.one_hot_vector(dimension, 0) * norm_epsilon * 0.75
      )
      self.assertTrue(
          vector_util.is_vector_normalized(
              unit_vector + small_error_vector, norm_epsilon
          )
      )
      # Scaling by a factor outside of [1 - norm_epsilon, 1 + norm_epsilon]
      # should result in an a vector that is not considered "normalized"
      # within norm_epsilon.
      self.assertFalse(
          vector_util.is_vector_normalized(
              unit_vector * (1.0 + norm_epsilon * 1.1), norm_epsilon
          )
      )
      self.assertFalse(
          vector_util.is_vector_normalized(
              unit_vector * (1.0 - norm_epsilon * 1.1), norm_epsilon
          )
      )

  def _assert_valid_z_values(self, values, mu, sigma):
    """Asserts that the input values are plausibly generated by a Gaussian.

    Checks that the z-values are all less than a maximum value (around 6 sigmas
    from the mean) and that at least one exceeds a minimum value which depends
    on the number of tests in the set.

    Args:
      values: Values from the distribution.
      mu: Mean of the distribution.
      sigma: Standard deviation of the distribution.
    """
    min_max_abs_z = _min_max_abs_z(len(values))
    logging.debug(
        'values: shape=%s range=[%f %f], mu=%g sigma=%g',
        values.shape,
        np.min(values),
        np.max(values),
        mu,
        sigma,
    )

    # Calculate z-values from expected mean and standard deviation.
    z_values = (values - mu) / sigma
    logging.debug(
        'z_values: shape=%s z-range=[%f %f]',
        z_values.shape,
        np.min(z_values),
        np.max(z_values),
    )

    # All results should be within |z| <= 6 and at least one should be
    # measurably greater than zero: max|z| >= min_max_abs_z
    self.assert_all_less_equal(np.abs(z_values), _MAX_ABS_Z_VALUE)
    self.assertGreaterEqual(np.max(np.fabs(z_values)), min_max_abs_z)

  @parameterized.parameters(
      (2, math.pi / 2),
      (2, math.pi / 6),
      (2, 0.01),
      (3, math.pi / 2),
      (3, math.pi / 6),
      (3, 0.1),
      (4, math.pi / 2),
      (4, math.pi / 6),
      (4, 0.25),
  )
  def test_random_unit_uniform_distribution(self, dimension, cone_angle):
    """Test function for random_unit_2, random_unit_3, and random_unit_4.

    Tests that the vectors generated by the random_unit_<n> functions are
    uniformly distributed over the unit ball (circle, sphere, or hypersphere).

    The test chooses a set of cone centers.  If the points are uniformly
    distributed over the ball, the fraction of points lying in each cone should
    be equal to the fraction of the ball area that lies inside the cone.

    Tests:
      random_unit_2
      random_unit_3
      random_unit_4

    Args:
      dimension: Number of components in each vector.
      cone_angle: Cone angle to test for distribution over the ball.
    """

    # ------------------------------------------------------------------------
    # random_unit_fn: The function under test.  Generates a uniform random
    #   vector from the unit ball.
    # cone_area_ratio_fn: Utility function that calculates the fraction of the
    #   surface of a ball that lies within a cone.
    #
    # random_unit_fn and cone_area_ratio_fn are defined separately for 2, 3,
    # and 4 dimensions, because the math is entirely different for each.
    test_functions_by_dimension = {
        2: _cone_area_ratio_2,
        3: _cone_area_ratio_3,
        4: _cone_area_ratio_4,
    }
    random_unit_fn = RANDOM_UNIT_N[dimension]
    cone_area_ratio_fn = test_functions_by_dimension[dimension]

    cone_centers = math_test.make_test_vectors(
        dimension=dimension,
        values=[0, 1, -1, 0.5, -0.5],
        normalize=True,
        number_of_random_vectors=20,
    )
    num_cones = cone_centers.shape[0]
    num_trials = 10000  # Number of random samples to test against cones.
    # The expected ratio is the fraction of the ball that lies within each cone.
    expected_ratio = cone_area_ratio_fn(cone_angle)
    cone_cos_angle = math.cos(cone_angle)
    counts = np.zeros((num_cones, 1), dtype=np.float64)
    for _ in range(num_trials):
      random_unit_vector = random_unit_fn()
      self.assertLen(random_unit_vector, dimension)
      self.assertAlmostEqual(np.linalg.norm(random_unit_vector), 1.0)
      # Calculate all cone containment tests in parallel.
      cone_center_dot_products = np.dot(
          cone_centers, random_unit_vector[:, None]
      )
      matches = cone_center_dot_products > cone_cos_angle
      counts += matches
    # Calculate mean and sigma for a binomial distribution.
    expected_value = expected_ratio * num_trials
    sigma = math.sqrt(expected_ratio * (1 - expected_ratio) * num_trials)
    # Check that expected_value and sigma are in a range where the normal
    # approximation to the binomial will be reasonable.
    self.assertGreater(expected_value, _MIN_BINOMIAL_MU)
    self.assertGreater(sigma, _MIN_BINOMIAL_SIGMA)
    logging.debug('cone_angle=%g cos=%g', cone_angle, cone_cos_angle)
    self._assert_valid_z_values(counts, expected_value, sigma)

  @parameterized.parameters((2, 10), (3, 1001), (4, 2))
  def test_random_unit_seeded(self, dimension, seed):
    """Test that seeded rngs work correctly."""
    random_unit_fn = RANDOM_UNIT_N[dimension]
    rng_a = vector_util.default_rng(seed=seed)
    rng_a2 = vector_util.default_rng(seed=seed)
    rng_b = vector_util.default_rng(seed=seed + 1)
    rng_b2 = vector_util.default_rng(seed=seed + 1)
    rng_c = vector_util.default_rng()
    rng_d = vector_util.default_rng()
    for _ in range(10):
      va = random_unit_fn(rng=rng_a)
      vb = random_unit_fn(rng=rng_b)
      self.assert_all_equal(va, random_unit_fn(rng=rng_a2))
      self.assert_all_equal(vb, random_unit_fn(rng=rng_b2))
      v = [
          va,
          vb,
          random_unit_fn(rng=rng_c),
          random_unit_fn(rng=rng_d),
          random_unit_fn(),
      ]
      for i in range(len(v)):
        for j in range(i):
          self.assertFalse(np.any(v[i] == v[j]))

  def test_gaussian_limits(self):
    """Verify that the _min_max_abs_z function does the right thing."""
    for n in [1, 10, 100, 1000, 10000]:
      min_abs_z = _min_max_abs_z(n)
      values = np.random.normal(size=(n))
      max_abs = np.max(np.fabs(values))
      self.assertLess(0, min_abs_z)
      self.assertLess(min_abs_z, max_abs)
      self.assertLess(max_abs, _MAX_ABS_Z_VALUE)


if __name__ == '__main__':
  absltest.main()
