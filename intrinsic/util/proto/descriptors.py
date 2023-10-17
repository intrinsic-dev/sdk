# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for viewing and manipulating proto descriptors."""

import typing

from google.protobuf import descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool


def _add_file_and_imports(
    file_descriptors: typing.Dict[str, descriptor.FileDescriptor],
    current_file: descriptor.FileDescriptor,
):
  """Adds the current file to file_descriptors if not present.

  Recursively adds dependencies until all dependencies (along with transients)
  are present in file_descriptors.

  Args:
    file_descriptors: A dictionary mapping file descriptor name to file
      descriptors. Modified to add transitive dependencies of current_file
    current_file: The file descriptor of the current file.
  """
  if current_file.name in file_descriptors:
    return

  file_descriptors[current_file.name] = current_file
  for dependency_file_descriptor in current_file.dependencies:
    _add_file_and_imports(file_descriptors, dependency_file_descriptor)


def gen_file_descriptor_set(
    msg_descriptor: descriptor.Descriptor,
) -> descriptor_pb2.FileDescriptorSet:
  """Generates a FileDescriptorSet given a Descriptor.

  Args:
    msg_descriptor: The message descriptor of interest.

  Returns:
    A descriptor_pb2.FileDescriptorSet containing the file descriptors of all
    transitive dependencies of msg_descriptor.
  """
  file_descriptors = {}
  _add_file_and_imports(file_descriptors, msg_descriptor.file)
  file_descriptor_set = descriptor_pb2.FileDescriptorSet()
  for file_descriptor in file_descriptors.values():
    file_descriptor.CopyToProto(file_descriptor_set.file.add())
  return file_descriptor_set


def _append_file_descriptor_set_to_pool(
    pool: descriptor_pool.DescriptorPool,
    file_set: descriptor_pb2.FileDescriptorSet,
) -> None:
  """Appends a given file descriptor set to a file descriptor pool.

  Runs through all file descriptors and appends them one-by-one to the pool.

  Args:
    pool: Protobuf descriptor pool to append descriptors to
    file_set: proto containing the set of descriptors to add.
  """
  file_by_name = {file_proto.name: file_proto for file_proto in file_set.file}

  # N.B. GetMessages() file protos must be added in topo ordering to satisfy the
  # cpp impl of python Protobuf. If this is not done, we get strange errors
  # like "Message.field: 'FieldType' seems to be defined in 'file.proto',
  # which is not imported by '#.proto'.  To use it here, please add the
  # necessary import"
  def add_file(file_proto: descriptor_pb2.FileDescriptorProto):
    for dependency in file_proto.dependency:
      if dependency in file_by_name:
        # Remove from elements to be visited, in order to cut cycles.
        add_file(file_by_name.pop(dependency))
    pool.Add(file_proto)

  while file_by_name:
    add_file(file_by_name.popitem()[1])


def create_descriptor_pool(
    file_set: descriptor_pb2.FileDescriptorSet,
) -> descriptor_pool.DescriptorPool:
  """Returns a DescriptorPool containing all files in the given file set.

  Args:
    file_set: The file descriptors to seed the descriptor pool with.

  Returns:
    A descriptor pool containing all descriptors from the given file_set.
  """
  pool = descriptor_pool.DescriptorPool()
  _append_file_descriptor_set_to_pool(pool, file_set)
  return pool
