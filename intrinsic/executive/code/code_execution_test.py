# Copyright 2023 Intrinsic Innovation LLC

"""Tests of code_execution.py."""

import sys

from absl.testing import absltest
from google.protobuf import descriptor_pb2
from google.protobuf import text_format
from intrinsic.executive.code import code_execution
from intrinsic.math.proto import point_pb2

# Backup of the "initial state" of the import cache.
_SYS_MODULES_BACKUP = sys.modules.copy()


class CodeExecutionTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    # Reset import cache between tests to the "initial state".
    sys.modules = _SYS_MODULES_BACKUP.copy()

  def test_import_from_file_descriptor_set(self):
    file_descriptor_set = text_format.Parse(
        """
        file {
          name: "intrinsic/math/proto/point.proto"
          package: "intrinsic_proto"
          syntax: "proto3"
          # No messages defined here, test would fail if this file was used.
        }
        file {
          name: "my_folder/my_proto.proto"
          package: "my_protos"
          dependency: "intrinsic/math/proto/point.proto"
          message_type {
            name: "MyParams"
            field {
              name: "my_point"
              number: 1
              label: LABEL_OPTIONAL
              type: TYPE_MESSAGE
              type_name: ".intrinsic_proto.Point"
            }
            field {
              name: "my_str"
              number: 2
              label: LABEL_OPTIONAL
              type: TYPE_STRING
            }
          }
          syntax: "proto3"
        }""",
        descriptor_pb2.FileDescriptorSet(),
    )

    my_proto_pb2 = code_execution.import_from_file_descriptor_set(
        "my_folder.my_proto_pb2", file_descriptor_set
    )

    self.assertIsNotNone(my_proto_pb2.DESCRIPTOR)

    # Assert that creating a MyParams does not fail. If the following succeeds,
    # then:
    #  - my_proto_pb2 must have been created from the file descriptor set since
    #    there exists no corresponding "file" it could have been imported from.
    #  - point_pb2 must have been imported from the corresponding file since the
    #    corresponding "file" in the file descriptor set is empty.
    #  - my_proto_pb2 and point_pb2 must be using the same descriptor pool since
    #    otherwise the message creation would fail.
    my_proto_pb2.MyParams(my_str="foo", my_point=point_pb2.Point(x=1, y=2, z=3))

  def test_import_from_file_descriptor_set_fails_for_wrong_file_path(self):
    file_descriptor_set = text_format.Parse(
        """
        file {
          name: "some/other/path/point.proto"
          package: "intrinsic_proto"
          syntax: "proto3"
          message_type {
            name: "Point"
          }
        }
        file {
          name: "my_folder/my_proto.proto"
          package: "my_protos"
          dependency: "some/other/path/point.proto"
          syntax: "proto3"
        }""",
        descriptor_pb2.FileDescriptorSet(),
    )

    with self.assertRaisesRegex(TypeError, "intrinsic_proto.Point"):
      # This should fail because the file descriptor set contains point.proto
      # under a different path (some/other/path/point.proto) than the current
      # Python environment (intrinsic/math/proto/point.proto) and we have
      # imported the latter already at the top.
      code_execution.import_from_file_descriptor_set(
          "my_folder.my_proto_pb2", file_descriptor_set
      )

  def test_import_from_file_descriptor_set_fails_for_invalid_input(self):
    file_descriptor_set = descriptor_pb2.FileDescriptorSet()

    with self.assertRaisesRegex(ValueError, "must end with _pb2"):
      code_execution.import_from_file_descriptor_set(
          "some.non_proto_module", file_descriptor_set
      )

    with self.assertRaisesRegex(
        ValueError, "Could not find file not/in/file_descriptor_set.proto"
    ):
      code_execution.import_from_file_descriptor_set(
          "not.in.file_descriptor_set_pb2", file_descriptor_set
      )


if __name__ == "__main__":
  absltest.main()
