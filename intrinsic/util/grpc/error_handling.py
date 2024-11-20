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


def is_resource_exhausted_grpc_status(exception: Exception) -> bool:
  """Returns True if the given exception signals resource exhausted.

  Args:
    exception: The exception under evaluation.

  Returns:
    True if the given exception is a gRPC error that signals resource exhausted.
  """
  if isinstance(exception, grpc.Call):
    return (
        cast(grpc.Call, exception).code() == grpc.StatusCode.RESOURCE_EXHAUSTED
    )
  return False


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


def _is_resource_exhausted_grpc_status_with_logging(
    exception: Exception,
) -> bool:
  """Same as 'is_resource_exhausted_grpc_status' but also logs to the console."""
  is_resource_exhausted = is_resource_exhausted_grpc_status(exception)
  if is_resource_exhausted:
    print("Backend resource exhausted. Retrying ...")
  return is_resource_exhausted


def _is_unavailable_grpc_status_with_logging(exception: Exception) -> bool:
  """Same as 'is_unavailable_grpc_status' but also logs to the console."""
  is_unavailable = is_unavailable_grpc_status(exception)
  if is_unavailable:
    print("Backend unavailable. Retrying ...")
  return is_unavailable


def _is_transient_error_grpc_status_with_logging(exception: Exception) -> bool:
  """Logs and returns true if the exception is a transient error."""
  return _is_unavailable_grpc_status_with_logging(
      exception
  ) or _is_resource_exhausted_grpc_status_with_logging(exception)


# Decorator that retries gRPC requests if the server is resource exhausted.
# The default policy here should happen with a larger delay than the default
# retry_on_grpc_unavailable policy to avoid spamming the backend.
retry_on_grpc_resource_exhausted = retrying.retry(
    retry_on_exception=_is_resource_exhausted_grpc_status_with_logging,
    stop_max_attempt_number=15,
    wait_exponential_multiplier=4,
    wait_exponential_max=20000,  # in milliseconds
    wait_incrementing_start=1000,  # in milliseconds
    wait_jitter_max=1000,  # in milliseconds
)


# Decorator that retries gRPC requests if the server is unavailable.
retry_on_grpc_unavailable = retrying.retry(
    retry_on_exception=_is_unavailable_grpc_status_with_logging,
    stop_max_attempt_number=15,
    wait_exponential_multiplier=3,
    wait_exponential_max=10000,  # in milliseconds
    wait_incrementing_start=500,  # in milliseconds
    wait_jitter_max=1000,  # in milliseconds
)

# Decorator that retries gRPC requests if the server is reporting a transient
# error.
# The default policy here should happen with a larger delay than the default
# retry_on_grpc_unavailable policy to avoid spamming the backend.
retry_on_grpc_transient_errors = retrying.retry(
    retry_on_exception=_is_transient_error_grpc_status_with_logging,
    stop_max_attempt_number=15,
    wait_exponential_multiplier=4,
    wait_exponential_max=20000,  # in milliseconds
    wait_incrementing_start=1000,  # in milliseconds
    wait_jitter_max=1000,  # in milliseconds
)
