# Copyright 2023 Intrinsic Innovation LLC

"""Shared handlers for grpc errors."""

from typing import cast

import grpc
import retrying


# The Ingress will return UNIMPLEMENTED if the server it wants to forward to
# is unavailable, so we check for both UNAVAILABLE and UNIMPLEMENTED.
_UNAVAILABLE_CODES = [
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.UNIMPLEMENTED,
]


def is_unavailable_grpc_status(exception: Exception) -> bool:
  """Returns True if the given exception signals temporary unavailability.

  Use to determine whether retrying a gRPC request might help.

  Args:
    exception: The exception under evaluation.

  Returns:
    True if the given exception is a gRPC error that signals temporary
    unavailability.
  """
  if isinstance(exception, grpc.Call):
    return cast(grpc.Call, exception).code() in _UNAVAILABLE_CODES
  return False


def _is_unavailable_grpc_status_with_logging(exception: Exception) -> bool:
  """Same as 'is_unavailable_grpc_status' but also logs to the console."""
  is_unavailable = is_unavailable_grpc_status(exception)
  if is_unavailable:
    print("Backend unavailable. Retrying ...")
  return is_unavailable


# Decorator that retries gRPC requests if the server is unavailable.
retry_on_grpc_unavailable = retrying.retry(
    retry_on_exception=_is_unavailable_grpc_status_with_logging,
    stop_max_attempt_number=15,
    wait_exponential_multiplier=3,
    wait_exponential_max=10000,  # in milliseconds
    wait_incrementing_start=500,  # in milliseconds
)
