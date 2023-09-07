# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Utility functions for skills related proto conversions."""
from typing import TypeVar

from google.protobuf import any_pb2
from google.protobuf import message

T = TypeVar("T", bound=message.Message)


class ProtoMismatchTypeError(TypeError):
  """An unexpected proto type was specified."""


def unpack_any(any_message: any_pb2.Any, proto_message: T) -> T:
  """Unpacks a proto Any into a message.

  The message passed must be the same type as is contained in the proto Any.

  Args:
    any_message: a proto Any message.
    proto_message: A proto message of the type contained in the any to unpack
      the message into.

  Returns:
    The unpacked proto message.

  Raises:
    ProtoMismatchTypeError: If the type of `proto_message` does not match that
      of the specified Any proto.
  """

  if not any_message.Unpack(proto_message):
    raise ProtoMismatchTypeError(
        f"Expected proto of type {any_message.TypeName()}, but got"
        f" {proto_message.DESCRIPTOR.name}"
    )

  return proto_message
