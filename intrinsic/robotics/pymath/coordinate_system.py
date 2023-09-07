# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Coordinate System Transforms between left and right-handed systems.

go/left-right-coordinates

CoordinateSystem defines the canonical orientation vectors (right, down, and
front) in a local coordinate frame.

Four geometric types can have an associated coordinate frame:

  Vector3
  Quaternion
  Rotation3
  Pose3

The canonical frame is the RDF (Right-Down-Front) frame.  Each object has
functions that convert to and from the RDF frame.

  to_rdf - Returns the object in the RDF frame.

  from_rdf - Constructs an object from a frame and an RDF representation.

  to_frame - Returns the object converted to a new frame.

This library and its test can be used to determine and validate conversions
between two coordinate frames.

---------------------------------------------------------------------

Example:

Bullet/ROS: right-handed, up=z, front=x
Unit: left-handed, up=y, front=z

When we construct these two CoordinateSystems and log their properties, we get:

Bullet
  handed  RIGHT
  right   V.Bullet([ 0 -1  0])
  down    V.Bullet([ 0  0 -1])
  front   V.Bullet([ 1  0  0])
  left    V.Bullet([ 0  1  0])
  up      V.Bullet([ 0  0  1])
  back    V.Bullet([-1  0  0])
  local <- RDF
[[ 0.  0  1]
 [-1  0  0]
 [ 0 -1  0]]
  RDF <- local
[[ 0 -1  0]
 [ 0  0 -1]
 [ 1  0  0]]

Unity
  handed  LEFT
  right   V.Unity([ 1  0  0])
  down    V.Unity([ 0 -1  0])
  front   V.Unity([ 0  0  1])
  left    V.Unity([-1  0  0])
  up      V.Unity([ 0  1  0])
  back    V.Unity([ 0  0 -1])
  local <- RDF
[[ 1  0  0]
 [ 0 -1  0]
 [ 0  0  1]]
  RDF <- local
[[ 1  0  0]
 [ 0 -1  0]
 [ 0  0  1]]


A point in Bullet can be converted into a point in Unity by applying this
transform:

Unity_pose_Bullet = Unity.local_RDF * Bullet.RDF_local -

  [[ 0 -1  0]
   [ 0  0  1]
   [ 1  0  0]]

  Unity point = (-Bullet.y, Bullet.z, Bullet.x)

Bullet_pose_Unity = Bullet.local_RDF * Unit.RDF_local -

  [[ 0  0  1]
   [-1  0  0]
   [ 0  1  0]]

  Bullet point = (Unity.z, -Unity.x, Unity.y)

Because Unity is left-handed and Bullet is right-handed, this matrix is not a
rotation.  Its determinant is -1 and it contains a mirror.

---------------------------------------------------------------------

Rotations

Extra care must be taken when converting between right-handed and left-handed
rotations.  Check the results in both directions.

  Are rotation angles clockwise or counter-clockwise?

  Is the quaternion multiplication right-handed or left-handed?

  Is quaternion rotation performed as qpq-1 or q-1pq?

  If an Euler angle representation is used, are Euler angles specified along the
  same axes in the same order?
