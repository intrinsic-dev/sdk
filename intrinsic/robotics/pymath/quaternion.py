# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Quaternion class (python3).

This library implements a Quaternion class that is intended to be used
primarily for performing 3D rotations.

go/quaternion-rotation - Quaternion definitions and derivations, including
  rotation matrix conversions.

go/robotics-math - Robotics math libraries.

go/quaternions - Quaternions at Google - Describes quaternion libraries in
  various languages and the different conventions for representation, naming,
  and computation.
"""

from typing import Optional, Text, Union

from intrinsic.robotics.messages import quaternion_pb2
from intrinsic.robotics.pymath import math_types
from intrinsic.robotics.pymath import vector_util
import numpy as np

# ----------------------------------------------------------------------------
# Pytype definitions.
QuaternionOrScalarType = Union['Quaternion', float, int]

# ----------------------------------------------------------------------------
# Constants
QUATERNION_NORM_EPSILON = vector_util.DEFAULT_NORM_EPSILON
QUATERNION_ZERO_EPSILON = vector_util.DEFAULT_ZERO_EPSILON

# ----------------------------------------------------------------------------
# Error messages for exceptions.
QUATERNION_INVALID_MESSAGE = (
    'Quaternion component vector should have four values'
)
QUATERNION_ZERO_MESSAGE = 'Quaternion has zero magnitude'
QUATERNION_NOT_NORMALIZED_MESSAGE = 'Quaternion is not normalized'

# ----------------------------------------------------------------------------
# Constants for efficient quaternion multiplication.
#
# These arrays are used to construct the matrix that performs
# left-multiplication by a quaternion, which can be used for an efficient
# quaternion product computation in numpy. (See go/quaternion-rotation for
# a deeper explanation.)
#
# left_matrix = xyzw[_QUATERNION_MULTIPLICATION_INDICES] *
#               _QUATERNION_LEFT_MULTIPLICATION_SCALE_FACTORS
#
# Let q be a quaternion, q = (ci*i + cj*j + ck*k + c1)
#
# Lq is the matrix that computes left-multiplication by q as a linear operation
# on quaternion components.
#
# Lq = |  c1  -ck   cj   ci |
#      |  ck   c1  -ci   cj |
#      | -cj   ci   c1   ck |
#      | -ci  -cj  -ck   c1 |
#
# Let p be another quaternion, p = (ai*i + aj*j + ak*k + a1)
#
# The product of q and p will be
#
#   q * p = (ci*i + cj*j + ck*k + c1) * (ai*i + aj*j + ak*k + a1)
#
# Lq * p = |  c1  -ck   cj   ci | |ai|
#          |  ck   c1  -ci   cj | |aj|
#          | -cj   ci   c1   ck | |ak|
#          | -ci  -cj  -ck   c1 | |a1|
#
#       = ( c1*ai - ck*aj + cj*ak + ci*a1) i +
#         ( ck*ai + c1*aj - ci*ak + cj*a1) j +
#         (-cj*ai + ci*aj + c1*ak + ck*a1) k +
#         (-ci*ai - cj*aj - ck*ak + c1*a1)
#
_QUATERNION_MULTIPLICATION_INDICES = np.array(
    [[3, 2, 1, 0], [2, 3, 0, 1], [1, 0, 3, 2], [0, 1, 2, 3]]
)
_QUATERNION_LEFT_MULTIPLICATION_SCALE_FACTORS = np.array(
    [[1, -1, 1, 1], [1, 1, -1, 1], [-1, 1, 1, 1], [-1, -1, -1, 1]],
    dtype=np.float64,
)
_QUATERNION_RIGHT_MULTIPLICATION_SCALE_FACTORS = np.array(
    [[1, 1, -1, 1], [-1, 1, 1, 1], [1, -1, 1, 1], [-1, -1, -1, 1]],
    dtype=np.float64,
)

# ----------------------------------------------------------------------------
# Numpy constant matrix for computing the conjugate.
_QUATERNION_CONJUGATE_SCALE_FACTORS = np.array(
    [-1, -1, -1, 1], dtype=np.float64
)


class Quaternion(object):
  """A quaternion represented as an array of four values [x,y,z,w].

  This class defines standard Hamiltonian quaternions.
  The matrix convention is for column vector multiplication.

  A quaternion is a number with three imaginary components, i, j, and k and one
  real component.

      q = x i + y j + z k + w

  We represent the quaternion with the vector [x, y, z, w].

  Attributes:
    _xyzw: [x, y, z, w], the quaternion representation in a numpy array.

  Properties:
    xyzw: All coefficients as a numpy array.
    x: Coefficient of imaginary component i.
    y: Coefficient of imaginary component j.
    z: Coefficient of imaginary component k.
    w: Real component of quaternion.
    real: Real component of quaternion.
    imag: Three imaginary components of quaternion, [x, y, z], as a numpy array.
    conjugate: Conjugate of the quaternion, -xi - yj - zk + w.
  Factory functions:
    one: Returns the multiplicative identity, 1.0.
    zero: Returns the additive identity, 0.0.
    i: Returns the unit quaternion, i.
    j: Returns the unit quaternion, j.
    k: Returns the unit quaternion, k.
  """

  def __init__(
      self,
      xyzw: Optional[math_types.VectorType] = None,
      normalize: bool = False,
  ):
    """Initializes the quaternion with the xyzw component values.

    Sets the components to the values xyzw.

    If no components are given, the default is the zero quaternion.  The zero
    quaternion does not represent any rotation.

    If normalize is True, the quaternion will be scaled by 1/norm to give it a
    magnitude of 1.0.  This will result in an exception if the quaternion is
    close to zero.

    Quaternion.one() returns the multiplicative identity.

    Args:
      xyzw: Quaternion component values in a vector.
      normalize: Indicates whether to normalize the quaternion.

    Raises:
      ValueError: If xyzw has wrong shape or if normalization fails.
    """
    if xyzw is None:
      xyzw = (0, 0, 0, 0)
    self._xyzw = vector_util.as_finite_vector(
        xyzw,
        dimension=4,
        normalize=normalize,
        dtype=np.float64,
        err_msg='Quaternion.__init__',
    ).copy()

  # --------------------------------------------------------------------------
  # Properties
  # --------------------------------------------------------------------------

  @property
  def xyzw(self) -> np.ndarray:
    """Returns the x, y, z, w component values of the quaternion.

    Returns:
      The xyzw coefficients of the quaternion as a numpy array.
    """
    return self._xyzw.copy()

  @property
  def x(self) -> float:
    """Returns x component of quaternion."""
    return self._xyzw[0]

  @property
  def y(self) -> float:
    """Returns y component of quaternion."""
    return self._xyzw[1]

  @property
  def z(self) -> float:
    """Returns z component of quaternion."""
    return self._xyzw[2]

  @property
  def w(self) -> float:
    """Returns w component of quaternion."""
    return self._xyzw[3]

  @property
  def real(self) -> float:
    """Returns real component of quaternion."""
    return self._xyzw[3]

  @property
  def imag(self) -> np.ndarray:
    """Returns imaginary components of quaternion."""
    return self._xyzw[:3].copy()

  @property
  def conjugate(self) -> 'Quaternion':
    """Returns the complex conjugate of the quaternion."""
    return self._get_conjugate()

  # --------------------------------------------------------------------------
  # Property implementation functions
  # --------------------------------------------------------------------------

  def _get_conjugate(self) -> 'Quaternion':
    """Returns the complex conjugate of the quaternion.

    The conjugate of a quaternion is the same quaternion with the three
    imaginary components negated:

      q' = -qx i + -qy j + -qz k + qw

      q * q' = |q|^2, so if |q| = 1, then q' = q^-1

    Returns:
      The complex conjugate of the quaternion.
    """
    return Quaternion(xyzw=self._xyzw * _QUATERNION_CONJUGATE_SCALE_FACTORS)

  # --------------------------------------------------------------------------
  # Utility functions
  # --------------------------------------------------------------------------

  def norm(self) -> float:
    """Returns the magnitude of the quaternion."""
    return np.linalg.norm(self._xyzw)

  def norm_squared(self) -> float:
    """Returns the squared magnitude of the quaternion."""
    return np.inner(self._xyzw, self._xyzw)

  def is_normalized(
      self, norm_epsilon: float = QUATERNION_NORM_EPSILON
  ) -> bool:
    """Returns True if the quaternion is normalized within norm_epsilon.

    Returns True if abs(1 - |q|) <= norm_epsilon

    Args:
      norm_epsilon: Error tolerance on magnitude.

    Returns:
      True if the quaternion has magnitude close to 1.0.
    """
    return vector_util.is_vector_normalized(
        self._xyzw, norm_epsilon=norm_epsilon
    )

  def inverse(self) -> 'Quaternion':
    """Returns the multiplicative inverse of a non-zero quaternion.

    q * q.inverse() = q.inverse() * q = 1

    Returns:
      Inverse of the quaternion.

    Raises:
      ValueError: If the other quaternion cannot be inverted, i.e. |q| == 0.
    """
    norm_squared = self.norm_squared()
    if norm_squared <= QUATERNION_ZERO_EPSILON**2:
      raise ValueError(
          self._zero_magnitude_message(
              norm_epsilon=QUATERNION_ZERO_EPSILON, err_msg='cannot be inverted'
          )
      )
    return self.conjugate / norm_squared

  def left_multiplication_matrix(self) -> np.ndarray:
    """Returns the matrix that computes left multiplication.

    Multiplication by a quaternion is a linear operation.  This function
    computes the matrix that performs the linear operation of
    left-multiplication by this quaternion.

     Lq = |  w  -z   y   x |
          |  z   w  -x   y |
          | -y   x   w   z |
          | -x  -y  -z   w |

    If p = [ai + bj + ck + d], the product (q * p) can be computed by taking the
    matrix product of Lq with the column vector containing the components of p:

      Lq * | a |  ==  q * p
           | b |
           | c |
           | d |

    Returns:
      A matrix, L_q, that computes a left product by this quaternion.
    """
    return (
        self._xyzw[_QUATERNION_MULTIPLICATION_INDICES]
        * _QUATERNION_LEFT_MULTIPLICATION_SCALE_FACTORS
    )

  def right_multiplication_matrix(self) -> np.ndarray:
    """Returns the matrix that computes right multiplication.

    Multiplication by a quaternion is a linear operation.  This function
    computes the matrix that performs the linear operation of
    right-multiplication by this quaternion.

     Rq = |  w   z  -y   x |
          | -z   w   x   y |
          |  y  -x   w   z |
          | -x  -y  -z   w |

    If p = [ai + bj + ck + d], the product (p * q) can be computed by taking the
    matrix product of Rq with the column vector containing the components of p:

      Rq * | a |  ==  p * q
           | b |
           | c |
           | d |

    Returns:
      A matrix, R_q, that computes a right product by this quaternion.
    """
    return (
        self._xyzw[_QUATERNION_MULTIPLICATION_INDICES]
        * _QUATERNION_RIGHT_MULTIPLICATION_SCALE_FACTORS
    )

  def multiply(self, other_quaternion: 'Quaternion') -> 'Quaternion':
    """Returns the quaternion product (self * other_quaternion).

    Quaternion multiplication follows these rules:

      (i * i) = (j * j) = (k * k) = -1

      (i * j) = k   (j * i) = -k
      (j * k) = i   (k * j) = -i
      (k * i) = j   (i * k) = -j

      Quaternion multiplication is not commutative!

    Args:
      other_quaternion: Right hand side operand of quaternion product.

    Returns:
      The quaternion product: self * other_quaternion.
    """
    q_result_xyzw = np.matmul(
        self.left_multiplication_matrix(), other_quaternion.xyzw
    )
    return Quaternion(xyzw=q_result_xyzw)

  def scale(self, scale_factor: float) -> 'Quaternion':
    """Returns the quaternion scaled by a constant real value.

    Args:
      scale_factor: Real value to scale all coefficients.

    Returns:
      The product of the quaternion with the scale factor.
    """
    return Quaternion(self._xyzw * scale_factor)

  def divide(self, other: QuaternionOrScalarType) -> 'Quaternion':
    """Returns the quaternion quotient (self * other.inverse()).

    If the other value is a scalar, the result is a scale of the quaternion.

    Args:
      other: Right hand side operand of quaternion product.

    Returns:
      The quaternion product: self * other_quaternion.

    Raises:
      ValueError: If the other quaternion cannot be inverted.
    """
    if isinstance(other, Quaternion):
      return self.multiply(other.inverse())
    elif other <= QUATERNION_ZERO_EPSILON:
      # Calls the quaternion version to get the correct exception message.
      return self.divide(Quaternion.from_real(other))
    else:
      # If the operand is a real scalar, scales the quaternion components by the
      # inverse of the operand.
      return self.scale(1.0 / other)

  def normalize(self, err_msg: Text = '') -> 'Quaternion':
    """Returns a normalized copy of this quaternion.

    Calculates q / |q|

    Args:
      err_msg: Message to be added to error in case of failure.

    Returns:
      A quaternion with the same direction but magnitude 1.

    Raises:
      ValueError: If the quaternion cannot be normalized, i.e. |q| == 0.
    """
    norm = self.norm()
    if norm <= QUATERNION_ZERO_EPSILON:
      raise ValueError(
          self._zero_magnitude_message(
              norm_epsilon=QUATERNION_ZERO_EPSILON, err_msg=err_msg
          )
      )
    return Quaternion(self._xyzw / norm)

  def to_proto(
      self, proto_out: Optional[quaternion_pb2.Quaterniond] = None
  ) -> quaternion_pb2.Quaterniond:
    """Populates a Quaterniond protobuf with this quaternion.

    Args:
      proto_out: The output protobuf.  If not specified, create a new one.

    Returns:
      A Quaterniond protobuf containing the component values.  Returns the input
      protobuf if specified.
    """
    if proto_out is None:
      proto_out = quaternion_pb2.Quaterniond()
    proto_out.x = self.x
    proto_out.y = self.y
    proto_out.z = self.z
    proto_out.w = self.w
    return proto_out

  # --------------------------------------------------------------------------
  # Operators
  # --------------------------------------------------------------------------

  def __eq__(self, other: 'Quaternion') -> bool:
    """Returns True iff the quaternions are identical."""
    if not isinstance(other, type(self)):
      return NotImplemented
    return np.array_equal(self._xyzw, other.xyzw)

  def __ne__(self, other: 'Quaternion') -> bool:
    """Returns True iff the quaternions are not identical."""
    return not self == other

  __hash__ = None  # This class is not hashable.

  def __neg__(self) -> 'Quaternion':
    """Returns the negative (additive inverse) of this quaternion."""
    return Quaternion(xyzw=-(self._xyzw))

  def __mul__(self, other: QuaternionOrScalarType) -> 'Quaternion':
    """Returns the quaternion product of self * other."""
    if isinstance(other, Quaternion):
      return self.multiply(other)
    else:
      # If the operand is a scalar, scale the components.
      return self.scale(other)

  def __rmul__(self, scale_factor: float) -> 'Quaternion':
    """Returns the quaternion product of other * self."""
    # Multiplication with real scalar values is commutative.
    return self.scale(scale_factor)

  def __div__(self, other: QuaternionOrScalarType) -> 'Quaternion':
    """Returns quotient of self / other (python2).

    other / self == other * self^-1

    Args:
      other: Left hand operand of quotient.

    Returns:
      Quaternion quotient, other / self.

    Raises:
      ValueError: If the other quaternion or value cannot be inverted,
        i.e. |q| == 0.
    """
    return self.divide(other)

  def __truediv__(self, other: QuaternionOrScalarType) -> 'Quaternion':
    """Returns quotient of self / other (python3)."""
    return self.__div__(other)

  def __rdiv__(self, other: float) -> 'Quaternion':
    """Returns quotient of other / self (python2).

    other / self == other * self^-1

    This is equal to a scalar multiple of self.inverse().

    Args:
      other: Left hand operand of quotient.

    Returns:
      Quaternion quotient, other / self.

    Raises:
      ValueError: If the other quaternion cannot be inverted, i.e. |q| == 0.
    """
    return other * self.inverse()

  def __rtruediv__(self, other: float) -> 'Quaternion':
    """Returns quotient of other / self (python3)."""
    return self.__rdiv__(other)

  def __add__(self, other_quaternion: 'Quaternion') -> 'Quaternion':
    """Returns the sum of two quaternions.

    Quaternion addition works like complex addition, by adding the components:

      q = qx i + qy j + qz k + qw
      p = px i + py j + pz k + pw
      q + p = (qx + px) i + (qy + py) j + (qz + pz) k + (qw + pw).

    Args:
      other_quaternion: Right hand operand to addition.

    Returns:
      A quaternion equal to the sum of self + other_quaternion.
    """
    return Quaternion(self.xyzw + other_quaternion.xyzw)

  def __sub__(self, other_quaternion: 'Quaternion') -> 'Quaternion':
    """Returns the difference of two quaternions.

    Args:
      other_quaternion: Right hand operand to subtraction.

    Returns:
      A quaternion equal to the difference, self - other_quaternion.
    """
    return Quaternion(self.xyzw - other_quaternion.xyzw)

  def __abs__(self) -> float:
    """Returns the magnitude of the quaternion."""
    return self.norm()

  # --------------------------------------------------------------------------
  # Checks
  # --------------------------------------------------------------------------

  def _zero_magnitude_message(self, norm_epsilon: float, err_msg: Text = ''):
    return '%s: |%r| = %g <= %g  %s' % (
        QUATERNION_ZERO_MESSAGE,
        self,
        self.norm(),
        norm_epsilon,
        err_msg,
    )

  def check_non_zero(
      self, norm_epsilon: float = QUATERNION_ZERO_EPSILON, err_msg: Text = ''
  ) -> None:
    """Raises a ValueError exception if the quaternion is close to zero.

    Args:
      norm_epsilon: Error tolerance on magnitude.
      err_msg: Message to be added to error in case of failure.

    Raises:
      ValueError: If |q| <= norm_epsilon.
    """
    norm_squared = self.norm_squared()
    if norm_squared <= norm_epsilon**2:
      raise ValueError(
          self._zero_magnitude_message(
              norm_epsilon=norm_epsilon, err_msg=err_msg
          )
      )

  def check_normalized(
      self, norm_epsilon: float = QUATERNION_NORM_EPSILON, err_msg: Text = ''
  ) -> None:
    """Raises a ValueError exception if the quaternion is not normalized.

    Args:
      norm_epsilon: Error tolerance on magnitude.
      err_msg: Message to be added to error in case of failure.

    Raises:
      ValueError: If |q| != 1.
    """
    if not self.is_normalized(norm_epsilon):
      raise ValueError(
          '%s: |%r| = %g not within %g of 1.0  %s'
          % (
              QUATERNION_NOT_NORMALIZED_MESSAGE,
              self,
              self.norm(),
              norm_epsilon,
              err_msg,
          )
      )

  # --------------------------------------------------------------------------
  # Factory functions
  # --------------------------------------------------------------------------

  @classmethod
  def one(cls) -> 'Quaternion':
    """Returns 1, the multiplicative identity quaternion."""
    return cls(xyzw=vector_util.one_hot_vector(4, 3))

  @classmethod
  def zero(cls) -> 'Quaternion':
    """Returns zero, the additive identity quaternion."""
    return cls(xyzw=np.zeros(4))

  @classmethod
  def i(cls) -> 'Quaternion':
    """Returns the quaternion, i."""
    return cls(xyzw=vector_util.one_hot_vector(4, 0))

  @classmethod
  def j(cls) -> 'Quaternion':
    """Returns the quaternion, j."""
    return cls(xyzw=vector_util.one_hot_vector(4, 1))

  @classmethod
  def k(cls) -> 'Quaternion':
    """Returns the quaternion, k."""
    return cls(xyzw=vector_util.one_hot_vector(4, 2))

  @classmethod
  def from_real(cls, real_value: float) -> 'Quaternion':
    """Returns a quaternion representing a real value."""
    return cls(xyzw=[0.0, 0.0, 0.0, real_value])

  @classmethod
  def from_imaginary(cls, imaginary: math_types.Vector3Type) -> 'Quaternion':
    """Returns a quaternion representing a vector of purely imaginary values."""
    imaginary = vector_util.as_vector3(imaginary)
    return cls(xyzw=np.hstack((imaginary, [0.0])))

  @classmethod
  def from_real_imaginary(
      cls, real: float, imaginary: math_types.Vector3Type
  ) -> 'Quaternion':
    """Returns a quaternion represented by real and imaginary parts."""
    imaginary = vector_util.as_vector3(imaginary)
    return cls(xyzw=np.hstack((imaginary, [real])))

  @classmethod
  def random_unit(
      cls, rng: Optional[vector_util.RngType] = None
  ) -> 'Quaternion':
    """Returns a uniform random unit quaternion.

    Args:
      rng: A random number generator.

    Returns:
      A random Quaternion with magnitude one.
    """
    return cls(xyzw=vector_util.random_unit_4(rng=rng))

  @classmethod
  def from_proto(
      cls, quaternion_proto: quaternion_pb2.Quaterniond
  ) -> 'Quaternion':
    """Constructs a Quaternion from a Quaterniond protobuf message.

    Args:
      quaternion_proto: A quaternion protobuf message.

    Returns:
      The Quaternion represented by the protobuf.
    """
    return cls(
        xyzw=[
            quaternion_proto.x,
            quaternion_proto.y,
            quaternion_proto.z,
            quaternion_proto.w,
        ]
    )

  # --------------------------------------------------------------------------
  # String representations
  # --------------------------------------------------------------------------

  def __str__(self) -> Text:
    """Returns a string that describes the quaternion."""
    return '[%.4gi + %.4gj + %.4gk + %.4g]' % (self.x, self.y, self.z, self.w)

  def __repr__(self) -> Text:
    """Returns a string representation of the quaternion.

    This representation can be used to construct the quaternion.

    Returns:
      Returns the string, 'Quaternion([x, y, z, w])', which can be used to
      regenerate the quaternion.
    """
    return 'Quaternion([%r, %r, %r, %r])' % (self.x, self.y, self.z, self.w)
