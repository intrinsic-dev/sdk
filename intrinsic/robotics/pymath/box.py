# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Box class (python3).

  This library implements a Box class defined as a product of intervals.

A bounding box is defined by a minimum corner and maximum corner.
The box is closed on all sides, meaning that its edges are contained in the box.

A 2-dimensional Box is a square or rectangle.
A 3-dimensional Box is a cube or rectilinear solid.

A Box represented by min_corner and max_corner can be thought of as a Cartesian
product of intervals from the min_corner component to the max_corner component
in each dimension.  A point lies in the Box if each coordinate of the point lies
within the corresponding interval.

For example, b = Box([[0, 0, 0], [1, 1, 1]]) describes a unit cube in 3D with
one corner at the origin, with b.minimum = [0, 0, 0] and b.maximum = [1, 1, 1],
which could be written as a Cartesian product of intervals:
  [0,1] x [0,1] x [0,1].

In any dimension, if the minimum value is strictly greater than the maximum
value, the interval is empty (e.g. [1, 0]).  If any interval is empty, the
entire Box is considered to be empty, because no points exist with a coordinate
in that interval.
"""

from typing import Iterable, List, Optional, Text, Tuple, Union
from absl import logging
from intrinsic.robotics.messages import box_pb2
from intrinsic.robotics.pymath import interval
from intrinsic.robotics.pymath import math_types
from intrinsic.robotics.pymath import proto_util
from intrinsic.robotics.pymath import vector_util
import numpy as np

# ----------------------------------------------------------------------------
# Pytype definitions.

Box2ProtoType = Union[box_pb2.Box2d, box_pb2.Box2f, box_pb2.Box2i]
Box3ProtoType = Union[box_pb2.Box3d, box_pb2.Box3f, box_pb2.Box3i]
Box4ProtoType = Union[box_pb2.Box4d, box_pb2.Box4f, box_pb2.Box4i]
BoxProtoType = Union[Box2ProtoType, Box3ProtoType, Box4ProtoType]

BoxArrayType = Union[
    np.ndarray,
    Tuple[math_types.VectorType, math_types.VectorType],
    List[math_types.VectorType],
]

# ----------------------------------------------------------------------------
# Error messages for exceptions.

BOX_INVALID_MESSAGE = (
    'Box should be defined by two corners with the same dimensions.'
)

BOX_EMPTY_MESSAGE = (
    'Box is empty.  It has negative size in at least one dimension.'
)

BOX_ARRAY_SHAPE_MESSAGE = (
    'Box array should have shape (2,dimension) with dimension >= 2.'
)

BOX_ARRAY_NAN_MESSAGE = 'Box array should not contain any NaN values.'


class Box(object):
  """A closed, axially-aligned box represented as a pair of min and max corners.

  ------------------------------------------------------------------------------
  Representation:

  The box is represented by a 2D numpy array:

    [[min_corner]
     [max_corner]]

  It defines the set of points:

    v such that min_corner[i] <= v[i] <= max_corner[i] for all i

  ------------------------------------------------------------------------------
  Empty Boxes:

  If min_corner[i] > max_corner[i] in any dimension, the box contains no points
  and is said to be empty.

  All empty boxes are considered equivalent, regardless of how they are
  defined, since all represent the empty set.  Operations like scale and inflate
  are not defined on empty boxes and may have unpredictable results.

  Any empty box may be replaced by the canonical empty box.

  An empty box has:
    diagonal = zeros
    distance = np.inf
    closest_point(p) = p

  Operations on the coordinates of an empty box have undefined results.  Set
  operations have the expected results.

    b.union(empty) = b
    b.intersection(empty) = empty

  ------------------------------------------------------------------------------
  Attributes:
    _array: [min_value, max_value], the representation in a numpy array.

  Properties:
    array: Min and max values as a numpy array.
    dim: Number of dimensions.
    minimum: Minimum corner vector.
    maximum: Maximum corner vector.
    x, y, z, w: Interval in the dimension 0-3, respectively.
    empty: True if the box is empty.
    bounded: True if the box contains only finite values.
    unbounded: True if the box contains infinite values in any dimension.
    diagonal: Diagonal vector (max - min).
    center: Diagonal vector (max - min).
  Factory functions:
    zero: Returns the box [[0, 0, 0], [0, 0, 0]].
    unit: Returns the box [[0, 0, 0], [1, 1, 1]].
    infinity: Returns the unbounded box [[-np.inf], [np.inf]].
    from_interval: Returns a box with the given interval in every dimension.
    from_intervals: Returns a box with the given intervals in each dimension.
    from_corners: Returns a box with the given min and max corners.
    from_diagonal: Returns a box centered at zero with the given diagonal.
    from_value: Returns the box [[value], [value]].
  """

  def __init__(self, array: BoxArrayType):
    """Initializes the box with the corners defined in the array.

    Prefer to use from_corners or from_intervals, as they are less ambiguous.

    If the array is specified as a list or tuple, rather than a NumPy array, it
    must contain two vectors with the same number of elements.

    Args:
      array: Minimum and maximum corners of the box in a 2 x dim numpy array.

    Raises:
      ValueError: If array does not have valid shape.
    """
    self._array = np.array(array, copy=True, dtype=np.float64)
    self._check_array_valid()

  # --------------------------------------------------------------------------
  # Properties
  # --------------------------------------------------------------------------

  @property
  def array(self) -> np.ndarray:
    """Returns the [min, max] coordinates of the box as a 2D array."""
    return self._array.copy()

  @array.setter
  def array(self, array: np.ndarray) -> None:
    """Sets the [min, max] coordinates of the box from a 2D array."""
    self._array = array
    self._check_array_valid()

  @property
  def dim(self) -> int:
    """Returns the dimensionality of the vector space.

    For example, Box([[0, 0, 0], [1, 1, 1]]).dimension = 3
    """
    return self._array.shape[1]

  @property
  def minimum(self) -> np.ndarray:
    """Returns the minimum corner of the box.

    If the box is empty, returns a vector containing all infinity.
    """
    if self.empty:
      return np.full(self.dim, np.inf)
    return self._array[0, :]

  @minimum.setter
  def minimum(self, min_corner: math_types.VectorType) -> None:
    """Sets the minimum corner of the box."""
    self._array[0, :] = self.as_vector(min_corner)
    self._check_array_valid()

  @property
  def maximum(self) -> np.ndarray:
    """Returns the maximum corner of the box.

    If the box is empty, returns a vector containing all negative infinity.
    """
    if self.empty:
      return np.full(self.dim, -np.inf)
    return self._array[1, :]

  @maximum.setter
  def maximum(self, max_corner: math_types.VectorType) -> None:
    """Sets the maximum corner of the box."""
    self._array[1, :] = self.as_vector(max_corner)
    self._check_array_valid()

  @property
  def x(self) -> interval.Interval:
    """Returns x component (index 0) range of box."""
    return self[0]

  @property
  def y(self) -> interval.Interval:
    """Returns y component (index 1) range of box."""
    return self[1]

  @property
  def z(self) -> interval.Interval:
    """Returns z component (index 2) range of box."""
    return self[2]

  @property
  def w(self) -> interval.Interval:
    """Returns w component (index 3) range of box."""
    return self[3]

  @x.setter
  def x(self, ival: interval.Interval) -> None:
    """Sets the x component (index 0) range of box."""
    self[0] = ival
    self._check_array_valid()

  @y.setter
  def y(self, ival: interval.Interval) -> None:
    """Sets the y component (index 1) range of box."""
    self[1] = ival
    self._check_array_valid()

  @z.setter
  def z(self, ival: interval.Interval) -> None:
    """Sets the z component (index 2) range of box."""
    self[2] = ival
    self._check_array_valid()

  @w.setter
  def w(self, ival: interval.Interval) -> None:
    """Sets the w component (index 3) range of box."""
    self[3] = ival
    self._check_array_valid()

  @property
  def empty(self) -> bool:
    """Returns True if the box contains no points.

    A box is empty if the max value is less than the min value in any dimension.

    For example,
      Box([0, 0], [1, 1]).empty = False
      Box([0, 0], [0, 0]).empty = False
      Box([1, 1], [0, 0]).empty = True
      Box([0, 1], [1, 0]).empty = True
    """
    v_min = self._array[0, :]
    v_max = self._array[1, :]
    return (
        np.any(v_max < v_min)
        or np.any(v_min == np.inf)
        or np.any(v_max == -np.inf)
    )

  @property
  def bounded(self) -> bool:
    """Returns true if the box is bounded in every dimension."""
    return self.empty or np.all(np.isfinite(self._array))

  @property
  def unbounded(self) -> bool:
    """Returns true if the box is unbounded in some dimension."""
    return not self.bounded

  @property
  def diagonal(self) -> np.ndarray:
    """Returns the diagonal of the box, which is its size in each dimension."""
    if self.empty:
      return np.zeros(self.dim, dtype=np.float64)
    else:
      return np.asarray([i.length for i in self])

  @property
  def center(self) -> np.ndarray:
    """Returns the center of the box."""
    if self.empty:
      return np.zeros(self.dim, dtype=np.float64)
    else:
      return np.asarray([i.center for i in self])

  # --------------------------------------------------------------------------
  # Operators
  # --------------------------------------------------------------------------

  def __eq__(self, other: 'Box') -> bool:
    """Returns true if the two boxes contain the same values."""
    return (self.empty and other.empty) or np.all(self._array == other._array)

  def __getitem__(self, dim: int) -> interval.Interval:
    """Returns the interval range for the given dimension.

    If the box is empty in some dimensions and non-empty in other dimensions,
    this function may return a non-empty interval for an empty box.

    Args:
      dim: The dimension of the interval to be returned.

    Returns:
      The range of the box in the given dimension.
    """
    return interval.Interval(bounds=self._array[:, dim])

  def __setitem__(self, dim: int, ival: interval.Interval) -> None:
    """Sets the interval range for the given dimension.

    If the new interval is empty, the entire box will be empty, since there are
    no valid values in this dimension.

    Args:
      dim: The dimension of the interval to be modified.
      ival: Interval defining the new range of the box in this dimension.
    """
    self._array[:, dim] = ival.bounds

  def __mul__(self, scale_factor: float) -> 'Box':
    """Returns the box with corners scaled by the scale_factor."""
    return self.scale_corners(scale_factor)

  def __rmul__(self, scale_factor: float) -> 'Box':
    """Returns the box with corners scaled by the scale_factor."""
    return self.scale_corners(scale_factor)

  def __truediv__(self, inverse_scale_factor: float) -> 'Box':
    """Returns the box with corners scaled by 1/inverse_scale_factor."""
    return self.scale_corners(1.0 / inverse_scale_factor)

  def __add__(self, delta: math_types.VectorOrValueType) -> 'Box':
    """Translates all box components by delta."""
    return self.translate(delta)

  def __radd__(self, delta: math_types.VectorOrValueType) -> 'Box':
    """Translates all box components by delta."""
    return self + delta

  def __sub__(self, delta: math_types.VectorOrValueType) -> 'Box':
    """Translates all box components by -delta."""
    delta = self.as_vector(delta)
    return self.translate(-delta)

  def __str__(self) -> Text:
    """Returns a string that describes the box."""
    if self.empty:
      return 'Box(EMPTY, dim=%d)' % self.dim
    return 'Box(%s, %s)' % (self.minimum, self.maximum)

  def __repr__(self) -> Text:
    """Returns a string representation of the box."""
    return 'Box(%r, %r)' % (self.minimum, self.maximum)

  # --------------------------------------------------------------------------
  # Box Operations
  # --------------------------------------------------------------------------

  def intervals(self) -> List[interval.Interval]:
    """Returns an interval for each dimension as a list."""
    return list(self)

  def corners(self):
    """Returns minimum and maximum corners of the box."""
    return self.minimum, self.maximum

  def contains(self, other: Union[math_types.VectorType, 'Box']) -> bool:
    """Returns True if the point is contained in this box."""
    if isinstance(other, Box):
      return self._contains_box(other)
    else:
      return self._contains_point(other)

  def _contains_point(self, point: math_types.VectorType) -> bool:
    """Returns True if the box contains the point.

    A point on the boundary of the box is contained in the box.

             D
    +--------*        Box A contains points, B, C, and D.
    |A       |        Box A does not contain point E.
    |   B    |
    |   *    | E      A.ContainsPoint(B) = True
    |        | *      A.ContainsPoint(C) = True (on an edge)
    |     C  |        A.ContainsPoint(D) = True (on a corner)
    +-----*--+        A.ContainsPoint(E) = False

    An empty box cannot contain any point.

    Args:
      point: Point in space as a numpy array.

    Raises:
      ValueError: If query point has different dimensions from box.

    Returns:
      True if the box contains the point.
    """
    point = self.as_vector(point)
    return np.all(self.minimum <= point) and np.all(self.maximum >= point)

  def _contains_box(self, other: 'Box') -> bool:
    """Returns True if all points in the other box are contained in this one.

    Always returns True if the other box is empty.

    Always returns False if this box is empty and the other box is non-empty.

    Returns False if the boxes intersect, but this box does not completely
    contain the other box or if the boxes are entirely disjoint.

    A non-empty box contains itself.

    +---+----+
    |A  |   C|       Box A contains box C, but does not contain box B.
    |   +----+       Box B does not contain box A or box C.
    |        |       Box C does not contain box A or box B.
    |   +----|---+
    |   |    |   |   A.ContainsBox(C) = True
    +---|----+   |   A.ContainsBox(B) = False
        |       B|   C.ContainsBox(A) = False
        +--------+   C.ContainsBox(B) = False

    Args:
      other: Another box of the same dimensions.

    Returns:
      True if this box contains the other box.

    Raises:
      ValueError: If the two boxes have different dimensions.
    """
    return other.empty or (
        self.contains(other.minimum) and self.contains(other.maximum)
    )

  def intersection_in_place(self, other: 'Box') -> None:
    """Reduces the size of this box to its intersection with the other box."""
    logging.debug('%s.intersection_in_place(%s)', self, other)
    if self.empty:
      pass
    elif other.empty:
      self._array = self.create_empty(self.dim).array
    else:
      self.minimum = np.maximum(self.minimum, other.minimum)
      self.maximum = np.minimum(self.maximum, other.maximum)

  def intersection(self, other: 'Box') -> 'Box':
    """Returns the intersection of the two boxes as a new box.

                Amax
        +--------+     A.Intersection(B) = X =
        |A       |       [[B_min_x, A_min_y], [A_max_x, B_max_y]]
        |        |  Bmax
        |   +----+---+
        |   | X  |   |
        +---+----+   |
      Amin  |       B|
            +--------+
          Bmin

    The intersection of boxes A and B is box X.

    If two boxes do not overlap, the intersection will be empty.

    The intersection of an empty box with any other box is empty.

    A non-empty box intersects itself.

    Args:
      other: Another box of the same type.

    Returns:
      The intersection volume of this box with the other.

    Raises:
      ValueError: If other box has different dimensions from this box.
    """
    result = self.copy()
    result.intersection_in_place(other)
    return result

  def intersects(self, other: 'Box') -> bool:
    """Returns True if the two boxes overlap.

    This is identical to saying that the intersection of the two boxes is not
    empty.

    +---+----+       Box A intersects boxes B and C,
    |A  |C   |       Box B does not intersect box C.
    |   +----+       Box B intersects box D, because they share a boundary.
    |        |
    |   +----|---+---+  A.Intersects(B) = True
    |   |    |   |  D|  A.Intersects(C) = True
    +---|----+   +---+  A.Intersects(D) = False
        |       B|      B.Intersects(C) = False
        +--------+      B.Intersects(D) = True (along an edge)

    Args:
      other: Another box of the same type.

    Returns:
      True if this box intersects the other box.
    """
    return not self.intersection(other).empty

  def union_in_place(self, other: 'Box') -> None:
    """Increases the size of this box to contain the other box."""
    logging.debug('%s.union_in_place(%s)', self, other)
    if other.empty:
      pass
    elif self.empty:
      self._array = other.array
    else:
      self.minimum = np.minimum(self.minimum, other.minimum)
      self.maximum = np.maximum(self.maximum, other.maximum)

  def union(self, other: 'Box') -> 'Box':
    """Calculates the smallest box that contains both boxes.

    +---+----+  C = A.union(B) = B.union(A)
    |C  | A  |
    |   +----+
    |--+     |
    |B |     |
    +--+-----+

    The union of an empty box with any other box is the other box.

    Args:
      other: Another box of the same type.

    Returns:
      The union volume of this box with the other.

    Raises:
      ValueError: If other box has different dimensions from this box.
    """
    result = self.copy()
    result.union_in_place(other)
    return result

  def insert(self, point: math_types.VectorType) -> 'Box':
    """Expands the box to contain the point."""
    return self.union(Box.from_point(point))

  def mirror(self) -> 'Box':
    """Returns the box mirrored about the origin.

    +----------+
    |     A    |
    +----------+
             *
           +----------+
           | A.mirror |
           +----------+

    Returns:
      The box (-maximum, -minimum).
    """
    return Box.from_intervals([ival.mirror() for ival in self.intervals()])

  def clamp(
      self, other: Union[math_types.VectorType, 'Box']
  ) -> Union[np.ndarray, 'Box']:
    if isinstance(other, Box):
      return self._clamp_box(other)
    else:
      return self._clamp_point(other)

  def _clamp_point(self, point: math_types.VectorType) -> np.ndarray:
    """Returns the closest point in the box to the point."""
    point = self.as_vector(point)
    if self.empty:
      return point
    return np.maximum(np.minimum(point, self.maximum), self.minimum)

  def _clamp_box(self, other: 'Box') -> 'Box':
    """Clamps the other box to this box and returns the result.

    Returns the intersection of the two boxs if the boxes intersect.

    Returns an empty box if either box is empty.

    Otherwise, returns a flattened box containing all points in this box that
    are at the minimum distance to the other box.

    Args:
      other: The box to be clamped.

    Returns:
      The clamped box.
    """
    if self.empty:
      return self
    if other.empty:
      return other
    clamped_min = self.clamp(other.minimum)
    clamped_max = self.clamp(other.maximum)
    return Box._from_corners(clamped_min, clamped_max)

  def distance(self, other: Union[math_types.VectorType, 'Box']) -> float:
    """Returns the signed distance to this box."""
    if isinstance(other, Box):
      return self._distance_box(other)
    else:
      point = self.as_vector(other)
      return self._distance_point(point)

  def _distance_point(self, point: np.ndarray) -> float:
    """Returns the signed distance from the point to the box.

       Returns the signed L2 distance to the closest point on the boundary of
       the box.  If the query point is inside the box, returns a negative
       distance.
                                  *5
                   *2            /
                   |            /
                   |           /
              +---------------+
         4    |       |       |
         *----|       |       |        7
              |       |       |--------*
              |     -3*       |
              |          -2*--|
              |     -1*       |
              |       |       |
              +---------------+

    Args:
      point: A point that may lie in or out of the box.

    Returns:
      Signed distance from the point to the box.
    """
    if self.empty:
      return np.inf
    ival_dists = np.array([i.distance(x) for i, x in zip(self, point)])
    max_ival_dist = ival_dists.max()
    if max_ival_dist <= 0:
      return max_ival_dist
    return np.linalg.norm(np.maximum(ival_dists, 0))

  def _distance_box(self, other: 'Box') -> float:
    if self.empty:
      return np.inf
    ival_dists = np.array(
        [i_this.distance(i_other) for i_this, i_other in zip(self, other)]
    )
    max_ival_dist = ival_dists.max()
    if max_ival_dist <= 0:
      return max_ival_dist
    return np.linalg.norm(np.maximum(ival_dists, 0))

  def closest_point(self, point: math_types.VectorType) -> np.ndarray:
    """Returns the closest point in this interval to x."""
    point = self.as_vector(point)
    if self.empty:
      return point
    p = np.zeros(self.dim)
    for dim in range(self.dim):
      i = self[dim]
      p[dim] = i.closest_value(point[dim])
    return p

  def interpolate(self, t: math_types.VectorOrValueType) -> np.ndarray:
    """Returns a value interpolated along the diagonal of the box.

    interpolate(0) = minimum
    interpolate(1) = maximum
    interpolate(0.5) = center

    This function does no checking for finite values and may have overflow or
    other errors if the box is empty or unbounded.

    Args:
      t: Interpolation parameter.

    Returns:
      Interpolated value in the interval.
    """
    t = self.as_vector(t)
    return np.asarray([i.interpolate(u) for i, u in zip(self, t)])

  # --------------------------------------------------------------------------
  # Utility functions
  # --------------------------------------------------------------------------

  def copy(self) -> 'Box':
    return Box(array=self.array)

  def as_vector(self, v: math_types.VectorOrValueType) -> np.ndarray:
    """Returns the vector after validating it has the correct dimensions."""
    if math_types.is_scalar(v):
      return np.full(self.dim, v, dtype=np.float64)
    else:
      return vector_util.as_vector(v, dimension=self.dim, dtype=np.float64)

  def scale_corners(self, scale_factor: float) -> 'Box':
    """Scales the corners of the box by the scale factor.

    A negative value will invert the box to keep it non-empty.

    Example:
      [0,1] x [2,3] x [4,5] * 2 = [0,2] x [4,6] x [8,10]
      [0,1] x [2,3] x [4,5] * -2 = [-2,0] x [-6,-4] x [-10,-8]

    Args:
      scale_factor: Scale factor for box corners.

    Returns:
      The scaled box.
    """
    if self.empty:
      return self
    scale_factor = self.as_vector(scale_factor)
    return Box.from_intervals(
        [ival.scale(f) for ival, f in zip(self.intervals(), scale_factor)]
    )

  def scale_size(self, scale_factor: math_types.VectorOrValueType) -> 'Box':
    """Returns a box that is a uniform scaling of this box about its center.

    The center of the box will be at the same location after scaling.
    The size vector of the box will be scaled by the factor.
    If non-uniform scaling is specified, each component of size will be scaled
      by the corresponding factor in the scale_vector.

    Args:
      scale_factor: Non-negative scale factor, or vector of scale factors, for
        box dimensions.

    Returns:
      The scaled box.

    Raises:
      ValueError: If scale factor is negative.
    """
    if self.empty:
      return self
    scale_factor = self.as_vector(scale_factor)
    return Box.from_intervals(
        [
            ival.scale_length(f)
            for ival, f in zip(self.intervals(), scale_factor)
        ]
    )

  def translate(self, delta: math_types.VectorOrValueType) -> 'Box':
    """Returns a box that is a rigid shift of this box.

    Args:
      delta: Offset scalor or vector that will be added to both corners of the
        box.

    Raises:
      ValueError: If offset vector has different dimensions from this box.

    Returns:
      The box translated by delta.
    """
    if self.empty:
      return self
    delta = self.as_vector(delta)
    return Box(array=self._array + delta)

  def inflate(self, delta: math_types.VectorOrValueType) -> 'Box':
    """Inflates the interval by moving the endpoints outward by delta."""
    if self.empty:
      return self
    delta = self.as_vector(delta)
    return Box._from_corners(self.minimum - delta, self.maximum + delta)

  def _box_proto_type(self) -> BoxProtoType:
    """Returns the appropriate protobuf to represent this Box."""
    proto_for_dim = {
        2: box_pb2.Box2d,
        3: box_pb2.Box3d,
        4: box_pb2.Box4d,
    }
    return proto_for_dim[self.dim]()

  def to_proto(self, proto_out: Optional[BoxProtoType] = None) -> BoxProtoType:
    """Populates a Box protobuf with this box.

    Args:
      proto_out: The output protobuf.  If not specified, create a new one.

    Returns:
      A Box protobuf containing the component values.  Returns the input
      protobuf if specified.
    """
    if proto_out is None:
      proto_out = self._box_proto_type()
    proto_util.vector_to_proto(self.minimum, proto_out.min_corner)
    proto_util.vector_to_proto(self.maximum, proto_out.max_corner)
    return proto_out

  # --------------------------------------------------------------------------
  # Checks
  # --------------------------------------------------------------------------

  def check_non_empty(self, err_msg: Text = '') -> None:
    """Raises a ValueError exception if the box is empty."""
    if self.empty:
      raise ValueError(
          '%s: %s  diagonal=%s  %s'
          % (BOX_EMPTY_MESSAGE, self, self.diagonal, err_msg)
      )

  def _check_array_valid(self, err_msg: Text = '') -> None:
    """Raises a ValueError exception if the box is not well defined."""
    shape = self._array.shape
    if len(shape) != 2 or shape[0] != 2 or shape[1] < 2:
      raise ValueError(
          '%s: %s  shape=%s %s'
          % (BOX_ARRAY_SHAPE_MESSAGE, self._array, self._array.shape, err_msg)
      )
    if np.any(np.isnan(self._array)):
      raise ValueError('%s: %s %s' % (BOX_ARRAY_NAN_MESSAGE, self, err_msg))

  # --------------------------------------------------------------------------
  # Factory functions
  # --------------------------------------------------------------------------

  @classmethod
  def zero(cls, dim: int = 3) -> 'Box':
    """Returns the box containing exactly the origin."""
    return cls(array=np.zeros((2, dim)))

  @classmethod
  def unit(cls, dim: int = 3) -> 'Box':
    """Returns the box containing [0, 1] in every dimension."""
    return cls.from_interval(interval.Interval.unit(), dim)

  @classmethod
  def infinity(cls, dim: int = 3) -> 'Box':
    """Returns the unbounded box that contains all points."""
    return cls.from_interval(interval.Interval.infinity(), dim)

  @classmethod
  def create_empty(cls, dim: int = 3) -> 'Box':
    """Returns a box containing no points."""
    return cls.from_interval(interval.Interval.create_empty(), dim=dim)

  @classmethod
  def from_point(cls, point: math_types.VectorType, delta: float = 0) -> 'Box':
    """Constructs a Box that contains a single point."""
    point = vector_util.as_vector(point)
    return cls._from_corners(point - delta, point + delta)

  @classmethod
  def from_interval(
      cls, ival: Union[interval.Interval, math_types.Vector2Type], dim: int = 3
  ) -> 'Box':
    """Constructs a Box from min and max corners."""
    if not isinstance(ival, interval.Interval):
      ival = interval.Interval(bounds=ival)
    return cls._from_corners(
        np.full(dim, ival.minimum), np.full(dim, ival.maximum)
    )

  @classmethod
  def from_intervals(cls, ivals: Iterable[interval.Interval]) -> 'Box':
    """Constructs a Box from min and max corners."""
    return cls(array=np.stack([ival.bounds for ival in ivals], axis=1))

  @classmethod
  def _from_corners(
      cls, min_corner: np.ndarray, max_corner: np.ndarray
  ) -> 'Box':
    """Constructs a Box from min and max corners assuming they are valid."""
    return cls(array=np.stack((min_corner, max_corner), axis=0))

  @classmethod
  def from_corners(
      cls, min_corner: math_types.VectorType, max_corner: math_types.VectorType
  ) -> 'Box':
    """Constructs a Box from min and max corners.

    Args:
      min_corner: Minimum corner of the box.
      max_corner: Maximum corner of the box.

    Returns:
      A Box defined by the min and max corners.

    Raises:
      ValueError: If corners are defined with different dimensions.
    """
    min_corner = vector_util.as_vector(min_corner, dtype=np.float64)
    max_corner = vector_util.as_vector(max_corner, dtype=np.float64)
    if not np.all(min_corner.shape == max_corner.shape):
      raise ValueError(
          '%s: Box.from_corners(%s, %s)  %s != %s'
          % (
              BOX_INVALID_MESSAGE,
              min_corner,
              max_corner,
              min_corner.shape,
              max_corner.shape,
          )
      )
    return cls._from_corners(min_corner, max_corner)

  @classmethod
  def from_diagonal(cls, diagonal: math_types.VectorType) -> 'Box':
    """Constructs a Box with a given diagonal centered at zero."""
    diagonal = vector_util.as_vector(diagonal, dtype=np.float64)
    max_corner = diagonal * 0.5
    min_corner = -max_corner
    return cls._from_corners(min_corner, max_corner)

  @classmethod
  def from_size(cls, size: float, dim: int = 3) -> 'Box':
    """Constructs a Box with a given side-length centered at the origin."""
    corner = np.full(dim, size * 0.5, dtype=np.float64)
    return cls._from_corners(-corner, corner)

  @classmethod
  def from_proto(cls, box_proto: BoxProtoType) -> 'Box':
    """Constructs a Box from a Box protobuf message.

    Args:
      box_proto: A box protobuf message.

    Returns:
      The Box represented by the protobuf.
    """
    return cls._from_corners(
        proto_util.vector_from_proto(box_proto.min_corner),
        proto_util.vector_from_proto(box_proto.max_corner),
    )
