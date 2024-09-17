# Copyright 2023 Intrinsic Innovation LLC

from unittest import mock

from absl.testing import absltest
from google.protobuf import descriptor_pb2
from google.protobuf import text_format
from intrinsic.executive.proto import proto_builder_pb2
from intrinsic.solutions import behavior_tree
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import proto_building
from intrinsic.solutions.testing import compare


class ProtoBuildingTest(absltest.TestCase):
  """Tests that all public methods of ErrorLoader work."""

  # Transitively closed world descriptors containing a subset of the messages
  # from the actual object_world_refs.proto.
  _world_descriptors_min_pbtxt = """
  name: "intrinsic/world/proto/object_world_refs.proto"
  package: "intrinsic_proto.world"
  message_type {
    name: "ObjectReferenceByName"
    field {
      name: "object_name"
      number: 1
      label: LABEL_OPTIONAL
      type: TYPE_STRING
    }
  }
  message_type {
    name: "FrameReferenceByName"
    field {
      name: "object_name"
      number: 1
      label: LABEL_OPTIONAL
      type: TYPE_STRING
    }
    field {
      name: "frame_name"
      number: 2
      label: LABEL_OPTIONAL
      type: TYPE_STRING
    }
  }
  message_type {
    name: "TransformNodeReferenceByName"
    field {
      name: "object"
      number: 1
      label: LABEL_OPTIONAL
      type: TYPE_MESSAGE
      type_name: ".intrinsic_proto.world.ObjectReferenceByName"
      oneof_index: 0
    }
    field {
      name: "frame"
      number: 2
      label: LABEL_OPTIONAL
      type: TYPE_MESSAGE
      type_name: ".intrinsic_proto.world.FrameReferenceByName"
      oneof_index: 0
    }
    oneof_decl {
      name: "transform_node_reference_by_name"
    }
  }
  message_type {
    name: "ObjectReference"
    field {
      name: "id"
      number: 1
      label: LABEL_OPTIONAL
      type: TYPE_STRING
      oneof_index: 0
    }
    field {
      name: "by_name"
      number: 2
      label: LABEL_OPTIONAL
      type: TYPE_MESSAGE
      type_name: ".intrinsic_proto.world.ObjectReferenceByName"
      oneof_index: 0
    }
    field {
      name: "debug_hint"
      number: 3
      label: LABEL_OPTIONAL
      type: TYPE_STRING
    }
    oneof_decl {
      name: "object_reference"
    }
  }
  message_type {
    name: "TransformNodeReference"
    field {
      name: "id"
      number: 1
      label: LABEL_OPTIONAL
      type: TYPE_STRING
      oneof_index: 0
    }
    field {
      name: "by_name"
      number: 2
      label: LABEL_OPTIONAL
      type: TYPE_MESSAGE
      type_name: ".intrinsic_proto.world.TransformNodeReferenceByName"
      oneof_index: 0
    }
    field {
      name: "debug_hint"
      number: 3
      label: LABEL_OPTIONAL
      type: TYPE_STRING
    }
    oneof_decl {
      name: "transform_node_reference"
    }
  }
  syntax: "proto3"
"""

  def setUp(self):
    super().setUp()

    proto_builder_stub = mock.MagicMock()
    self._proto_builder = proto_building.ProtoBuilder(proto_builder_stub)

    wkt_response = proto_builder_pb2.GetWellKnownTypesResponse
    wkt_response.type_names = [
        'google.protobuf.Any',
        'google.protobuf.Empty',
        'google.protobuf.Int64Value',
        'google.protobuf.StringValue',
        'intrinsic_proto.Pose',
        'intrinsic_proto.Quaternion',
        'intrinsic_proto.world.ObjectReference',
        'intrinsic_proto.world.ObjectReferenceByName',
        'intrinsic_proto.world.TransformNodeReference',
    ]
    self._proto_builder._stub.GetWellKnownTypes.return_value = wkt_response

  def setup_compose_mock(
      self,
      package: str,
      input_descriptor: descriptor_pb2.DescriptorProto,
      has_world_protos: bool = False,
  ):
    """Sets up the return value for a Compose call.

    The Compose call will return a proper FileDescriptorSet that can be used in
    subsequent calls. This mocks a subset of the behavior of the proto builder
    service.

    It is assumed that a single message is to be constructed that either has
    single fields of built-in proto types or that they are message types from
    the world proto: ObjectReference, ObjectReferenceByName,
    TransformNodeReference, TransformNodeReferenceByName, FrameReferenceByName.

    Args:
      package: proto package for the message
      input_descriptor: descriptor for the message to be composed
      has_world_protos: set to true, if input_descriptor contains a world type.
    """
    compose_response = proto_builder_pb2.ProtoComposeResponse
    compose_descriptors = descriptor_pb2.FileDescriptorSet()
    message_file_descriptor = descriptor_pb2.FileDescriptorProto(
        name=package.replace('.', '_') + '_' + input_descriptor.name + '.proto',
        package=package,
    )
    if has_world_protos:
      world_descriptors_min = descriptor_pb2.FileDescriptorProto()
      text_format.Parse(
          ProtoBuildingTest._world_descriptors_min_pbtxt, world_descriptors_min
      )
      compose_descriptors.file.append(world_descriptors_min)
      message_file_descriptor.dependency.append(
          'intrinsic/world/proto/object_world_refs.proto'
      )
    message_file_descriptor.message_type.append(input_descriptor)
    compose_descriptors.file.append(message_file_descriptor)
    compose_response.file_descriptor_set = compose_descriptors
    self._proto_builder._stub.Compose.return_value = compose_response

  def assert_compose_call(
      self,
      package: str,
      name: str,
      expected_input_descriptor: descriptor_pb2.DescriptorProto,
  ):
    """Asserts that Compose was called with the expected parameters.

    Args:
      package: proto package for the message.
      name: name of the message.
      expected_input_descriptor: Single DescriptorProto to be composed.
    """
    self._proto_builder._stub.Compose.assert_called_once()
    compose_args, _ = self._proto_builder._stub.Compose.call_args
    compose_request = compose_args[0]
    self.assertEqual(compose_request.proto_package, package)
    self.assertEqual(
        compose_request.proto_filename,
        package.replace('.', '_') + '_' + name + '.proto',
    )

    # Note: The function under test `create_message` takes fields as a dict,
    # which is unordered, as the order does not matter for the user. Thus also
    # ignore the field order when verifying the call. Likewise also ignore the
    # assigned field numbers.
    compare.assertProto2SameElements(
        self,
        expected_input_descriptor,
        compose_request.input_descriptor[0],
        ignored_fields=['field.number'],
    )

  def test_get_well_known_types(self):
    wkt_actual = self._proto_builder.get_well_known_types()
    self.assertEqual(
        wkt_actual,
        [
            'google.protobuf.Any',
            'google.protobuf.Empty',
            'google.protobuf.Int64Value',
            'google.protobuf.StringValue',
            'intrinsic_proto.Pose',
            'intrinsic_proto.Quaternion',
            'intrinsic_proto.world.ObjectReference',
            'intrinsic_proto.world.ObjectReferenceByName',
            'intrinsic_proto.world.TransformNodeReference',
        ],
    )

  def test_create_empty_message(self):
    """Tests that an empty message can be created."""

    expected_input_descriptor = descriptor_pb2.DescriptorProto()
    text_format.Parse(
        """
      name: "TestMessage"
      """,
        expected_input_descriptor,
    )

    self.setup_compose_mock(
        package='test_pkg.sub_pkg',
        input_descriptor=expected_input_descriptor,
        has_world_protos=False,
    )

    msg = self._proto_builder.create_message(
        'test_pkg.sub_pkg', 'TestMessage', {}
    )

    # create_message must have called Compose with a descriptor similar to
    # expected_input_descriptor
    self.assert_compose_call(
        'test_pkg.sub_pkg', 'TestMessage', expected_input_descriptor
    )

    # The created msg object must also have a DESCRIPTOR similar to the
    # expected_input_descriptor
    msg_full_name, fds = behavior_tree._build_file_descriptor_set(msg)
    self.assertEqual(msg_full_name, 'test_pkg.sub_pkg.TestMessage')
    compare.assertProto2Equal(
        self,
        expected_input_descriptor,
        fds.file[0].message_type[0],
    )

  def test_create_basic_message(self):
    """Tests that a simple message can be created."""

    expected_input_descriptor = descriptor_pb2.DescriptorProto()
    text_format.Parse(
        """
      name: "TestMessage"
      field {
        name: "x"
        number: 1
        type: TYPE_INT64
        label: LABEL_OPTIONAL
      }
      field {
        name: "y"
        number: 2
        type: TYPE_DOUBLE
        label: LABEL_OPTIONAL
      }
      field {
        name: "a"
        number: 3
        type: TYPE_STRING
        label: LABEL_OPTIONAL
      }
      field {
        name: "b"
        number: 4
        type: TYPE_BOOL
        label: LABEL_OPTIONAL
      }
      field {
        name: "k"
        number: 5
        type: TYPE_BYTES
        label: LABEL_OPTIONAL
      }
      """,
        expected_input_descriptor,
    )

    self.setup_compose_mock(
        package='test_pkg.sub_pkg',
        input_descriptor=expected_input_descriptor,
        has_world_protos=False,
    )

    msg = self._proto_builder.create_message(
        'test_pkg.sub_pkg',
        'TestMessage',
        {'x': int, 'y': float, 'a': str, 'b': bool, 'k': bytes},
    )

    # create_message must have called Compose with a descriptor similar to
    # expected_input_descriptor
    self.assert_compose_call(
        'test_pkg.sub_pkg', 'TestMessage', expected_input_descriptor
    )

    # The created msg object must have the created fields
    self.assertTrue(hasattr(msg, 'x'))
    self.assertTrue(hasattr(msg, 'y'))
    self.assertTrue(hasattr(msg, 'a'))
    self.assertTrue(hasattr(msg, 'b'))
    self.assertTrue(hasattr(msg, 'k'))

    # The created msg object must also have a DESCRIPTOR similar to the
    # expected_input_descriptor
    msg_full_name, fds = behavior_tree._build_file_descriptor_set(msg)
    self.assertEqual(msg_full_name, 'test_pkg.sub_pkg.TestMessage')
    compare.assertProto2Equal(
        self,
        expected_input_descriptor,
        fds.file[0].message_type[0],
    )

  def test_create_message_with_well_known_types(self):
    """Tests that a message containing well known types can be created."""

    expected_input_descriptor = descriptor_pb2.DescriptorProto()
    text_format.Parse(
        """
              name: "TestMessage"
              field {
                name: "object"
                number: 1
                type: TYPE_MESSAGE
                type_name: "intrinsic_proto.world.ObjectReference"
                label: LABEL_OPTIONAL
              }
              field {
                name: "target_frame"
                number: 2
                type: TYPE_MESSAGE
                type_name: "intrinsic_proto.world.TransformNodeReference"
                label: LABEL_OPTIONAL
              }
      """,
        expected_input_descriptor,
    )

    self.setup_compose_mock(
        package='test_pkg.sub_pkg',
        input_descriptor=expected_input_descriptor,
        has_world_protos=True,
    )

    msg = self._proto_builder.create_message(
        'test_pkg.sub_pkg',
        'TestMessage',
        {
            'object': 'intrinsic_proto.world.ObjectReference',
            'target_frame': 'intrinsic_proto.world.TransformNodeReference',
        },
    )

    # create_message must have called Compose with a descriptor similar to
    # expected_input_descriptor
    self.assert_compose_call(
        'test_pkg.sub_pkg', 'TestMessage', expected_input_descriptor
    )

    # The created msg object must have the created fields
    self.assertTrue(hasattr(msg, 'object'))
    self.assertTrue(hasattr(msg, 'target_frame'))

    # The created msg object must also have a DESCRIPTOR similar to the
    # expected_input_descriptor
    msg_full_name, fds = behavior_tree._build_file_descriptor_set(msg)
    self.assertEqual(msg_full_name, 'test_pkg.sub_pkg.TestMessage')
    compare.assertProto2Equal(
        self,
        expected_input_descriptor,
        fds.file[0].message_type[0],
    )

  def test_create_message_with_unknown_message_type(self):
    """Tests that a message can only refer to well known types."""
    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """.*my_pkg.UnknownMessage is not a well known type.*""",
    ):
      self._proto_builder.create_message(
          'test_pkg.sub_pkg', 'TestMessage', {'test': 'my_pkg.UnknownMessage'}
      )
    self._proto_builder._stub.Compose.assert_not_called()

  def test_create_message_with_unknown_types(self):
    """Tests that a message can only refer to supported types."""
    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """.*test does not have a supported type.*""",
    ):
      self._proto_builder.create_message(
          'test_pkg.sub_pkg', 'TestMessage', {'test': list}
      )
    self._proto_builder._stub.Compose.assert_not_called()


if __name__ == '__main__':
  absltest.main()
