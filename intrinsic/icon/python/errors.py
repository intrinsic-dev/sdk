# Copyright 2023 Intrinsic Innovation LLC

"""A common location for ICON exceptions.

Centralises the exceptions for the ICON module through a single import. A common
base Error is provided for users to easily handle all ICON related exceptions.

  Usage example:

  try:
    session.do_something(...)
  except errors.Session.ActionError:
    # Handle specific error.
"""


class Error(Exception):
  pass


class Client:
  """Errors raised by icon.py."""

  class ServerError(Error):
    """Errors related to server connection."""

  class InvalidArgumentError(Error):
    """Errors related to bad arguments."""


class Session:
  """Errors raised by _session.py."""

  class ActionError(Error):
    """Errors related to OpenSessionResponse."""

  class StreamError(Error):
    """Errors related to OpenWriteStreamResponse."""

  class SessionEndedError(Error):
    """Errors related to the (expected or unexpected) end of an ICON sesson."""