"""

import math
from typing import Optional
from typing import Text
from typing import Union
from absl import logging
from intrinsic.robotics.pymath import math_types
from intrinsic.robotics.pymath import quaternion
from intrinsic.robotics.pymath import vector_util
import numpy as np


def _cos_sin_half_angle(radians: float = 0, degrees: Optional[float] = None):
  """Returns the cosine and sine of the half-angle."""
  if degrees is not None:
    radians = np.radians(degrees)
  radians /= 2
  return math.cos(radians), math.sin(radians)


class CoordinateSystem(object):
  """CoordinateSystem class.

  Describes a 3D coordinate frame in terms of orientation vectors and left or
  right handedness.

  Attributes: name right_handed left_handed
  Vectors: zero x y z up down front back right left
  Quaternions: one i j k
  Transformations:
    rdf_from_local: Converts a point in this coordinate frame into the canonical
    RDF coordinate frame.
    local_from_rdf: Converts a point in the canonical RDF coordinate frame into
    this coordinate frame.
  """

  def __init__(
      self,
      name: Text,
      up_direction: math_types.VectorType,
      front_direction: math_types.VectorType,
      right_handed: bool = True,
  ):
    """Constructs a named coordinate frame from orientation vectors.

    Expects exact arithmetic.  Up and Front ectors should be precisely
    orthonormal.

    Args:
      name: Name of the system, e.g. 'Unity'
      up_direction: Direction of up-vector as array.
      front_direction: Direction of front-vector as array.
      right_handed: Indicates right-handed or left-handed system.
    """
    self._name = name
    self._right_handed = right_handed
    up = vector_util.as_vector3(up_direction)
    front = vector_util.as_vector3(front_direction)
    assert up.dot(up) == 1
    assert front.dot(front) == 1
    assert up.dot(front) == 0
    right = vector_util.as_vector3(np.cross(front, up))
    if self.left_handed:
      right = -right
    assert right.dot(right) == 1
    assert up.dot(right) == 0
    assert front.dot(right) == 0
    self._up = Vector3(self, xyz=up)
    self._front = Vector3(self, xyz=front)
    self._right = Vector3(self, xyz=right)
    self._rdf_local = np.vstack((self.right.xyz, self.down.xyz, self.front.xyz))
    self._local_rdf = self._rdf_local.transpose()

  @property
  def name(self):
    return self._name

  @property
  def right_handed(self):
    return self._right_handed

  @property
  def left_handed(self):
    return not self.right_handed

  # ======================================================================
  # Canonical vectors
  # ======================================================================

  @property
  def zero(self) -> 'Vector3':
    return Vector3(self)

  @property
  def x(self) -> 'Vector3':
    return Vector3(self, x=1)

  @property
  def y(self) -> 'Vector3':
    return Vector3(self, y=1)

  @property
  def z(self) -> 'Vector3':
    return Vector3(self, z=1)

  # ======================================================================
  # Orientation vectors
  # ======================================================================

  @property
  def up(self) -> 'Vector3':
    return self._up

  @property
  def down(self) -> 'Vector3':
    return -self.up

  @property
  def front(self) -> 'Vector3':
    return self._front

  @property
  def back(self) -> 'Vector3':
    return -self.front

  @property
  def right(self) -> 'Vector3':
    return self._right

  @property
  def left(self) -> 'Vector3':
    return -self.right

  # ======================================================================
  # Canonical quaternions
  # ======================================================================

  @property
  def one(self) -> 'Quaternion':
    return Quaternion.one(self)

  @property
  def i(self) -> 'Quaternion':
    return Quaternion.i(self)

  @property
  def j(self) -> 'Quaternion':
    return Quaternion.j(self)

  @property
  def k(self) -> 'Quaternion':
    return Quaternion.k(self)

  # ======================================================================
  # Conversion between frame and RDF coordinates.
  # ======================================================================

  def rdf_from_local(self, xyz: np.ndarray) -> np.ndarray:
    """Transforms a point from this frame into the canonical RDF frame."""
    return np.matmul(self._rdf_local, xyz)

  def local_from_rdf(self, rdf: np.ndarray) -> np.ndarray:
    """Converts a point from the canonical RDF frame into this frame."""
    return np.matmul(self._local_rdf, rdf)

  def __str__(self) -> Text:
    return self.name

  def __repr__(self) -> Text:
    return self.name

  def log(self) -> None:
    logging.info(
        '%s\n  handed  %s\n  right   %s\n  down    %s\n  front   %s\n'
        '  left    %s\n  up      %s\n  back    %s\n'
        '  local <- RDF\n%s\n  RDF <- local\n%s',
        self,
        ('RIGHT' if self.right_handed else 'LEFT'),
        self.right,
        self.down,
        self.front,
        self.left,
        self.up,
        self.back,
        self._local_rdf,
        self._rdf_local,
    )

  @classmethod
  def init_rdf(cls) -> 'CoordinateSystem':
    return cls(
        name='RDF',
        right_handed=True,
        up_direction=[0, -1, 0],
        front_direction=[0, 0, 1],
    )


AnyGeometry = Union['Geometry', 'Vector3', 'Quaternion', 'Rotation3', 'Pose3']


class Geometry(object):
  """Base class for a geometric object with an assigned coordinate frame.

  Properties:
    frame: Assigned coordinate frame.
    is_rdf_frame: True if the frame is the canonical RDF coordinate frame.
  """

  def __init__(self, frame: CoordinateSystem):
    self._frame = frame

  @property
  def frame(self) -> CoordinateSystem:
    return self._frame

  def assert_same_frame(self, g: 'Geometry') -> None:
    """Raises an error of the two objects have different frames."""
    if self.frame != g.frame:
      raise ValueError(
          'Geometric objects have different coordinate systems: \n  %s\n  %s'
          % (self, g)
      )

  def to_frame(self, frame: CoordinateSystem) -> AnyGeometry:
    """Returns this object transformed to the target frame."""
    if self.frame == frame:
      return self
    return self.__class__.from_rdf(frame, self.to_rdf())

  def to_rdf(self) -> AnyGeometry:
    self.assert_same_frame(Geometry(RDF))
    return self

  @classmethod
  def from_rdf(cls, frame: CoordinateSystem, rdf: 'Geometry') -> AnyGeometry:
    rdf.assert_same_frame(Geometry(frame))
    return rdf


class Vector3(Geometry):
  """Three-dimensional vector with a specified coordinate system."""

  def __init__(
      self,
      frame: CoordinateSystem,
      x=0,
      y=0,
      z=0,
      xyz: Optional[math_types.VectorType] = None,
      normalize: bool = False,
  ):
    super(Vector3, self).__init__(frame)
    if xyz is not None:
      x, y, z = xyz
    self._xyz = np.array([x, y, z], dtype=np.float64)
    if normalize:
      self.normalize()

  @property
  def xyz(self) -> np.ndarray:
    """Returns (x,y,z) components of the vector as a NumPy array."""
    return self._xyz

  @property
  def x(self) -> float:
    """Returns the x component of the vector."""
    return self.xyz[0]

  @property
  def y(self) -> float:
    """Returns the y component of the vector."""
    return self.xyz[1]

  @property
  def z(self) -> float:
    """Returns the z component of the vector."""
    return self.xyz[2]

  def __eq__(self, v: 'Vector3') -> bool:
    self.assert_same_frame(v)
    return (self.xyz == v.xyz).all()

  def __ne__(self, v: 'Vector3') -> bool:
    return not self == v

  def __neg__(self) -> 'Vector3':
    return Vector3(self.frame, xyz=-self.xyz)

  def __add__(self, v: 'Vector3') -> 'Vector3':
    self.assert_same_frame(v)
    return Vector3(self.frame, xyz=self.xyz + v.xyz)

  def __sub__(self, v: 'Vector3') -> 'Vector3':
    self.assert_same_frame(v)
    return Vector3(self.frame, xyz=self.xyz - v.xyz)

  def __mul__(self, c: float) -> 'Vector3':
    return Vector3(self.frame, xyz=self.xyz * c)

  def __truediv__(self, c: float) -> 'Vector3':
    return Vector3(self.frame, xyz=self.xyz / c)

  def __abs__(self) -> float:
    """Returns the magnitude (L2 norm) of the vector."""
    return np.linalg.norm(self.xyz)

  def __str__(self) -> Text:
    return 'V.%s(%s)' % (self.frame.name, self.xyz)

  def __repr__(self) -> Text:
    return 'V.%s([%r, %r, %r])' % (self.frame.name, self.x, self.y, self.z)

  def normalize(self) -> None:
    """Normalizes the vector in place."""
    self /= abs(self)

  def normalized(self) -> 'Vector3':
    """Returns a Normalized copy of the vector."""
    return self / abs(self)

  # ----------------------------------------------------------------------
  # Conversion between different frames

  def to_rdf(self) -> 'Vector3':
    """Returns this vector transformed to the canonical RDF frame."""
    return Vector3(frame=RDF, xyz=self.frame.rdf_from_local(self.xyz))

  @classmethod
  def from_rdf(
      cls, frame: CoordinateSystem, vector_rdf: 'Vector3'
  ) -> 'Vector3':
    """Returns the vector transformed from the canonical RDF frame."""
    assert vector_rdf.frame == RDF
    return cls(frame=frame, xyz=frame.local_from_rdf(rdf=vector_rdf.xyz))


class Quaternion(Geometry):
  """Quaternion with a specified CoordinateSystem.

  Attributes:  quat  right_handed  real  imag  x  y  z  w

  Operators: eq ne neg add sub mul truediv abs str repr

  Factory functions: one i j k zero from_xyzw from_real_imaginary
  """

  def __init__(
      self,
      frame: CoordinateSystem,
      q: quaternion.Quaternion = quaternion.Quaternion.one(),
  ):
    super(Quaternion, self).__init__(frame)
    self._quat = q

  @property
  def quat(self) -> quaternion.Quaternion:
    """Returns the base quaternion object."""
    return self._quat

  @property
  def right_handed(self) -> bool:
    """Returns true if multiplication is right-handed (i * j = k)."""
    return self.frame.right_handed

  @property
  def real(self) -> float:
    """Returns the real part of the quaternion."""
    return self.quat.real

  @property
  def imag(self) -> Vector3:
    """Returns the imaginary components of the quaternion as a Vector3."""
    return Vector3(self.frame, xyz=self.quat.imag)

  @property
  def x(self) -> float:
    """Returns the coefficient of the i quaternion."""
    return self.quat.x

  @property
  def y(self) -> float:
    """Returns the coefficient of the j quaternion."""
    return self.quat.y

  @property
  def z(self) -> float:
    """Returns the coefficient of the k quaternion."""
    return self.quat.z

  @property
  def w(self) -> float:
    """Returns the coefficient of the real part of the quaternion."""
    return self.quat.w

  def __eq__(self, q: 'Quaternion') -> bool:
    self.assert_same_frame(q)
    return self.quat == q.quat

  def __ne__(self, q: 'Quaternion') -> bool:
    return not self == q

  def __neg__(self) -> 'Quaternion':
    return Quaternion(self.frame, q=-self.quat)

  def __add__(self, q: 'Quaternion') -> 'Quaternion':
    """Returns the component-wise sum of the two quaternions."""
    self.assert_same_frame(q)
    return Quaternion(self.frame, q=self.quat + q.quat)

  def __sub__(self, q: 'Quaternion') -> 'Quaternion':
    """Returns the component-wise difference of the two quaternions."""
    self.assert_same_frame(q)
    return Quaternion(self.frame, q=self.quat - q.quat)

  def __mul__(self, q: Union['Quaternion', float, int]) -> 'Quaternion':
    """Returns the quaternion product of the two quaternions."""
    if not isinstance(q, Quaternion):
      q = Quaternion(self.frame, q=quaternion.Quaternion(xyzw=[0, 0, 0, q]))

    self.assert_same_frame(q)
    if self.right_handed:
      return Quaternion(self.frame, q=self.quat * q.quat)
    else:
      return Quaternion(self.frame, q=q.quat * self.quat)

  def __truediv__(self, q: Union['Quaternion', float, int]) -> 'Quaternion':
    """Returns the quaternion quotient of the two quaternions."""
    if isinstance(q, Quaternion):
      self.assert_same_frame(q)
    return Quaternion(self.frame, self.quat / q)

  def __abs__(self) -> float:
    """Returns the magnitude of the quaternion."""
    return np.linalg.norm(self.quat.xyzw)

  def __str__(self) -> Text:
    return 'Q.%s(%s)' % (self.frame.name, self.quat)

  def __repr__(self) -> Text:
    return 'Q.%s([%r, %r, %r, %r])' % (
        self.frame.name,
        self.x,
        self.y,
        self.z,
        self.w,
    )

  def inverse(self) -> 'Quaternion':
    """Returns the multiplicative inverse of the quaternion."""
    return Quaternion(self.frame, q=self.quat.inverse())

  def normalize(self) -> None:
    """Normalizes the quaternion in place."""
    self /= abs(self)

  def normalized(self) -> 'Quaternion':
    """Returns a Normalized copy of the quaternion."""
    return self / abs(self)

  @classmethod
  def one(cls, frame: CoordinateSystem) -> 'Quaternion':
    """Constructs the one quaternion: (0i + 0j + 0k + 1)."""
    return cls(frame=frame, q=quaternion.Quaternion.one())

  @classmethod
  def i(cls, frame: CoordinateSystem) -> 'Quaternion':
    """Constructs the i quaternion: (i + 0j + 0k + 0)."""
    return cls(frame=frame, q=quaternion.Quaternion.i())

  @classmethod
  def j(cls, frame: CoordinateSystem) -> 'Quaternion':
    """Constructs the j quaternion: (0i + j + 0k + 0)."""
    return cls(frame=frame, q=quaternion.Quaternion.j())

  @classmethod
  def k(cls, frame: CoordinateSystem) -> 'Quaternion':
    """Constructs the k quaternion: (0i + 0j + k + 0)."""
    return cls(frame=frame, q=quaternion.Quaternion.k())

  @classmethod
  def zero(cls, frame: CoordinateSystem) -> 'Quaternion':
    """Constructs the zero quaternion: (0i + 0j + 0k + 0).

    This quaternion cannot be normalized and does not correspond to a rotation.

    Args:
      frame: Coordinate frame of the quaternion.

    Returns:
      The zero quaternion.
    """
    return cls(frame=frame, q=quaternion.Quaternion(xyzw=[0, 0, 0, 0]))

  @classmethod
  def from_xyzw(
      cls,
      frame: CoordinateSystem,
      xyzw: Optional[math_types.VectorType] = None,
      normalize: bool = False,
  ) -> 'Quaternion':
    """Constructs a quaternion from xyzw components in an array."""
    return cls(
        frame=frame, q=quaternion.Quaternion(xyzw=xyzw, normalize=normalize)
    )

  @classmethod
  def from_real_imaginary(cls, real: float, imaginary: Vector3) -> 'Quaternion':
    """Constructs a quaternion from a real and imaginary components.

    The imaginary component vector contains the coordinate frame reference.

    Args:
      real: Real component of quaternion.
      imaginary: Imaginary components of quaternion with coordinate system.

    Returns:
      The quaternion, <real,imaginary> in the given coordinate system.
    """
    return cls(
        frame=imaginary.frame,
        q=quaternion.Quaternion.from_real_imaginary(real, imaginary.xyz),
    )

  # ----------------------------------------------------------------------
  # Conversion between different frames
  def to_rdf(self) -> 'Quaternion':
    """Returns this quaternion transformed to the canonical RDF frame."""
    return Quaternion.from_real_imaginary(
        real=self.real, imaginary=self.imag.to_rdf()
    )

  @classmethod
  def from_rdf(
      cls, frame: CoordinateSystem, quaternion_rdf: 'Quaternion'
  ) -> 'Quaternion':
    """Returns the quaternion transformed from the canonical RDF frame."""
    assert quaternion_rdf.frame == RDF
    return cls.from_real_imaginary(
        real=quaternion_rdf.real,
        imaginary=Vector3.from_rdf(frame=frame, vector_rdf=quaternion_rdf.imag),
    )


class Rotation3(Geometry):
  """Three-dimensional rotation with a specified CoordinateSystem."""

  def __init__(self, q: Quaternion, normalize: bool = False):
    super(Rotation3, self).__init__(q.frame)
    self._quat = q
    # Assert that the quaternion can be normalized.

    # Rotation uses the inverse, not the conjugate, of the quaternion, so the
    # quaternion does not have to be maintained with length.
    assert abs(q) > 1e-6
    if normalize:
      self._quat.normalize()

  @property
  def quat(self) -> Quaternion:
    return self._quat

  @property
  def frame(self) -> CoordinateSystem:
    return self.quat.frame

  def __eq__(self, r: 'Rotation3') -> bool:
    return self.quat == r.quat or self.quat == -r.quat or abs(self - r) == 0

  def __ne__(self, r: 'Rotation3') -> bool:
    return not self == r

  def __mul__(self, r: 'Rotation3') -> 'Rotation3':
    """Returns the composition of the two rotations."""
    return Rotation3(q=self.quat * r.quat)

  def __truediv__(self, r: 'Rotation3') -> 'Rotation3':
    return self * r.inverse()

  def __sub__(self, r: 'Rotation3') -> 'Rotation3':
    """Used only for assertAlmostEqual.

    Rotations form a group under composition.  Subtraction in the group
    operation is equivalent to division.

    Args:
      r: Another rotation

    Returns:
      The quotient self/r.
    """
    return self / r

  def __abs__(self) -> float:
    """Used only for assertAlmostEqual.

    The magnitude of the imaginary vector is equal to sin(angle/2), so an
    identity rotation has magnitude zero.

    This norm satisfies the triangle inequality: |AB| <= |A| + |B|

    Returns:
      Magnitude of quaternion imaginary components = sin(angle/2).
    """
    return abs(self.quat.imag) / abs(self.quat)

  def __str__(self) -> Text:
    return 'R(%s)' % self.quat

  def __repr__(self) -> Text:
    return 'R(%r)' % self.quat

  def inverse(self) -> 'Rotation3':
    return Rotation3(self.quat.inverse())

  def rotate_vector(self, v: Vector3) -> Vector3:
    self.quat.assert_same_frame(v)
    q_v = Quaternion.from_real_imaginary(real=0, imaginary=v)
    q_v_rotated = self.quat * q_v * self.quat.inverse()
    return q_v_rotated.imag

  @classmethod
  def identity(cls, frame: CoordinateSystem) -> 'Rotation3':
    return cls(q=Quaternion.one(frame=frame))

  @classmethod
  def rx180(cls, frame: CoordinateSystem) -> 'Rotation3':
    return cls(q=Quaternion.i(frame=frame))

  @classmethod
  def ry180(cls, frame: CoordinateSystem) -> 'Rotation3':
    return cls(q=Quaternion.j(frame=frame))

  @classmethod
  def rz180(cls, frame: CoordinateSystem) -> 'Rotation3':
    return cls(q=Quaternion.k(frame=frame))

  @classmethod
  def x_rotation(
      cls,
      frame: CoordinateSystem,
      radians: float = 0,
      degrees: Optional[float] = None,
  ) -> 'Rotation3':
    cos, sin = _cos_sin_half_angle(radians, degrees)
    return cls(q=Quaternion.from_xyzw(frame, [sin, 0, 0, cos]))

  @classmethod
  def y_rotation(
      cls,
      frame: CoordinateSystem,
      radians: float = 0,
      degrees: Optional[float] = None,
  ) -> 'Rotation3':
    cos, sin = _cos_sin_half_angle(radians, degrees)
    return cls(q=Quaternion.from_xyzw(frame, [0, sin, 0, cos]))

  @classmethod
  def z_rotation(
      cls,
      frame: CoordinateSystem,
      radians: float = 0,
      degrees: Optional[float] = None,
  ) -> 'Rotation3':
    cos, sin = _cos_sin_half_angle(radians, degrees)
    return cls(q=Quaternion.from_xyzw(frame, [0, 0, sin, cos]))

  @classmethod
  def axis_angle(
      cls, axis: Vector3, radians: float = 0, degrees: Optional[float] = None
  ) -> 'Rotation3':
    """Returns a rotation about the given axis by the given clockwise angle."""
    cos, sin = _cos_sin_half_angle(radians, degrees)
    xyzw = np.zeros(4)
    xyzw[:3] = axis.normalized().xyz
    xyzw[:3] *= sin
    xyzw[3] = cos
    return cls(q=Quaternion.from_xyzw(axis.frame, xyzw), normalize=False)

  # ----------------------------------------------------------------------
  # Conversion between different frames
  def to_rdf(self) -> 'Rotation3':
    return Rotation3(q=self.quat.to_rdf())

  @classmethod
  def from_rdf(
      cls, frame: CoordinateSystem, rotation_rdf: 'Rotation3'
  ) -> 'Rotation3':
    assert rotation_rdf.quat.frame == RDF
    return cls(
        q=Quaternion.from_rdf(frame=frame, quaternion_rdf=rotation_rdf.quat)
    )


class Pose3(Geometry):
  """Three-dimensional pose with a specified CoordinateSystem.

  Attributes: rotation translation
  """

  def __init__(self, rotation: Rotation3, translation: Vector3):
    super(Pose3, self).__init__(rotation.frame)
    self._rotation = rotation
    self._translation = translation
    self.assert_same_frame(rotation)

  @property
  def rotation(self) -> Rotation3:
    return self._rotation

  @property
  def translation(self) -> Vector3:
    return self._translation

  @property
  def frame(self) -> CoordinateSystem:
    return self.translation.frame

  def __eq__(self, p: 'Pose3') -> bool:
    return self.rotation == p.rotation and self.translation == p.translation

  def __ne__(self, p: 'Pose3') -> bool:
    return not self == p

  def __mul__(self, p: 'Pose3') -> 'Pose3':
    """Returns the composition of the two transforms.

    (A * B)(p) = A(B(p))

    Args:
      p: The right-hand operand.

    Returns:
      self * p
    """
    return Pose3(
        rotation=self.rotation * p.rotation,
        translation=self.transform_point(p.translation),
    )

  def __truediv__(self, p: 'Pose3') -> 'Pose3':
    """Returns A * B-1.

    (A / B)(p) = A(B-1(p))

    Args:
      p: The right-hand operand.

    Returns:
      self * p-1
    """
    return self * p.inverse()

  def __sub__(self, p: 'Pose3') -> 'Pose3':
    """Returns a differential pose.

    Used only for assertAlmostEqual.

    Args:
      p: The right-hand operand.

    Returns:
      Difference between poses.
    """
    return Pose3(self.rotation - p.rotation, self.translation - p.translation)

  def __abs__(self) -> float:
    """Returns abs(rotation) + abs(translation).

    Used only for assertAlmostEqual.

    Returns:
      |self| The magnitude of the change represented by the pose.
    """
    return abs(self.translation) + abs(self.rotation)

  def __str__(self) -> Text:
    return 'P(%s, %s)' % (self.rotation, self.translation)

  def __repr__(self) -> Text:
    return 'P(%r, %r)' % (self.rotation, self.translation)

  def inverse(self) -> 'Pose3':
    """Returns the inverse transform.

    T-1(T(p)) = T(T-1(p)) = p

    Returns:
      self-1: The inverse of the pose.
    """
    rotation_inv = self.rotation.inverse()
    return Pose3(
        rotation=rotation_inv,
        translation=-rotation_inv.rotate_vector(self.translation),
    )

  def transform_point(self, point: Vector3) -> Vector3:
    """Transforms the point by the pose.

    T(p) = R p + v

    Args:
      point: Operand of the transform.

    Returns:
      The point transformed by this pose.
    """
    return self.rotation.rotate_vector(point) + self.translation

  @classmethod
  def identity(cls, frame: CoordinateSystem) -> 'Pose3':
    return cls(
        rotation=Rotation3.identity(frame=frame),
        translation=Vector3(frame=frame),
    )

  @classmethod
  def from_rotation(cls, rotation: Rotation3) -> 'Pose3':
    return cls(rotation=rotation, translation=Vector3(rotation.frame))

  @classmethod
  def from_translation(cls, translation: Vector3) -> 'Pose3':
    return cls(
        rotation=Rotation3.identity(translation.frame), translation=translation
    )

  # ----------------------------------------------------------------------
  # Conversion between different frames

  def to_rdf(self) -> 'Pose3':
    return Pose3(self.rotation.to_rdf(), self.translation.to_rdf())

  @classmethod
  def from_rdf(cls, frame: CoordinateSystem, pose_rdf: 'Pose3') -> 'Pose3':
    assert pose_rdf.frame == RDF
    return cls(
        Rotation3.from_rdf(frame=frame, rotation_rdf=pose_rdf.rotation),
        Vector3.from_rdf(frame=frame, vector_rdf=pose_rdf.translation),
    )


RDF = CoordinateSystem.init_rdf()
