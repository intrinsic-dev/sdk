# Copyright 2023 Intrinsic Innovation LLC

"""Utility functions for vectors (python3).

Vectors are represented as a numpy.ndarray.

Utility functions:
  one_hot_vector - Returns a vector of all 0 except for a single 1 value.
  is_vector_normalized - Efficient check for magnitude 1.
"""

from typing import Optional, Text, Type, Union

from intrinsic.math.python import math_types
import numpy as np


# ----------------------------------------------------------------------------
# Error messages for exceptions.
VECTOR_COMPONENTS_MESSAGE = 'Vector has incorrect number of components'
VECTOR_INFINITE_VALUES_MESSAGE = 'Vector has non-finite values'
VECTOR_VALUES_MESSAGE = 'Vector has NaN values'


def normalize_vector(
    vector: math_types.VectorType, err_msg: Text = ''
) -> np.ndarray:
  """Returns a vector in the same direction but with magnitude 1.

  Args:
    vector:
    err_msg:

  Returns:
    A vector in the same direction as the argument but with magnitude 1.

  Raises:
    ValueError: If the vector cannot be normalized.
  """
  vector = np.array(vector, dtype=np.float64)
  vector_norm = np.linalg.norm(vector)
  if vector_norm <= math_types.DEFAULT_ATOL_VALUE_FOR_NP_IS_CLOSE:
    raise ValueError(
        '%s: |%r| = %f\n%s'
        % ('Vector has nearly zero magnitude.', vector, vector_norm, err_msg)
    )
  return vector / vector_norm


def one_hot_vector(
    dimension: int,
    hot_index: int,
    dtype: Union[np.dtype, Type[np.number]] = np.float64,
) -> np.ndarray:
  """Returns a vector with all zeros except the hot_index component.

  For example,
    one_hot_vector(3, 0) = [1, 0, 0]
    one_hot_vector(4, 2) = [0, 0, 1, 0]

  Args:
    dimension: Number of components in the vector.
    hot_index: Index of element with value 1.0.
    dtype: Numeric type of components.

  Returns:
    The one-hot vector as a numpy array.
  """
  vector = np.zeros(dimension, dtype=dtype)
  vector[hot_index] = 1
  return vector


def as_vector(
    values: math_types.VectorType,
    dimension: Optional[int] = None,
    dtype: Optional[Union[np.dtype, Type[np.number]]] = None,
    err_msg: Text = '',
) -> np.ndarray:
  """Interprets the values as a vector with <dimension> components.

  All values may be infinite.  NaN values will result in an error.

  Args:
    values: Input vector values.
    dimension: Expected dimension of output vector and number of components in
      input vector.
    dtype: Numeric type of array.
    err_msg: Error message string appended to exception in case of failure.

  Returns:
    The input vector as a numpy array after checking its size and values.

  Raises:
    ValueError: If the inputs are not a valid vector with the correct number of
      components.
  """
  if dimension is not None and len(values) != dimension:
    raise ValueError(
        '%s: Expected %d vector components, but found %d: %r\n%s'
        % (VECTOR_COMPONENTS_MESSAGE, dimension, len(values), values, err_msg)
    )
  vector = np.asarray(values, dtype=dtype)
  if np.any(np.isnan(vector)):
    raise ValueError('%s: %r\n%s' % (VECTOR_VALUES_MESSAGE, values, err_msg))
  return vector


def as_finite_vector(
    values: math_types.VectorType,
    dimension: Optional[int] = None,
    normalize: bool = False,
    dtype: Optional[Union[np.dtype, Type[np.number]]] = None,
    err_msg: Text = '',
) -> np.ndarray:
  """Interprets the values as a vector with <dimension> components.

  All values must be finite.  Infinite or NaN values will result in an error.

  Args:
    values: Input vector values.
    dimension: Expected dimension of output vector and number of components in
      input vector.
    normalize: Indicates whether to normalize the vector.
    dtype: Numeric type of array.
    err_msg: Error message string appended to exception in case of failure.

  Returns:
    The input vector as a numpy array after checking its size and values.

  Raises:
    ValueError: If the inputs are not a valid vector with the correct number of
      components or if normalize is True and the vector has near zero magnitude.
  """
  vector = as_vector(
      values=values, dimension=dimension, dtype=dtype, err_msg=err_msg
  )
  if not np.all(np.isfinite(vector)):
    raise ValueError(
        '%s: %r\n%s' % (VECTOR_INFINITE_VALUES_MESSAGE, values, err_msg)
    )
  if normalize:
    vector = normalize_vector(vector, err_msg=err_msg)
  return vector


def as_vector3(
    values: math_types.VectorType,
    dtype: Union[np.dtype, Type[np.number]] = np.float64,
    err_msg='',
):
  """Gets input as a finite vector with dimension=3, dtype=float64."""
  return as_finite_vector(values, dimension=3, dtype=dtype, err_msg=err_msg)


def as_unit_vector3(
    values: math_types.VectorType,
    dtype: Union[np.dtype, Type[np.number]] = np.float64,
    err_msg='',
):
  """Gets input as a finite vector with dimension=3, dtype=float64, normalize=True."""
  return as_finite_vector(
      values, dimension=3, normalize=True, dtype=dtype, err_msg=err_msg
  )


def is_vector_normalized(
    vector: math_types.VectorType,
    norm_epsilon: float = math_types.DEFAULT_RTOL_VALUE_FOR_NP_IS_CLOSE,
) -> bool:
  """Returns true if |vector| = 1 within epsilon tolerance.

  If norm_epsilon is zero, only vectors that have magnitude precisely 1.0 will
  be considered normalized.

  This is an efficient computation without sqrt, but it is only accurate within
  norm_epsilon squared.

  Args:
    vector: Vector to check for magnitude = 1.
    norm_epsilon: Error tolerance on magnitude of vector.

  Returns:
    True if the magnitude of the vector is within epsilon of 1.0.
  """
  vector = np.asarray(vector)
  v_dot_v = vector.dot(vector)
  # The error in the squared norm varies linearly with error in component
  # values when the vector is close to unit magnitude.
  #
  # If |v| = 1 + x with x << 1
  #   then v.v = (1 + x)^2 = 1 + 2x + x^2
  #   and |1.0 - v.v| = |2x + x^2|
  #   which is close to 2|x|
  return abs(1 - v_dot_v) <= norm_epsilon * 2
