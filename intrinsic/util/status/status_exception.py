# Copyright 2023 Intrinsic Innovation LLC

"""Exception implementation with additional extended status."""

from __future__ import annotations

import datetime

from intrinsic.logging.proto import context_pb2
from intrinsic.util.status import extended_status_pb2


class ExtendedStatusError(Exception):
  """Class that represents an error with extended status information.

  The class uses the builder pattern, so you can parameterize and raise the
  exception like this:

  raise status_exception.ExtendedStatusError()
    .set_status_code("ai.intrinsic.my_skill", 24543)
    .set_title("Failed to do fancy thing")
    .set_timestamp()

  Attributes:
    extended_status: extended status proto that is modified with builder methods
  """

  extended_status: extended_status_pb2.ExtendedStatus

  def __init__(self, external_report_message: str = ""):
    """Initializes the instance.

    Args:
      external_report_message: if non-empty, set extended status external report
        message to this string. This is for backwards compatibility with Python
        exceptions. It is recommended to call the appropriate functions to set
        extended status details.
    """
    self.extended_status = extended_status_pb2.ExtendedStatus()
    if external_report_message:
      self.set_external_report_message(external_report_message)
    super().__init__(external_report_message)

  def set_extended_status(
      self, extended_status: extended_status_pb2.ExtendedStatus
  ) -> ExtendedStatusError:
    """Sets extended status directly from a proto."""
    self.extended_status = extended_status
    return self

  def set_status_code(
      self, component: str, error_code: int
  ) -> ExtendedStatusError:
    """Sets the status code.

    Args:
      component: component where the error originated
      error_code: numeric error code for the specific unique error

    Returns:
      self
    """
    self.extended_status.status_code.component = component
    self.extended_status.status_code.code = error_code
    return self

  def set_timestamp(
      self, timestamp: datetime.datetime = datetime.datetime.now()
  ) -> ExtendedStatusError:
    """Sets time of error.

    Args:
      timestamp: the time of the error. Default argument simply sets current
        time.

    Returns:
      self
    """
    self.extended_status.timestamp.FromDatetime(timestamp)
    return self

  def set_title(self, title: str) -> ExtendedStatusError:
    """Sets title of error.

    Args:
      title: title string for the error

    Returns:
      self
    """
    self.extended_status.title = title
    return self

  def add_context(
      self, context_status: extended_status_pb2.ExtendedStatus
  ) -> ExtendedStatusError:
    """Adds context status.

    Args:
      context_status: another extended status that helps explain or further
        analyze this error.

    Returns:
      self
    """
    self.extended_status.context.append(context_status)
    return self

  def set_internal_report_message(self, message: str) -> ExtendedStatusError:
    """Sets internal report message.

    Call this function only if you intend for the receiver of the status to see
    it. An indicator could be running in the context of specific organizations.

    Args:
      message: human-readable error message intended for internal developers

    Returns:
      self
    """
    self.extended_status.internal_report.message = message
    return self

  def set_external_report_message(self, message: str) -> ExtendedStatusError:
    """Sets external report message.

    This is the main error message and should almost always be set.

    Args:
      message: human-readable error message intended for users of the component.

    Returns:
      self
    """
    self.extended_status.external_report.message = message
    return self

  def set_log_context(
      self, context: context_pb2.Context
  ) -> ExtendedStatusError:
    """Sets logging context.

    Note that this is specific to the structured data logger. This is NOT
    other extended status as context (use add_context() for those).

    Args:
      context: log context

    Returns:
      self
    """
    self.extended_status.log_context.CopyFrom(context)
    return self
