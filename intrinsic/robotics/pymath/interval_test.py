# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.robotics.pymath.interval."""

from absl import logging
from absl.testing import absltest
from intrinsic.robotics.pymath import interval
from intrinsic.robotics.pymath import math_test
import numpy as np

I_ZERO = interval.Interval.zero()
I_UNIT = interval.Interval.unit()
I_ALL = interval.Interval.infinity()
I_NEGATIVE = interval.Interval((-np.inf, 0))
I_POSITIVE = interval.Interval((0, np.inf))
I_EMPTY = interval.Interval.create_empty()


class IntervalTest(math_test.TestCase):

  def test_bounds(self):
    test_interval = interval.Interval((2, 5))
    self.assert_all_equal(test_interval.bounds, [2, 5])

  def test_minimum(self):
    ival = interval.Interval((-2, 3))
    self.assertEqual(ival.minimum, -2)
    ival.minimum = 0
    self.assertEqual(ival.minimum, 0)
    self.assertEqual(ival.maximum, 3)

  def test_maximum(self):
    ival = interval.Interval((-2, 3))
    self.assertEqual(ival.maximum, 3)
    ival.maximum = 0
    self.assertEqual(ival.minimum, -2)
    self.assertEqual(ival.maximum, 0)

  def test_empty(self):
    self.assert_empty(I_EMPTY)
    self.assert_not_empty(I_ZERO)
    self.assert_not_empty(I_UNIT)
    self.assert_not_empty(I_ALL)

  def test_bounded(self):
    self.assertTrue(I_EMPTY.bounded)
    self.assertTrue(I_UNIT.bounded)
    self.assertTrue(I_ZERO.bounded)
    self.assertFalse(I_ALL.bounded)
    self.assertFalse(I_POSITIVE.bounded)
    self.assertFalse(I_NEGATIVE.bounded)

  def test_bounded_below(self):
    self.assertTrue(I_EMPTY.bounded_below)
    self.assertTrue(I_UNIT.bounded_below)
    self.assertTrue(I_ZERO.bounded_below)
    self.assertFalse(I_ALL.bounded_below)
    self.assertTrue(I_POSITIVE.bounded_below)
    self.assertFalse(I_NEGATIVE.bounded_below)

  def test_bounded_above(self):
    self.assertTrue(I_EMPTY.bounded_above)
    self.assertTrue(I_UNIT.bounded_above)
    self.assertTrue(I_ZERO.bounded_above)
    self.assertFalse(I_ALL.bounded_above)
    self.assertFalse(I_POSITIVE.bounded_above)
    self.assertTrue(I_NEGATIVE.bounded_above)

  def test_unbounded(self):
    self.assertFalse(I_EMPTY.unbounded)
    self.assertFalse(I_UNIT.unbounded)
    self.assertFalse(I_ZERO.unbounded)
    self.assertTrue(I_ALL.unbounded)
    self.assertTrue(I_POSITIVE.unbounded)
    self.assertTrue(I_NEGATIVE.unbounded)

  def test_length(self):
    self.assertEqual(I_EMPTY.length, 0)
    self.assertEqual(I_UNIT.length, 1)
    self.assertEqual(I_ZERO.length, 0)
    self.assertEqual(I_ALL.length, np.inf)
    self.assertEqual(I_POSITIVE.length, np.inf)
    self.assertEqual(I_NEGATIVE.length, np.inf)
    self.assertEqual(interval.Interval((1, 4)).length, 3)

  def test_center(self):
    self.assertEqual(I_EMPTY.center, 0)
    self.assertEqual(I_UNIT.center, 0.5)
    self.assertEqual(I_ZERO.center, 0)
    self.assertEqual(I_ALL.center, 0)
    self.assertEqual(I_POSITIVE.center, np.inf)
    self.assertEqual(I_NEGATIVE.center, -np.inf)
    self.assertEqual(interval.Interval((1, 4)).center, 2.5)

  def test_eq(self):
    self.assertEqual(I_ZERO, I_ZERO)
    self.assertEqual(I_UNIT, I_UNIT)
    self.assertEqual(I_ALL, I_ALL)
    self.assertEqual(I_POSITIVE, I_POSITIVE)
    self.assertEqual(I_NEGATIVE, I_NEGATIVE)
    self.assertNotEqual(I_ZERO, I_UNIT)
    self.assertNotEqual(I_ALL, I_POSITIVE)
    self.assertNotEqual(I_ZERO, I_NEGATIVE)

  def test_eq_empty(self):
    self.assertEqual(I_EMPTY, I_EMPTY)
    self.assertEqual(I_EMPTY, interval.Interval((2, -2)))
    self.assertEqual(I_EMPTY, interval.Interval((np.inf, 0)))
    self.assertEqual(I_EMPTY, interval.Interval((-1, -np.inf)))

  def test_add(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival + 2, interval.Interval((3, 7)))
    self.assertEqual(2 + ival, ival + 2)
    self.assertEqual(ival + 0, ival)
    self.assertEqual(0 + ival, ival)

  def test_add_empty(self):
    self.assert_empty(I_EMPTY + 1)

  def test_sub(self):
    ival = interval.Interval((0, 2))
    self.assertEqual(ival - 2, interval.Interval((-2, 0)))
    self.assertEqual(ival - 2, ival + (-2))

  def test_sub_empty(self):
    self.assert_empty(I_EMPTY - 1)

  def test_mul(self):
    ival = interval.Interval((-1, 4))
    self.assert_all_equal((ival * 2).bounds, ival.bounds * 2)
    self.assertEqual(ival * 2, 2 * ival)
    self.assertEqual(ival * 0, I_ZERO)

  def test_mul_negative(self):
    ival = interval.Interval((1, 3))
    self.assertEqual((ival * (-1)).minimum, -ival.maximum)
    self.assertEqual((ival * (-2)).maximum, -2 * ival.minimum)

  def test_mul_empty(self):
    ival = I_EMPTY
    self.assert_empty(ival * 2)
    self.assert_empty(2 * ival)
    self.assert_empty(ival * 0)

  def test_div(self):
    ival = interval.Interval((1, 3))
    self.assert_all_equal((ival / 2).bounds, ival.bounds / 2)
    self.assertEqual(ival / 2, ival * 0.5)

  def test_div_negative(self):
    ival = interval.Interval((-1, 2))
    self.assertEqual((ival / (-1)).minimum, -ival.maximum)
    self.assertEqual((ival / (-2)).maximum, -0.5 * ival.minimum)

  def test_div_empty(self):
    ival = I_EMPTY
    self.assertEqual(ival, ival / 2)

  def test_str(self):
    ival = interval.Interval((2, 5))
    logging.info(ival)
    self.assertEqual('%s' % ival, '[2.0, 5.0]')
    self.assertEqual('%s' % I_EMPTY, '[EMPTY]')

  def test_repr(self):
    ival = interval.Interval((2, 5))
    logging.info(ival)
    self.assertEqual('%r' % ival, '[2.0, 5.0]')
    self.assertEqual('%r' % I_EMPTY, '[inf, -inf]')

  def test_contains(self):
    ival = interval.Interval((-2, 5))
    self.assert_contains(ival, -2)
    self.assert_contains(ival, 5)
    self.assert_contains(ival, 0)
    self.assert_not_contains(ival, -3)
    self.assert_not_contains(ival, 8)
    self.assert_not_contains(ival, -np.inf)
    self.assert_not_contains(ival, np.inf)

  def test_contains_interval(self):
    ival = interval.Interval((0, 4))
    self.assert_contains(ival, ival)
    self.assert_contains(ival, interval.Interval((0, 0)))
    self.assert_contains(ival, interval.Interval((4, 4)))
    self.assert_contains(ival, interval.Interval((1, 3)))
    self.assert_not_contains(ival, interval.Interval((-1, 5)))
    self.assert_not_contains(ival, ival + 1)

  def test_intersection(self):
    ival = interval.Interval((1, 6))
    ival_min = interval.Interval((1, 1))
    ival_max = interval.Interval((6, 6))
    self.assertEqual(ival.intersection(ival), ival)
    self.assertEqual(ival.intersection(ival_min), ival_min)
    self.assertEqual(ival_max.intersection(ival), ival_max)
    self.assert_intersects(ival, ival + 1)
    self.assert_not_intersects(ival, ival + 10)
    self.assert_contains(ival, ival.intersection(ival + 1))
    self.assert_contains(ival + 1, ival.intersection(ival + 1))
    self.assert_empty(ival.intersection(ival + 10))

  def test_intersection_empty(self):
    ival = interval.Interval((2, 4))
    self.assertEqual(ival.intersection(I_EMPTY), I_EMPTY)
    self.assertEqual(I_EMPTY.intersection(ival), I_EMPTY)
    self.assert_not_intersects(ival, I_EMPTY)
    self.assert_not_intersects(I_EMPTY, ival)

  def test_union_self(self):
    ival = interval.Interval((-4, -2))
    ival_min = interval.Interval((-4, -4))
    ival_max = interval.Interval((-2, -2))
    self.assertEqual(ival.union(ival), ival)
    self.assertEqual(ival.union(ival_min), ival)
    self.assertEqual(ival_max.union(ival), ival)

  def test_union(self):
    ival = interval.Interval((5, 10))
    self.assert_contains(ival.union(ival + 1), ival)
    self.assert_contains(ival.union(ival + 10), ival)
    self.assert_contains(ival.union(ival - 1), ival)
    self.assert_contains(ival.union(ival - 10), ival)
    self.assert_not_contains(ival, ival.union(ival + 1))

  def test_union_empty(self):
    ival = interval.Interval((2, 3))
    self.assertEqual(ival.union(I_EMPTY), ival)
    self.assertEqual(I_EMPTY.union(ival), ival)

  def test_insert(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival.insert(1), ival)
    self.assertEqual(ival.insert(5), ival)
    self.assertEqual(
        ival.insert(9), ival.union(interval.Interval.from_value(9))
    )

  def test_insert_empty(self):
    ival = interval.Interval((1, 2))
    self.assertEqual(I_EMPTY.insert(1).insert(2), ival)
    self.assertEqual(I_EMPTY.insert(2).insert(1), ival)

  def test_mirror(self):
    ival = interval.Interval((1, 4))
    self.assertEqual(ival.mirror(), interval.Interval((-4, -1)))
    self.assertEqual(ival.mirror().mirror(), ival)

  def test_clamp(self):
    ival = interval.Interval((2, 6))
    ival_min = interval.Interval((2, 2))
    ival_max = interval.Interval((6, 6))
    self.assertEqual(ival.clamp(ival_min), ival_min)
    self.assertEqual(ival_min.clamp(ival), ival_min)
    self.assertEqual(ival.clamp(ival + 1), ival.intersection(ival + 1))
    self.assertEqual(ival.clamp(ival + 10), ival_max)
    self.assertEqual(ival.clamp(ival - 10), ival_min)

  def test_clamp_empty(self):
    ival = interval.Interval((2, 3))
    self.assertEqual(I_EMPTY.clamp(I_EMPTY), I_EMPTY)
    self.assertEqual(ival.clamp(I_EMPTY), I_EMPTY)
    self.assertEqual(I_EMPTY.clamp(ival), I_EMPTY)
    self.assertEqual(I_EMPTY.clamp(3), 3)

  def test_distance_value(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival.distance(0), 1)
    self.assertEqual(ival.distance(1), 0)
    self.assertEqual(ival.distance(2), -1)
    self.assertEqual(ival.distance(3), -2)
    self.assertEqual(ival.distance(4), -1)
    self.assertEqual(ival.distance(5), 0)
    self.assertEqual(ival.distance(6), 1)
    self.assertEqual(ival.distance(np.inf), np.inf)
    self.assertEqual(ival.distance(-np.inf), np.inf)

  def test_distance_interval(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival.distance(interval.Interval((1, 1))), 0)
    self.assertEqual(ival.distance(interval.Interval((0, 2))), 0)
    self.assertEqual(ival.distance(interval.Interval((5, 5))), 0)
    self.assertEqual(ival.distance(interval.Interval((4, 6))), 0)
    # Strictly contained interval has negative distance.
    self.assertEqual(ival.distance(interval.Interval((2, 3))), -1)
    self.assertEqual(ival.distance(interval.Interval((2, 2))), -1)
    self.assertEqual(ival.distance(interval.Interval((3, 3))), -2)
    # Disjoint interval has positive distance.
    self.assertEqual(ival.distance(interval.Interval((7, 12))), 2)
    self.assertEqual(ival.distance(interval.Interval((-10, -8))), 9)

  def test_distance_empty(self):
    self.assertEqual(I_EMPTY.distance(0), np.inf)
    self.assertEqual(I_EMPTY.distance(100), np.inf)
    self.assertEqual(I_EMPTY.distance(interval.Interval((1, 5))), np.inf)
    self.assertEqual(interval.Interval((1, 5)).distance(I_EMPTY), np.inf)

  def test_closest_value(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival.closest_value(1), 1)
    self.assertEqual(ival.closest_value(5), 5)
    self.assertEqual(ival.closest_value(0), 1)
    self.assertEqual(ival.closest_value(-np.inf), 1)
    self.assertEqual(ival.closest_value(6), 5)
    self.assertEqual(ival.closest_value(np.inf), 5)
    self.assertEqual(ival.closest_value(3), 3)

  def test_closest_value_empty(self):
    self.assertEqual(I_EMPTY.closest_value(1), 1)

  def test_interpolate(self):
    ival = interval.Interval((1, 5))
    self.assertEqual(ival.interpolate(0), 1)
    self.assertEqual(ival.interpolate(0.25), 2)
    self.assertEqual(ival.interpolate(0.5), 3)
    self.assertEqual(ival.interpolate(0.75), 4)
    self.assertEqual(ival.interpolate(1), 5)
    self.assertEqual(ival.interpolate(-1), -3)
    self.assertEqual(ival.interpolate(2), 9)

  def test_interpolate_infinite(self):
    self.assertEqual(I_ALL.interpolate(0), -np.inf)
    self.assertEqual(I_ALL.interpolate(0.25), -np.inf)
    self.assertEqual(I_ALL.interpolate(0.5), 0)
    self.assertEqual(I_ALL.interpolate(0.75), np.inf)
    self.assertEqual(I_ALL.interpolate(1), np.inf)
    self.assertEqual(I_ALL.interpolate(-1), -np.inf)
    self.assertEqual(I_ALL.interpolate(2), np.inf)

    self.assertEqual(I_POSITIVE.interpolate(0), 0)
    self.assertEqual(I_POSITIVE.interpolate(0.25), np.inf)
    self.assertEqual(I_POSITIVE.interpolate(0.5), np.inf)
    self.assertEqual(I_POSITIVE.interpolate(0.75), np.inf)
    self.assertEqual(I_POSITIVE.interpolate(1), np.inf)
    self.assertEqual(I_POSITIVE.interpolate(-1), -np.inf)
    self.assertEqual(I_POSITIVE.interpolate(2), np.inf)

    self.assertEqual(I_NEGATIVE.interpolate(0), -np.inf)
    self.assertEqual(I_NEGATIVE.interpolate(0.25), -np.inf)
    self.assertEqual(I_NEGATIVE.interpolate(0.5), -np.inf)
    self.assertEqual(I_NEGATIVE.interpolate(0.75), -np.inf)
    self.assertEqual(I_NEGATIVE.interpolate(1), 0)
    self.assertEqual(I_NEGATIVE.interpolate(-1), -np.inf)
    self.assertEqual(I_NEGATIVE.interpolate(2), np.inf)

  def test_scale_length(self):
    ival = interval.Interval((1, 5))
    ival3 = ival.scale_length(3)
    self.assertEqual(ival3, interval.Interval((-3, 9)))
    self.assertEqual(ival3.center, ival.center)
    self.assertEqual(ival3.length, ival.length * 3)
    self.assertEqual(ival.scale_length(2).scale_length(0.5), ival)
    self.assert_interval_close(ival, ival3.scale_length(1.0 / 3.0))

  def test_scale_length_empty(self):
    self.assert_empty(I_EMPTY.scale_length(2))
    self.assert_empty(I_EMPTY.scale_length(0))

  def test_scale_length_invalid(self):
    self.assertRaisesRegex(
        ValueError,
        interval.NEGATIVE_SCALE_FACTOR_MESSAGE,
        I_UNIT.scale_length,
        -2,
    )

  def test_inflate(self):
    ival = interval.Interval((10, 20))
    self.assertEqual(ival.inflate(1), interval.Interval((9, 21)))
    self.assertEqual(ival.inflate(2).inflate(-2), ival)
    self.assert_empty(ival.inflate(-12))

  def test_inflate_empty(self):
    self.assert_empty(I_EMPTY.inflate(2))
    self.assert_empty(I_EMPTY.inflate(-2))

  def test_proto(self):
    ival = interval.Interval((1, 3))
    p = ival.to_proto()
    self.assertEqual(interval.Interval.from_proto(p), ival)

  def test_check_non_empty(self):
    self.assertRaisesRegex(
        ValueError, interval.INTERVAL_EMPTY_MESSAGE, I_EMPTY.check_non_empty
    )

  def test_zero(self):
    self.assert_all_equal(interval.Interval.zero().bounds, [0, 0])

  def test_unit(self):
    self.assert_all_equal(interval.Interval.unit().bounds, [0, 1])

  def test_infinity(self):
    self.assert_all_equal(
        interval.Interval.infinity().bounds, [-np.inf, np.inf]
    )

  def test_create_empty(self):
    self.assert_all_equal(
        interval.Interval.create_empty().bounds, [np.inf, -np.inf]
    )

  def test_from_value(self):
    self.assert_all_equal(interval.Interval.from_value(2.5).bounds, [2.5, 2.5])

  def test_from_length(self):
    self.assert_all_equal(interval.Interval.from_length(5).bounds, [-2.5, 2.5])


if __name__ == '__main__':
  absltest.main()
