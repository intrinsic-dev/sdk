# Copyright 2023 Intrinsic Innovation LLC

"""Tests for source_code_info_present."""

import os

from absl import flags
from absl.testing import absltest
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import message_factory

FLAGS = flags.FLAGS


def _read_message_from_pbbin_file(filename):
  with open(filename, 'rb') as fileobj:
    return descriptor_pb2.FileDescriptorSet.FromString(fileobj.read())


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


def _create_descriptor_pool(
    file_set: descriptor_pb2.FileDescriptorSet,
) -> descriptor_pool.DescriptorPool:
  """Adds files in file_set to self._descriptor_pool().

  Args:
    file_set: The file descriptors to seed the descriptor pool with.

  Returns:
    A descriptor pool containing all descriptors from the given file_set.
  """
  pool = descriptor_pool.DescriptorPool()
  _append_file_descriptor_set_to_pool(pool, file_set)
  return pool


class SourceCodeInfoPresentTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._test_data_path = os.path.normpath(os.path.join(__file__, '..'))
    self._file_descriptor_set_pbbin_filename = os.path.join(
        FLAGS.test_srcdir,
        self._test_data_path,
        'test_message_proto_descriptors_transitive_set_sci.proto.bin',
    )
    self._file_descriptor_set = _read_message_from_pbbin_file(
        self._file_descriptor_set_pbbin_filename
    )

  def test_source_code_info(self):
    for file in self._file_descriptor_set.file:
      self.assertTrue(file.HasField('source_code_info'))

  def test_can_construct_classes(self):
    desc_pool = _create_descriptor_pool(self._file_descriptor_set)
    msg_factory = message_factory.MessageFactory(pool=desc_pool)
    for file_proto in self._file_descriptor_set.file:
      msg_factory.GetMessages([file_proto.name])


if __name__ == '__main__':
  absltest.main()
