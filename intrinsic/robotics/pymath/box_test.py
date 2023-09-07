# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.robotics.pymath.box."""

import math

from absl import logging
from absl.testing import absltest
from intrinsic.robotics.pymath import box
from intrinsic.robotics.pymath import interval
from intrinsic.robotics.pymath import math_test
from intrinsic.robotics.pymath import vector_util
import numpy as np

I_ZERO = interval.Interval.zero()
I_UNIT = interval.Interval.unit()
I_ALL = interval.Interval.infinity()
I_NEGATIVE = interval.Interval((-np.inf, 0))
I_POSITIVE = interval.Interval((0, np.inf))

_BOX_SHAPE_MSG_PATTERN = 'Box array should have shape'
_BOX_INIT_INVALID_ARRAY_PATTERN = 'setting an array element with a sequence.'


class BoxTest(math_test.TestCase):

  def _box_init(self, array):
    return box.Box(array=array)

  def test_init(self):
    b = box.Box.from_corners([1, 2, 3], [4, 5, 6])
    self.assertEqual(box.Box(np.array([[1, 2, 3], [4, 5, 6]])), b)

  def test_init_list(self):
    b = box.Box.from_corners([1, 2, 3], [4, 5, 6])
    self.assertEqual(box.Box([[1, 2, 3], [4, 5, 6]]), b)
    self.assertEqual(box.Box([np.array([1, 2, 3]), np.array([4, 5, 6])]), b)
    self.assertRaisesRegex(
        ValueError,
        _BOX_SHAPE_MSG_PATTERN,
        self._box_init,
        [np.array([1, 2, 3]), np.array([4, 5, 6]), np.array([7, 8, 9])],
    )
    self.assertRaisesRegex(
        ValueError,
        _BOX_INIT_INVALID_ARRAY_PATTERN,
        self._box_init,
        [np.array([1, 2, 3]), np.array([4, 5, 6, 7])],
    )

  def test_init_tuple(self):
    b = box.Box.from_corners([1, 2, 3], [4, 5, 6])
    self.assertEqual(box.Box((np.array([1, 2, 3]), np.array([4, 5, 6]))), b)
    self.assertEqual(box.Box(([1, 2, 3], [4, 5, 6])), b)
    self.assertEqual(box.Box(((1, 2, 3), (4, 5, 6))), b)
    self.assertEqual(
        box.Box(((1, 2, 3), (4, 5, 6))),
        box.Box.from_corners([1, 2, 3], [4, 5, 6]),
    )
    self.assertRaisesRegex(
        ValueError,
        _BOX_INIT_INVALID_ARRAY_PATTERN,
        self._box_init,
        ((1, 2, 3), (4, 5)),
    )

  def test_array(self):
    test_box = box.Box.from_corners([1, 2, 3], [4, 5, 6])
    self.assert_all_equal(test_box.array, np.array([[1, 2, 3], [4, 5, 6]]))
    a = np.array([[1, 2], [3, 4]])
    test_box.array = a
    self.assert_all_equal(test_box.array, a)

  def test_dim(self):
    self.assertEqual(box.Box.from_corners([1, 2], [4, 5]).dim, 2)
    self.assertEqual(box.Box.from_corners([1, 2, 3], [4, 5, 6]).dim, 3)

  def test_minimum(self):
    b = box.Box.from_corners([1, 2, 3], [4, 5, 6])
    self.assert_all_equal(b.minimum, [1, 2, 3])
    b.minimum = [0, 1, 2]
    self.assert_all_equal(b.minimum, [0, 1, 2])
    self.assert_all_equal(b.maximum, [4, 5, 6])

  def test_maximum(self):
    b = box.Box.from_corners([1, 2], [4, 5])
    self.assert_all_equal(b.maximum, [4, 5])
    b.maximum = [7, 8]
    self.assert_all_equal(b.minimum, [1, 2])
    self.assert_all_equal(b.maximum, [7, 8])

  def test_x(self):
    b = box.Box.from_corners([1, 2], [4, 5])
    self.assertEqual(b.x, interval.Interval((1, 4)))
    b.x = I_ZERO
    self.assertEqual(b.x, I_ZERO)

  def test_y(self):
    b = box.Box.from_corners([1, 2], [4, 5])
    self.assertEqual(b.y, interval.Interval((2, 5)))
    b.y = I_ALL
    self.assertEqual(b.y, I_ALL)

  def test_z(self):
    b = box.Box.from_corners([1, 2, 3, 10], [4, 5, 6, 20])
    self.assertEqual(b.z, interval.Interval((3, 6)))
    b.z = I_UNIT
    self.assertEqual(b.z, I_UNIT)

  def _get_z(self, b):
    return b.z

  def test_z_invalid(self):
    self.assertRaisesRegex(
        IndexError,
        'index 2 is out of bounds for axis 1 with size 2',
        self._get_z,
        box.Box.unit(dim=2),
    )

  def test_w(self):
    b = box.Box.from_corners([1, 2, 3, 10], [4, 5, 6, 20])
    self.assertEqual(b.w, interval.Interval((10, 20)))
    b.w = I_POSITIVE
    self.assertEqual(b.w, I_POSITIVE)

  def _get_w(self, b):
    return b.w

  def test_w_invalid(self):
    self.assertRaisesRegex(
        IndexError,
        'index 3 is out of bounds for axis 1 with size 2',
        self._get_w,
        box.Box.unit(dim=2),
    )
    self.assertRaisesRegex(
        IndexError,
        'index 3 is out of bounds for axis 1 with size 3',
        self._get_w,
        box.Box.unit(dim=3),
    )

  def test_bounded(self):
    self.assertTrue(box.Box.from_corners([1, 2, 3], [4, 5, 6]).bounded)
    self.assertFalse(box.Box.from_corners([1, 2, -np.inf], [4, 5, 6]).bounded)
    self.assertFalse(box.Box.from_corners([1, 2, 3], [4, np.inf, 6]).bounded)
    self.assertFalse(box.Box.infinity(dim=4).bounded)

  def test_unbounded(self):
    self.assertFalse(box.Box.from_corners([1, 2, 3], [4, 5, 6]).unbounded)
    self.assertTrue(box.Box.from_corners([1, 2, -np.inf], [4, 5, 6]).unbounded)
    self.assertTrue(box.Box.from_corners([1, 2, 3], [4, np.inf, 6]).unbounded)
    self.assertTrue(box.Box.infinity(dim=4).unbounded)

  def test_diagonal(self):
    self.assert_all_equal(
        box.Box.from_corners([1, 2, 3], [4, 5, 6]).diagonal, [3, 3, 3]
    )

  def test_diagonal_empty(self):
    self.assert_all_equal(box.Box.create_empty(dim=4).diagonal, [0, 0, 0, 0])

  def test_diagonal_infinite(self):
    self.assert_all_equal(box.Box.infinity(dim=2).diagonal, [np.inf, np.inf])
    self.assert_all_equal(
        box.Box.from_intervals(
            [I_ALL, I_POSITIVE, I_NEGATIVE, I_UNIT]
        ).diagonal,
        [np.inf, np.inf, np.inf, 1],
    )

  def test_center(self):
    self.assert_all_equal(
        box.Box.from_corners([1, 2, 3], [5, 6, 7]).center, [3, 4, 5]
    )

  def test_center_empty(self):
    self.assert_all_equal(box.Box.create_empty(dim=4).center, [0, 0, 0, 0])

  def test_center_infinite(self):
    self.assert_all_equal(box.Box.infinity(dim=2).center, [0, 0])
    self.assert_all_equal(
        box.Box.from_intervals([I_ALL, I_POSITIVE, I_NEGATIVE, I_UNIT]).center,
        [0, np.inf, -np.inf, 0.5],
    )

  def test_eq(self):
    b1 = box.Box.from_corners([-1, 0, 1], [0, 1, 2])
    b2 = box.Box.from_corners([-1, 1, 1], [0, 1, 2])
    self.assertEqual(b1, b1)
    self.assertEqual(b2, b2)
    self.assertNotEqual(b1, b2)

  def test_eq_empty(self):
    b = box.Box.create_empty(dim=2)
    self.assertEqual(b, box.Box.from_corners([1, 1], [0, 0]))

  def test_add(self):
    a = np.array([[-1, 0, 1], [0, 1, 2]])
    b = box.Box(array=a)
    self.assertEqual(b + 2, box.Box(array=a + 2))
    self.assertEqual(2 + b, b + 2)
    self.assertEqual(b + 0, b)
    self.assertEqual(0 + b, b)

  def test_add_empty(self):
    self.assert_empty(box.Box.create_empty(dim=2) + 1)

  def test_sub(self):
    b = box.Box(array=np.array([[-1, 0, 1], [0, 1, 2]]))
    self.assertEqual(b - 2, b + (-2))

  def test_sub_empty(self):
    self.assert_empty(box.Box.create_empty(dim=2) - 1)

  def test_mul(self):
    b = box.Box.from_corners([-1, 0, 1], [0, 1, 2])
    self.assert_all_equal((b * 2).array, b.array * 2)
    self.assertEqual(b * 2, 2 * b)

  def test_mul_negative(self):
    b = box.Box.from_corners([-1, 0, 1], [0, 1, 2])
    self.assert_all_equal((b * (-1)).minimum, -b.maximum)
    self.assert_all_equal((b * (-2)).maximum, -2 * b.minimum)

  def test_mul_empty(self):
    b = box.Box.create_empty(dim=4)
    self.assert_empty(b * 2)
    self.assert_empty(2 * b)

  def test_div(self):
    b = box.Box.from_corners([-1, 0, 1], [0, 1, 2])
    self.assert_all_equal((b / 2).array, b.array / 2)
    self.assertEqual(b / 2, b * 0.5)

  def test_div_negative(self):
    b = box.Box.from_corners([-1, 0, 1], [0, 1, 2])
    self.assert_all_equal((b / (-1)).minimum, -b.maximum)
    self.assert_all_equal((b / (-2)).maximum, -0.5 * b.minimum)

  def test_div_empty(self):
    b = box.Box.create_empty(dim=4)
    self.assertEqual(b, b / 2)

  def test_str(self):
    b = box.Box(array=[[1, 2, 3], [4, 5, 6]])
    logging.info('%s', b)
    self.assertEqual('%s' % b, 'Box([1. 2. 3.], [4. 5. 6.])')
    self.assertEqual('%s' % box.Box.create_empty(3), 'Box(EMPTY, dim=3)')

  def test_repr(self):
    b = box.Box(array=[[-1, -2], [4, 5]])
    logging.info('%r', b)
    self.assertEqual('%r' % b, 'Box(array([-1., -2.]), array([4., 5.]))')
    self.assertEqual(
        '%r' % box.Box.create_empty(3),
        'Box(array([inf, inf, inf]), array([-inf, -inf, -inf]))',
    )

  def test_intervals(self):
    intervals = [I_ALL, I_POSITIVE, I_NEGATIVE, I_UNIT]
    self.assertEqual(box.Box.from_intervals(intervals).intervals(), intervals)

  def test_corners(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    a, b = box.Box.from_corners(min_corner, max_corner).corners()
    self.assert_all_equal(a, min_corner)
    self.assert_all_equal(b, max_corner)

  def test_contains_point(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assert_contains(b, min_corner)
    self.assert_contains(b, max_corner)
    self.assert_contains(b, [3, 3, 3])
    self.assert_not_contains(b, [0, 3, 3])
    self.assert_not_contains(b, [0, 1, 2])
    self.assert_not_contains(b, [0, 10, 5])

  def test_contains_point_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError, vector_util.VECTOR_COMPONENTS_MESSAGE, b.contains, [1, 2]
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        b.contains,
        [1, 2, 3, 4],
    )

  def test_contains_box(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assert_contains(b, b)
    self.assert_contains(b, box.Box.from_point(min_corner))
    self.assert_contains(b, box.Box.from_point(max_corner))
    self.assert_contains(b.inflate(1), b)
    self.assert_not_contains(b, b.inflate(1))
    self.assert_not_contains(b, b + 1)
    self.assert_not_contains(b, box.Box.from_corners([-1, -1, -1], [0, 0, 0]))

  def test_contains_box_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        b.contains,
        box.Box.zero(2),
    )
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        b.contains,
        box.Box.unit(7),
    )

  def test_intersection(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    b_min = box.Box.from_point(min_corner)
    b_max = box.Box.from_point(max_corner)
    self.assertEqual(b.intersection(b), b)
    self.assertEqual(b.intersection(b_min), b_min)
    self.assertEqual(b_max.intersection(b), b_max)
    self.assert_intersects(b, b + 1)
    self.assert_not_intersects(b, b + 10)
    self.assert_contains(b, b.intersection(b + 1))
    self.assert_contains(b + 1, b.intersection(b + 1))
    self.assert_empty(b.intersection(b + 10))

  def test_intersection_empty(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b_empty = box.Box.create_empty(dim=3)
    b = box.Box.from_corners(min_corner, max_corner)
    self.assertEqual(b.intersection(b_empty), b_empty)
    self.assertEqual(b_empty.intersection(b), b_empty)
    self.assert_not_intersects(b, b_empty)
    self.assert_not_intersects(b_empty, b)

  def test_union_self(self):
    min_corner = [1, 2, 3, 4]
    max_corner = [4, 5, 6, 7]
    b = box.Box.from_corners(min_corner, max_corner)
    b_min = box.Box.from_point(min_corner)
    b_max = box.Box.from_point(max_corner)
    self.assertEqual(b.union(b), b)
    self.assertEqual(b.union(b_min), b)
    self.assertEqual(b_max.union(b), b)

  def test_union(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assert_contains(b.union(b + 1), b)
    self.assert_contains(b.union(b + 10), b)
    self.assert_contains(b.union(b - 1), b)
    self.assert_contains(b.union(b - 10), b)
    self.assert_not_contains(b, b.union(b + 1))

  def test_union_empty(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    b_empty = box.Box.create_empty(dim=3)
    self.assertEqual(b.union(b_empty), b)
    self.assertEqual(b_empty.union(b), b)

  def test_insert(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assertEqual(b.insert(min_corner), b)
    self.assertEqual(b.insert(max_corner), b)
    p = [10, 0, 5]
    self.assertEqual(b.insert(p), b.union(box.Box.from_point(p)))

  def test_insert_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assertEqual(b_empty.insert(min_corner).insert(max_corner), b)
    self.assertEqual(b_empty.insert(max_corner).insert(min_corner), b)

  def test_mirror(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    self.assertEqual(
        b.mirror(), box.Box.from_corners([-4, -5, -6], [-1, -2, -3])
    )
    self.assertEqual(b.mirror().mirror(), b)

  def test_clamp(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    b_min = box.Box.from_point(min_corner)
    b_max = box.Box.from_point(max_corner)
    self.assertEqual(b.clamp(b_min), b_min)
    self.assertEqual(b_min.clamp(b), b_min)
    self.assertEqual(b.clamp(b + 1), b.intersection(b + 1))
    self.assertEqual(b.clamp(b + 10), b_max)
    self.assertEqual(b.clamp(b - 10), b_min)

  def test_clamp_empty(self):
    min_corner = [1, 2, 3]
    max_corner = [4, 5, 6]
    b = box.Box.from_corners(min_corner, max_corner)
    b_empty = box.Box.create_empty(dim=3)
    self.assertEqual(b_empty.clamp(b_empty), b_empty)
    self.assertEqual(b.clamp(b_empty), b_empty)
    self.assertEqual(b_empty.clamp(b), b_empty)
    self.assert_all_equal(b_empty.clamp(min_corner), min_corner)

  def test_distance_point(self):
    min_corner = np.array([1.0, 2.0, 3.0])
    max_corner = np.array([4.0, 5.0, 6.0])
    b = box.Box.from_corners(min_corner, max_corner)
    self.assertEqual(b.distance(min_corner), 0)
    self.assertEqual(b.distance(max_corner), 0)
    self.assertEqual(b.distance([1, 4, 4]), 0)
    self.assertEqual(b.distance([2, 3, 4]), -1)
    self.assertEqual(b.distance([0, 3, 4]), 1)
    self.assertEqual(b.distance([3, 7, 3]), 2)
    self.assertEqual(b.distance(min_corner - 1.0), math.sqrt(3))
    self.assertEqual(b.distance(max_corner + 1.0), math.sqrt(3))
    self.assertEqual(b.distance([0, 6, 2]), math.sqrt(3))

  def test_distance_box(self):
    min_corner = np.array([1.0, 2.0, 3.0])
    max_corner = np.array([4.0, 5.0, 6.0])
    b = box.Box.from_corners(min_corner, max_corner)
    b_min = box.Box.from_point(min_corner)
    b_max = box.Box.from_point(max_corner)
    self.assertEqual(b.distance(b), 0)
    self.assertEqual(b.distance(b + 1), 0)
    self.assertEqual(b.distance(b_min), 0)
    self.assertEqual(b.distance(b_max), 0)
    self.assertEqual(b.distance(b.inflate(1)), 0)
    # Strictly contained box has negative distance.
    self.assertEqual(b.inflate(1).distance(b), -1)
    # Disjoint box has positive distance.
    self.assertEqual(b.distance(b_min - 1), math.sqrt(3))
    self.assertEqual(b.distance(b_max + 1), math.sqrt(3))
    self.assertEqual(b.distance(b + 4), math.sqrt(3))

  def test_distance_empty(self):
    min_corner = np.array([1.0, 2.0, 3.0])
    max_corner = np.array([4.0, 5.0, 6.0])
    b = box.Box.from_corners(min_corner, max_corner)
    b_empty = box.Box.create_empty(dim=3)
    self.assertEqual(b_empty.distance(min_corner), np.inf)
    self.assertEqual(b_empty.distance(b), np.inf)
    self.assertEqual(b_empty.distance(b_empty), np.inf)
    self.assertEqual(b.distance(b_empty), np.inf)

  def test_closest_point(self):
    min_corner = np.array([1.0, 2.0, 3.0])
    max_corner = np.array([4.0, 5.0, 6.0])
    b = box.Box.from_corners(min_corner, max_corner)
    self.assert_all_equal(b.closest_point(min_corner), min_corner)
    self.assert_all_equal(b.closest_point(max_corner), max_corner)
    self.assert_all_equal(b.closest_point(min_corner - 1), min_corner)
    self.assert_all_equal(b.closest_point(max_corner + 1), max_corner)
    self.assert_all_equal(b.closest_point([0, 3, 7]), [1, 3, 6])

  def test_closest_point_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    p = [1, 2, 3]
    self.assert_all_equal(b_empty.closest_point(p), p)

  def test_interpolate(self):
    min_corner = np.array([1.0, 2.0, 3.0])
    max_corner = np.array([4.0, 5.0, 6.0])
    b = box.Box.from_corners(min_corner, max_corner)
    self.assert_all_equal(b.interpolate(0), min_corner)
    self.assert_all_equal(b.interpolate(1), max_corner)
    self.assert_all_equal(b.interpolate(0.5), b.center)

  def test_scale_corners(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    b_scaled = b.scale_corners(3)
    self.assert_all_equal(b_scaled.minimum, b.minimum * 3)
    self.assert_all_equal(b_scaled.center, b.center * 3)
    self.assert_all_equal(b_scaled.maximum, b.maximum * 3)
    self.assertEqual(b.scale_corners(2).scale_corners(0.5), b)

  def test_scale_corners_nonuniform(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    v = [0, 1, 2]
    b_scaled = b.scale_corners(v)
    self.assertEqual(b_scaled, box.Box.from_corners([0, 1, 4], [0, 5, 12]))
    self.assert_all_equal(b_scaled.minimum, b.minimum * v)
    self.assert_all_equal(b_scaled.maximum, b.maximum * v)
    self.assert_all_equal(b_scaled.center, b.center * v)
    self.assert_all_equal(b_scaled.diagonal, b.diagonal * v)
    self.assert_not_contains(b.scale_corners(1.1), b)

  def test_scale_corners_negative(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    v = [0, 1, -1]
    b_scaled = b.scale_corners(v)
    self.assertEqual(b_scaled, box.Box.from_corners([0, 1, -6], [0, 5, -2]))
    self.assert_all_equal(b_scaled.center, b.center * v)
    self.assert_all_equal(b_scaled.diagonal, b.diagonal * np.abs(v))

  def test_scale_corners_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    self.assert_empty(b_empty.scale_corners(2))
    self.assert_empty(b_empty.scale_corners(0))
    self.assert_empty(b_empty.scale_corners(-1))

  def test_scale_corners_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError,
        vector_util.VECTOR_COMPONENTS_MESSAGE,
        b.scale_corners,
        [1, 2],
    )

  def test_scale_size(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    b_scaled = b.scale_size(3)
    self.assert_all_equal(b_scaled.minimum, b.minimum - 4)
    self.assert_all_equal(b_scaled.center, b.center)
    self.assert_all_equal(b_scaled.maximum, b.maximum + 4)
    self.assertEqual(b.scale_size(2).scale_size(0.5), b)
    self.assert_contains(b.scale_size(1.1), b)

  def test_scale_size_nonuniform(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    v = [0, 1, 2]
    b_scaled = b.scale_size(v)
    self.assertEqual(b_scaled, box.Box.from_corners([2, 1, 0], [2, 5, 8]))
    self.assert_all_equal(b_scaled.center, b.center)
    self.assert_all_equal(b_scaled.diagonal, b.diagonal * v)
    self.assert_contains(b.scale_size([1, 1.1, 1.2]), b)

  def test_scale_size_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    self.assert_empty(b_empty.scale_size(2))
    self.assert_empty(b_empty.scale_size(0))
    self.assert_empty(b_empty.scale_size([1, 0, 2]))

  def test_scale_size_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError, vector_util.VECTOR_COMPONENTS_MESSAGE, b.scale_size, [1, 2]
    )
    self.assertRaisesRegex(
        ValueError, interval.NEGATIVE_SCALE_FACTOR_MESSAGE, b.scale_size, -1
    )
    self.assertRaisesRegex(
        ValueError,
        interval.NEGATIVE_SCALE_FACTOR_MESSAGE,
        b.scale_size,
        [1, -2, 3],
    )

  def test_translate(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assert_all_equal(b.translate(1).array, [[1, 2, 3], [5, 6, 7]])
    self.assertEqual(b.translate(2).translate(-2), b)

  def test_translate_nonuniform(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    v = [1, 0, -1]
    b_translated = b.translate(v)
    self.assert_all_equal(b_translated.array, [[1, 1, 1], [5, 5, 5]])
    self.assert_all_equal(b_translated.minimum, b.minimum + v)
    self.assert_all_equal(b_translated.maximum, b.maximum + v)
    self.assert_all_equal(b_translated.center, b.center + v)
    self.assert_not_contains(b.translate([1, 0, 0]), b)

  def test_translate_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    self.assert_empty(b_empty.translate(2))
    self.assert_empty(b_empty.translate([1, 2, 3]))

  def test_translate_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError, vector_util.VECTOR_COMPONENTS_MESSAGE, b.translate, [1, 2]
    )

  def test_inflate(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assert_all_equal(b.inflate(1).array, [[-1, 0, 1], [5, 6, 7]])
    self.assertEqual(b.inflate(2).inflate(-2), b)
    self.assert_empty(b.inflate(-3))

  def test_inflate_nonuniform(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    v = [1, 0, -1]
    b_inflated = b.inflate(v)
    self.assert_all_equal(b_inflated.array, [[-1, 1, 3], [5, 5, 5]])
    self.assert_all_equal(b_inflated.minimum, b.minimum - v)
    self.assert_all_equal(b_inflated.maximum, b.maximum + v)
    self.assert_all_equal(b_inflated.center, b.center)

  def test_inflate_empty(self):
    b_empty = box.Box.create_empty(dim=3)
    self.assert_empty(b_empty.inflate(2))
    self.assert_empty(b_empty.inflate([-1, -2, -3]))

  def test_inflate_invalid(self):
    b = box.Box.from_corners([0, 1, 2], [4, 5, 6])
    self.assertRaisesRegex(
        ValueError, vector_util.VECTOR_COMPONENTS_MESSAGE, b.inflate, [1, 2]
    )

  def test_proto_2(self):
    b = box.Box.unit(dim=2)
    p = b.to_proto()
    self.assertEqual(box.Box.from_proto(p), b)

  def test_proto_3(self):
    b = box.Box.zero(dim=3)
    p = b.to_proto()
    self.assertEqual(box.Box.from_proto(p), b)

  def test_proto_4(self):
    b = box.Box.from_diagonal([1, 2, 3, 4])
    p = b.to_proto()
    self.assertEqual(box.Box.from_proto(p), b)

  def test_zero(self):
    self.assert_all_equal(box.Box.zero(dim=2).array, [[0, 0], [0, 0]])
    self.assert_all_equal(box.Box.zero(dim=3).array, [[0, 0, 0], [0, 0, 0]])

  def test_unit(self):
    self.assert_all_equal(box.Box.unit(dim=2).array, [[0, 0], [1, 1]])
    self.assert_all_equal(box.Box.unit(dim=3).array, [[0, 0, 0], [1, 1, 1]])

  def test_infinity(self):
    self.assert_all_equal(
        box.Box.infinity(dim=2).array, [[-np.inf, -np.inf], [np.inf, np.inf]]
    )
    self.assert_all_equal(
        box.Box.infinity(dim=3).array,
        [[-np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf]],
    )

  def test_create_empty(self):
    self.assert_all_equal(
        box.Box.create_empty(dim=2).array,
        [[np.inf, np.inf], [-np.inf, -np.inf]],
    )
    self.assert_all_equal(
        box.Box.create_empty(dim=3).array,
        [[np.inf, np.inf, np.inf], [-np.inf, -np.inf, -np.inf]],
    )

  def test_from_point(self):
    self.assert_all_equal(box.Box.from_point([1, 2]).array, [[1, 2], [1, 2]])
    self.assert_all_equal(
        box.Box.from_point([1, 2, 3]).array, [[1, 2, 3], [1, 2, 3]]
    )

  def test_from_interval(self):
    self.assertEqual(box.Box.from_interval(I_UNIT, dim=2), box.Box.unit(dim=2))
    self.assertEqual(box.Box.from_interval((0, 1), dim=3), box.Box.unit(dim=3))

  def test_from_intervals(self):
    self.assert_all_equal(
        box.Box.from_intervals([
            interval.Interval((1, 2)),
            interval.Interval((2, np.inf)),
            interval.Interval((-np.inf, 4)),
        ]).array,
        [[1, 2, -np.inf], [2, np.inf, 4]],
    )

  def test_from_diagonal(self):
    self.assert_all_equal(
        box.Box.from_diagonal([1, 2]).array, [[-0.5, -1], [0.5, 1]]
    )
    self.assert_all_equal(
        box.Box.from_diagonal([1, 2, 4]).array, [[-0.5, -1, -2], [0.5, 1, 2]]
    )

  def test_from_size(self):
    self.assert_all_equal(
        box.Box.from_size(size=4, dim=2).array, [[-2, -2], [2, 2]]
    )
    self.assert_all_equal(
        box.Box.from_size(size=1, dim=3).array,
        [[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
    )

  def test_from_corners_invalid(self):
    self.assertRaisesRegex(
        ValueError,
        box.BOX_INVALID_MESSAGE,
        box.Box.from_corners,
        [1, 2, 3],
        [1, 2, 3, 4],
    )

  def test_check_non_empty(self):
    b_empty = box.Box.create_empty(dim=5)
    self.assertRaisesRegex(
        ValueError, box.BOX_EMPTY_MESSAGE, b_empty.check_non_empty
    )

  def make_box_from_array(self, a):
    return box.Box(array=a)

  def test_check_valid_array(self):
    pattern = _BOX_SHAPE_MSG_PATTERN
    self.assertRaisesRegex(
        ValueError, pattern, self.make_box_from_array, np.zeros(3)
    )
    self.assertRaisesRegex(
        ValueError, pattern, self.make_box_from_array, np.zeros((3, 3))
    )
    self.assertRaisesRegex(
        ValueError, pattern, self.make_box_from_array, np.zeros((3, 2))
    )
    self.assertRaisesRegex(
        ValueError,
        box.BOX_ARRAY_NAN_MESSAGE,
        self.make_box_from_array,
        np.array([[3, 2, np.inf], [4, 5, np.nan]]),
    )


if __name__ == '__main__':
  absltest.main()
