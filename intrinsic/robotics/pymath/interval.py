# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Interval class (python3).

This library implements an Interval class which represents a closed interval
with minimum and maximum floating point values.
"""
from typing import Optional, Text, Union
from intrinsic.robotics.messages import interval_pb2
from intrinsic.robotics.pymath import math_types
from intrinsic.robotics.pymath import vector_util
import numpy as np

# ----------------------------------------------------------------------------
# Pytype definitions.
IntervalProtoType = Union[
    interval_pb2.Intervald, interval_pb2.Intervalf, interval_pb2.Intervali
]

# ----------------------------------------------------------------------------
# Error messages for exceptions.
INTERVAL_EMPTY_MESSAGE = 'Interval contains no values.'

INTERVAL_INVALID_BOUNDS_MESSAGE = 'Interval has invalid bounds.'

NEGATIVE_SCALE_FACTOR_MESSAGE = 'Scale factor must be non-negative.'


class Interval(object):
  """A closed interval represented by a pair of minimum and maximum values.

  Represents the closed interval with the bounds vector [minimum, maximum].

  The minimum and maximum values can be any float values, including -np.inf and
  np.inf.

    The interval contains all values x such that minimum <= x <= maximum.

  If minimum > maximum, the interval contains no values and is said to be empty.
  All empty intervals are considered equivalent, regardless of how they are
  defined, since all represent the empty set.  Operations like scale and inflate
  are not defined on empty intervals and may have unpredictable results.

  Attributes:
    _bounds: [minimum, maximum], representation as a numpy array.

  Properties:
    bounds: Minimum and maximum values as a numpy array.
    minimum: Minimum interval value.
    maximum: Maximum interval value.
    empty: True if the interval contains no values (maximum < minimum).
    bounded: True if the endpoints are finite.
    bounded_below: True if the minimum value is finite.
    bounded_above: True if the maximum value is finite.
    unbounded: True if at least one endpoint is infinite.
    length: Length of interval (maximum - minimum).
    center: Midpoint of interval (maximum + minimum) / 2.
  Factory functions:
    zero: Returns the interval [0, 0].
    unit: Returns the interval [0, 1].
    infinity: Returns the inbounded interval [-np.inf, np.inf].
    from_length: Returns an interval centered at zero with the given length.
    from_value: Returns the interval [value, value].
  """

  def __init__(self, bounds: math_types.Vector2Type):
    """Initializes the interval with min and max values.

    If no components are given, the default is the zero interval.

    Args:
      bounds: [minimum, max] values.
    """
    self._bounds = np.zeros(2, dtype=np.float64)
    self.bounds = bounds

  # --------------------------------------------------------------------------
  # Properties
  # --------------------------------------------------------------------------

  @property
  def bounds(self) -> np.ndarray:
    """Returns the [min, max] values of the interval."""
    return self._bounds.copy()

  @bounds.setter
  def bounds(self, bounds: math_types.Vector2Type) -> None:
    """Returns minimum value of the interval."""
    self._bounds[:] = bounds
    self._check_valid()

  @property
  def minimum(self) -> float:
    """Returns minimum value of the interval."""
    if self.empty:
      return np.inf
    return self._bounds[0]

  @minimum.setter
  def minimum(self, min_value: float) -> None:
    """Returns minimum value of the interval."""
    self._bounds[0] = min_value
    self._check_valid()

  @property
  def maximum(self) -> float:
    """Returns maximum value of the interval."""
    if self.empty:
      return -np.inf
    return self._bounds[1]

  @maximum.setter
  def maximum(self, max_value: float) -> None:
    """Returns maximum value of the interval."""
    self._bounds[1] = max_value
    self._check_valid()

  @property
  def empty(self) -> bool:
    """Returns true if the interval contains no values."""
    return self._bounds[1] < self._bounds[0]

  @property
  def bounded(self) -> bool:
    """Returns true if the interval contains no values."""
    return self.empty or np.all(np.isfinite(self.bounds))

  @property
  def bounded_below(self) -> bool:
    """Returns true if the interval does not contain -np.inf."""
    return self.empty or np.isfinite(self.minimum)

  @property
  def bounded_above(self) -> bool:
    """Returns true if the interval does not contain np.inf."""
    return self.empty or np.isfinite(self.maximum)

  @property
  def unbounded(self) -> bool:
    return not self.bounded

  @property
  def length(self) -> float:
    """Returns length of the interval."""
    if self.empty:
      return 0
    if self.bounded:
      return self.maximum - self.minimum
    else:
      return np.inf

  @property
  def center(self) -> float:
    """Returns the midpoint of the interval."""
    if self.empty:
      return 0
    return self.interpolate(0.5)

  # --------------------------------------------------------------------------
  # Operations
  # --------------------------------------------------------------------------

  def __eq__(self, other: 'Interval') -> bool:
    """Returns true if the two intervals contain the same values."""
    return (self.empty and other.empty) or np.all(self._bounds == other._bounds)

  def __add__(self, delta: float) -> 'Interval':
    return self.shift(delta)

  def __radd__(self, delta: float) -> 'Interval':
    return self.shift(delta)

  def __sub__(self, delta: float) -> 'Interval':
    return self.shift(-delta)

  def __mul__(self, scale_factor: float) -> 'Interval':
    """Returns the scaled interval [min * scale_factor, max * scale_factor]."""
    return self.scale(scale_factor)

  def __rmul__(self, scale_factor: float) -> 'Interval':
    """Returns the scaled interval [min * scale_factor, max * scale_factor]."""
    # Multiplication with real scalar values is commutative.
    return self.scale(scale_factor)

  def __truediv__(self, inverse_scale_factor: float) -> 'Interval':
    return self.scale(1.0 / inverse_scale_factor)

  def __str__(self) -> str:
    if self.empty:
      return '[EMPTY]'
    return '[%s, %s]' % (self.minimum, self.maximum)

  def __repr__(self) -> str:
    return '[%r, %r]' % (self.minimum, self.maximum)

  # --------------------------------------------------------------------------
  # Interval Operations
  # --------------------------------------------------------------------------

  def almost_equal(
      self,
      other: 'Interval',
      rtol: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
      atol: float = math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE,
  ) -> bool:
    """Tests whether the two intervals are equivalent within tolerances.

    The two intervals are equivalent if the maximum absolute difference between
    the elements of the two intervals is <= atol and the relative difference is
    <= rtol.

    Args:
      other: another interval to test against this one
      rtol: relative tolerance
      atol: absolute tolerance

    Returns:
      True if the two intervals are equivalent.
    """
    return (self.empty and other.empty) or np.allclose(
        self.bounds, other.bounds, rtol=rtol, atol=atol
    )

  def contains(self, other: Union[float, 'Interval']) -> bool:
    if isinstance(other, Interval):
      return self._contains_interval(other)
    else:
      return self._contains_value(other)

  def _contains_value(self, value: float) -> bool:
    return (self.minimum <= value) and (self.maximum >= value)

  def _contains_interval(self, other: 'Interval') -> bool:
    return other.empty or (
        self.minimum <= other.minimum and self.maximum >= other.maximum
    )

  def intersection(self, other: 'Interval') -> 'Interval':
    return Interval(
        [max(self.minimum, other.minimum), min(self.maximum, other.maximum)]
    )

  def intersects(self, other: 'Interval') -> bool:
    return not self.intersection(other).empty

  def union(self, other: 'Interval') -> 'Interval':
    if other.empty:
      return self
    if self.empty:
      return other
    return Interval(
        [min(self.minimum, other.minimum), max(self.maximum, other.maximum)]
    )

  def insert(self, value: float) -> 'Interval':
    return self.union(Interval.from_value(value))

  def mirror(self) -> 'Interval':
    return Interval((-self.maximum, -self.minimum))

  def clamp(self, other: Union[float, 'Interval']) -> Union[float, 'Interval']:
    if isinstance(other, Interval):
      return self._clamp_interval(other)
    else:
      return self._clamp_value(other)

  def _clamp_value(self, value: float) -> float:
    """Returns the closest point in the interval to the value."""
    if self.empty:
      return value
    if value < self.minimum:
      return self.minimum
    if value > self.maximum:
      return self.maximum
    return value

  def _clamp_interval(self, other: 'Interval') -> 'Interval':
    """Clamps the other interval to this interval.

    Returns the intersection of the two intervals if it is non-empty.
    Returns an empty interval if either interval is empty.
    Otherwise, returns the closest endpoint in this interval to the other.

    Args:
      other: The interval to be clamped.

    Returns:
      The clamped interval.
    """
    if self.empty:
      return self
    if other.empty:
      return other
    return Interval((self.clamp(other.minimum), self.clamp(other.maximum)))

  def distance(self, other: Union[float, 'Interval']) -> float:
    if isinstance(other, Interval):
      return self._distance_interval(other)
    else:
      return self._distance_value(other)

  def _distance_value(self, value: float) -> float:
    """Returns the signed distance from the value to an endpoint of the interval.

     When the value is not contained in the interval, the distance is equal to
     the radius of the largest interval centered on the value that does not
     intersect with this interval.  For an empty interval, this value is
     infinite.

     When the value is contained in the interval, the distance is equal to the
     negative of the radius of the largest interval centered on the value that
     is contained by this interval.

     If the value is contained in the interval, the distance is negative.

     This graph shows the distance function over the interval.  It has the value
     zero at each endpoint.  It is negative inside the interval, with a minimum
     at the midpoint.

     distance
       ^
       |   min - x       x - max
       |      ^             ^
       |       .           .
       |        .interval .
     <-+---------[-------]-----------> x
       |          .     .
       |           .   .
       |            . .
       |             *
       v

    Returns np.inf if the interval is empty.

    Args:
      value: The value to be measured.

    Returns:
      Signed distance from the value to the interval.
    """
    if self.empty:
      return np.inf
    if np.isfinite(value):
      return max(self.minimum - value, value - self.maximum)
    return -np.inf if self._contains_value(value) else np.inf

  def _distance_interval(self, other: 'Interval') -> float:
    """Returns the signed distance from the other interval to this interval.

    The distance is the signed distance to the closest endpoint of this
    interval.

    This is not symmetric.

    Any interval that contains an endpoint of this interval has distance zero.

    Any disjoint interval will have positive distance to this interval.

    Any contained interval will have negative distance to this interval.

    Examples:
      Self             [0 . . . . 5]
      Dist: 0                [3 . . . . 8]
      Dist: 2                        [7 . 9]
      Dist: -1              [2 . 4]

    Args:
      other: The interval to measure distance against.

    Returns:
      Signed distance from this interval to the other.
    """
    if self.empty or other.empty:
      return np.inf
    if self.minimum > other.maximum:
      return self.minimum - other.maximum
    if other.minimum > self.maximum:
      return other.minimum - self.maximum
    if self._contains_interval(other):
      return max(
          self._distance_value(other.minimum),
          self._distance_value(other.maximum),
      )
    return 0

  def closest_value(self, value: float) -> float:
    """Returns the closest value in this interval to the given value."""
    if self.empty:
      return value
    elif self.minimum > value:
      return self.minimum
    elif self.maximum < value:
      return self.maximum
    else:
      # The value is contained in the interval.
      return value

  def interpolate(self, t: float) -> float:
    """Returns a value interpolated along the interval.

    interpolate(0) = minimum
    interpolate(1) = maximum
    interpolate(0.5) = center

    Unbounded intervals will return infinite values for most values of t.

    Args:
      t: Interpolation parameter, usually but not necessarily in [0, 1].

    Returns:
      Interpolated value in the interval.
    """
    if self.bounded:
      return self.minimum * (1 - t) + self.maximum * t
    elif self.bounded_below:
      return -np.inf if t < 0 else self.minimum if t == 0 else np.inf
    elif self.bounded_above:
      return -np.inf if t < 1 else self.maximum if t == 1 else np.inf
    else:
      return -np.inf if t < 0.5 else 0 if t == 0.5 else np.inf

  # --------------------------------------------------------------------------
  # Interval Transformations.
  # --------------------------------------------------------------------------

  def scale(self, scale_factor: float) -> 'Interval':
    """Scales the endpoints of the interval.

    Inverts the interval if the scale factor is negative.

    For example:
      [2, 4].scale(3) = [6, 12]
      [2, 4].scale(0) = [0, 0]
      [2, 4].scale(-1) = [-4, -2]

    Args:
      scale_factor: A scale factor for the endpoints of an interval.

    Returns:
      The scaled interval.
    """
    if self.empty:
      return self
    if scale_factor == 0:
      return Interval.zero()
    if scale_factor < 0:
      return self.scale(-scale_factor).mirror()
    return Interval(bounds=self.bounds * scale_factor)

  def scale_length(self, scale_factor: float) -> 'Interval':
    """Scales the length of the interval about its center.

    For example:
      [2, 4].scale_length(2) = [1, 5]
      The length is scaled by 2 from 2 to 4 and the center remains at 3.

    Returns the original interval if it is empty or has infinite length.

    Args:
      scale_factor: A scale factor for the length of an interval.

    Returns:
      The scaled interval.

    Raises:
      ValueError if the scale factor is negative.
    """
    if scale_factor < 0:
      raise ValueError(
          '%s: %s * %s  length=%s center=%s'
          % (
              NEGATIVE_SCALE_FACTOR_MESSAGE,
              self,
              scale_factor,
              self.length,
              self.center,
          )
      )

    if self.empty or self.unbounded:
      return self
    midpoint = self.center
    return Interval((
        midpoint + (self.minimum - midpoint) * scale_factor,
        midpoint + (self.maximum - midpoint) * scale_factor,
    ))

  def inflate(self, delta: float) -> 'Interval':
    """Inflates the interval by moving the endpoints outward by delta."""
    return Interval((self.minimum - delta, self.maximum + delta))

  def shift(self, delta: float) -> 'Interval':
    """Translates the interval by delta."""
    return Interval(bounds=self.bounds + delta)

  # --------------------------------------------------------------------------
  # Checks
  # --------------------------------------------------------------------------

  def check_non_empty(self, err_msg: Text = '') -> None:
    """Raises a ValueError exception if the interval is empty."""
    if self.empty:
      raise ValueError(
          '%s: %s  length=%s  %s'
          % (INTERVAL_EMPTY_MESSAGE, self, self.length, err_msg)
      )

  def _check_valid(self, err_msg: Text = '') -> None:
    """Raises a ValueError exception if the interval has invalid endpoints."""
    vector_util.as_vector(
        self._bounds,
        dimension=2,
        err_msg='%s %s' % (INTERVAL_INVALID_BOUNDS_MESSAGE, err_msg),
    )

  # --------------------------------------------------------------------------
  # Factory Functions
  # --------------------------------------------------------------------------

  @classmethod
  def zero(cls) -> 'Interval':
    """Returns the interval [0, 0]."""
    return cls((0, 0))

  @classmethod
  def unit(cls) -> 'Interval':
    """Returns the interval [0, 1]."""
    return cls((0, 1))

  @classmethod
  def infinity(cls) -> 'Interval':
    """Returns the interval [-infinity, infinity]."""
    return cls((-np.inf, np.inf))

  @classmethod
  def create_empty(cls) -> 'Interval':
    """Returns the empty interval [np.inf, -np.inf]."""
    return cls((np.inf, -np.inf))

  @classmethod
  def from_length(cls, length: float) -> 'Interval':
    """Returns the interval [-length/2, length/2]."""
    return cls((-length * 0.5, length * 0.5))

  @classmethod
  def from_value(cls, value: float) -> 'Interval':
    """Returns the interval [value, value]."""
    return cls((value, value))

  # --------------------------------------------------------------------------
  # Protobuf conversion
  # --------------------------------------------------------------------------

  @classmethod
  def from_proto(cls, interval_proto: IntervalProtoType) -> 'Interval':
    """Constructs an Interval from an Interval protobuf message."""
    return cls((interval_proto.min, interval_proto.max))

  def to_proto(
      self, proto_out: Optional[IntervalProtoType] = None
  ) -> IntervalProtoType:
    """Populates a Interval protobuf with this interval."""
    if proto_out is None:
      proto_out = interval_pb2.Intervald()
    proto_out.min = self.minimum
    proto_out.max = self.maximum
    return proto_out
