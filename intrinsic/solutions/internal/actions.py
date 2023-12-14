# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrappers around actions."""

import abc
import datetime
from typing import Any, Optional

from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.math.python import data_types
from intrinsic.skills.proto import skills_pb2


def _format_nd_vector(vector: skills_pb2.VectorNdValue) -> str:
  return f'[{", ".join(str(value) for value in vector.value)}]'


def _format_string_vector(vector: skills_pb2.StringVector) -> str:
  return f'[{", ".join(repr(value) for value in vector.values)}]'


def _format_nd_array(array: skills_pb2.VectorNdArray) -> str:
  rows = [_format_nd_vector(vector) for vector in array.array]
  return f'[{", ".join(rows)}]'


def _format_pose3(pose: data_types.Pose3) -> str:
  # NOTE: We do not use str() here because it does not generate copy&paste-able
  # Python code: 'Pose3(Rotation3([0i + 0j + 0k + 1]),[1.1 2.2 3.3])'
  return 'types.Pose3.from_vec7([{}, {}, {}, {}, {}, {}, {}, ])'.format(
      *pose.vec7
  )


_MESSAGE_NAME_TO_STRING_MAP = {
    'intrinsic_proto.skills.StringVector': _format_string_vector,
    'intrinsic_proto.skills.VectorNdValue': _format_nd_vector,
    'intrinsic_proto.skills.VectorNdArray': _format_nd_array,
}


def message_to_repr_string(message_name: str, value: Any) -> str:
  """Returns the string representation of value.

  value is associated with the protobuf type message_name in the workcell API.
  The returned string should be usable in the ways that repr() normally implies
  to construct an object of the correct type with the given value.

  If the message_name does not have a custom type associated with it in the
  Workcell API, this defaults to returning repr(value).

  Args:
    message_name: The Protobuf type associated with the value in Workcell API
    value: The value to create a representation of
  """
  if message_name in _MESSAGE_NAME_TO_STRING_MAP:
    return _MESSAGE_NAME_TO_STRING_MAP[message_name](value)
  # For messages that we don't have a intrinsic-native pythonic-type support
  # just fallback to protobuf message repr.
  return repr(value)


class ActionBase(abc.ABC):
  """Abstract base class of an action.

  Derived classes need to override the getter for self.proto.
  """

  def __init__(self):
    self._project_timeout: Optional[datetime.timedelta] = None
    self._execute_timeout: Optional[datetime.timedelta] = None

  @property
  @abc.abstractmethod
  def proto(self) -> behavior_call_pb2.BehaviorCall:
    """Proto representation of action.

    Needs to be overridden by subclasses.

    Returns:
      Proto representation of action as behavior_call_pb2.BehaviorCall.

    Raises:
      NoImplementedError if the class fails to override method.
    """
    raise NotImplementedError

  @property
  def execute_timeout(self) -> Optional[datetime.timedelta]:
    """Timeout after which execution should be considered failed."""
    return self._execute_timeout

  @execute_timeout.setter
  def execute_timeout(self, timeout: datetime.timedelta) -> None:
    self._execute_timeout = timeout

  @property
  def project_timeout(self) -> Optional[datetime.timedelta]:
    """Timeout after which projection should be considered failed."""
    return self._project_timeout

  @project_timeout.setter
  def project_timeout(self, timeout: datetime.timedelta) -> None:
    self._project_timeout = timeout
