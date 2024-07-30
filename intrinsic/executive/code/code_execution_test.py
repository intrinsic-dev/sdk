# Copyright 2023 Intrinsic Innovation LLC

"""Tests of code_execution.py."""

import sys

from absl.testing import absltest
from google.protobuf import any_pb2
from google.protobuf import descriptor_pb2
from google.protobuf import message_factory
from google.protobuf import text_format
from intrinsic.executive.code import code_execution
from intrinsic.math.proto import point_pb2
from intrinsic.skills.python import basic_compute_context
from intrinsic.solutions.testing import compare
from intrinsic.world.python import object_world_client

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

  def test_unpack_params_message(self):
    file_descriptor_set = text_format.Parse(
        """
        file {
          name: "unpack_params.proto"
          package: "my_protos"
          message_type {
            name: "UnpackParams"
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
    # Generate message class from file descriptor set. Note that the returned
    # class is independent/different from unpack_params_pb2.UnpackParams below.
    # message_factory.GetMessages creates its own descriptor pool on the fly.
    unpack_params_class = message_factory.GetMessages(file_descriptor_set.file)[
        "my_protos.UnpackParams"
    ]
    params_any = any_pb2.Any()
    params_any.Pack(unpack_params_class(my_str="some value"))

    params = code_execution.unpack_params_message(
        params_any, file_descriptor_set
    )

    unpack_params_pb2 = code_execution.import_from_file_descriptor_set(
        "unpack_params_pb2", file_descriptor_set
    )
    self.assertIsInstance(params, unpack_params_pb2.UnpackParams)
    compare.assertProto2Equal(
        self, params, unpack_params_pb2.UnpackParams(my_str="some value")
    )

  def test_unpack_params_message_fails(self):
    file_descriptor_set = descriptor_pb2.FileDescriptorSet()
    params_any = any_pb2.Any(
        type_url="type.googleapis.com/non.existent.Message",
    )

    with self.assertRaisesRegex(ValueError, "non.existent.Message"):
      code_execution.unpack_params_message(params_any, file_descriptor_set)

  def test_serialize_return_value_message(self):
    return_value = point_pb2.Point(x=1, y=2, z=3)
    expected_any = any_pb2.Any()
    expected_any.Pack(return_value)

    return_value_bytes = code_execution.serialize_return_value_message(
        return_value, "intrinsic_proto.Point"
    )

    self.assertEqual(return_value_bytes, expected_any.SerializeToString())

  def test_serialize_return_value_message_fails_on_wrong_type(self):
    with self.assertRaises(ValueError):
      code_execution.serialize_return_value_message(
          "this is not a proto message", "irrelevant.MessageType"
      )

    with self.assertRaises(ValueError):
      code_execution.serialize_return_value_message(
          point_pb2.Point(), "expected.MessageType"
      )

  def test_serialize_return_value_message_passes_none_through(self):
    self.assertIsNone(
        code_execution.serialize_return_value_message(
            None, "irrelevant.MessageType"
        )
    )

  def test_create_compute_context(self):
    context = code_execution.create_compute_context(
        "world_id",
        "invalid_world_service_address",
        "invalid_geometry_service_address",
    )

    self.assertIsInstance(context, basic_compute_context.BasicComputeContext)
    self.assertIsInstance(
        context.object_world, object_world_client.ObjectWorldClient
    )


if __name__ == "__main__":
  absltest.main()
