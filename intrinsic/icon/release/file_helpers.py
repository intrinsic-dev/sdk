# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Python equivalent to file_helpers.h."""

from google.protobuf import message


def load_binary_proto(path: str, msg: message.Message):
  """Reads a binary proto from a file to and loads it into a message.

  Args:
    path: The path to the binary proto file.
    msg: The message to load the binary proto file into.
  """
  with open(path, 'rb') as fb:
    msg.ParseFromString(fb.read())
