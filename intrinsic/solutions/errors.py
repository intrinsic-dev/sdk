# Copyright 2023 Intrinsic Innovation LLC

"""Common errors in the solution building library."""

import retrying


class Error(Exception):
  """Top-level module error for the solution building library."""


class InvalidArgumentError(Error):
  """Thrown when invalid arguments are passed to the solution building library."""


class NotFoundError(Error):
  """Thrown when an element cannot be found in the solution building library."""


class UnavailableError(Error):
  """Thrown when a backend of the solution building library cannot be reached."""


class FailedPreconditionError(Error):
  """Thrown when a precondition about the state of the solution is broken."""


class BackendPendingError(Error):
  """Thrown if a backend is unhealthy but expected to become healthy again."""


class BackendHealthError(Error):
  """Thrown if a backend is unhealthy and not expected to recover."""


class BackendNoWorkcellError(Error):
  """Thrown if no workcell spec has been installed."""


def _is_backend_pending_error(e: Exception) -> bool:
  """Determines whether a backend is expected to become healthy.

  Args:
    e: The exception under evaluation.

  Returns:
    True if the exception indicates that the backend is expected to become
      healthy again.
  """
  return isinstance(e, BackendPendingError)


# Decorator that retries if a backend's health is expected to recover.
retry_on_pending_backend = retrying.retry(
    retry_on_exception=_is_backend_pending_error,
    stop_max_attempt_number=40,
    wait_exponential_multiplier=2,
    wait_exponential_max=20000,  # in milliseconds
    wait_incrementing_start=2000,  # in milliseconds
)
