# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrapper around the proto builder service."""

from __future__ import annotations

from google.protobuf import descriptor_pb2
from google.protobuf import message as protobuf_message
import grpc
from intrinsic.executive.proto import proto_builder_pb2
from intrinsic.executive.proto import proto_builder_pb2_grpc
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions.internal import skill_utils
from intrinsic.util.grpc import error_handling
from intrinsic.util.proto import descriptors


class ProtoBuilder:
  """Wrapper for the proto builder gRPC service."""

  def __init__(self, stub: proto_builder_pb2_grpc.ProtoBuilderStub):
    """Constructs a new ProtoBuilder object.

    Args:
      stub: The gRPC stub to be used for communication with the service.
    """
    self._stub: proto_builder_pb2_grpc.ProtoBuilderStub = stub

  @classmethod
  def connect(cls, grpc_channel: grpc.Channel) -> ProtoBuilder:
    """Connect to a running proto builder.

    Args:
      grpc_channel: Channel to the gRPC service.

    Returns:
      A newly created instance of the wrapper class.

    Raises:
      grpc.RpcError: When gRPC call to service fails.
    """
    stub = proto_builder_pb2_grpc.ProtoBuilderStub(grpc_channel)
    return cls(stub)

  @error_handling.retry_on_grpc_unavailable
  def compile(
      self, proto_filename: str, proto_schema: str
  ) -> descriptor_pb2.FileDescriptorSet:
    """Compiles a proto schema into a FileDescriptorSet proto.

    Args:
      proto_filename: file name to assume for the generated FileDescriptor.
      proto_schema: The schema, e.g., the contents of a .proto file.

    Returns:
      A FileDescriptorSet for the proto_schema.

    Raises:
      grpc.RpcError: When gRPC call fails.
    """
    request = proto_builder_pb2.ProtoCompileRequest(
        proto_filename=proto_filename, proto_schema=proto_schema
    )

    response = self._stub.Compile(request)
    return response.file_descriptor_set

  @error_handling.retry_on_grpc_unavailable
  def compose(
      self,
      proto_filename: str,
      proto_package: str,
      input_descriptors: list[descriptor_pb2.DescriptorProto],
  ) -> descriptor_pb2.FileDescriptorSet:
    """Composes a list of DescriptorProtos into a FileDescriptorSet proto.

    The fields in the input descriptors must point to either native proto types
    or a message contained in the well known types. Use get_well_known_types()
    for a list of the available message types.

    Args:
      proto_filename: file name to assume for the generated FileDescriptor.
      proto_package: the proto package the input_descriptors are in.
      input_descriptors: list of DescriptorProto describing the messages.

    Returns:
      A FileDescriptorSet for the input_descriptors.

    Raises:
      grpc.RpcError: When gRPC call fails.
    """
    request = proto_builder_pb2.ProtoComposeRequest(
        proto_filename=proto_filename,
        proto_package=proto_package,
        input_descriptor=input_descriptors,
    )

    response = self._stub.Compose(request)
    return response.file_descriptor_set

  @error_handling.retry_on_grpc_unavailable
  def get_well_known_types(self) -> list[str]:
    """Retrieves a list of well known types.

    Returns:
      A list of full names for the well known types.

    Raises:
      grpc.RpcError: When gRPC call fails.
    """
    request = proto_builder_pb2.GetWellKnownTypesRequest()

    response = self._stub.GetWellKnownTypes(request)
    return list(response.type_names)

  def create_message(
      self,
      package: str,
      name: str,
      fields: dict[
          str,
          type[int] | type[float] | type[str] | type[bool] | type[bytes] | str,
      ],
  ) -> protobuf_message.Message:
    """Creates a new custom message.

    Example usage:
      create_message('my_pkg', 'MyMessage', {
          'x': float,
          'a': str,
          'object' : 'intrinsic_proto.world.ObjectReference'})

    Args:
      package: The proto package for the message.
      name: The name of the message.
      fields: dict from field name to field type. The type can either be a
        python type, i.e., `int`, `float`, `str`, `bool`, `bytes` or the name of
        a well known type (see get_well_known_types).

    Returns:
      An instance of the new message.
    """
    # 1. Check that all fields refer to built-in types or well known types
    well_known_types = self.get_well_known_types()
    for field_name, field_type in fields.items():
      if isinstance(field_type, str):
        if field_type not in well_known_types:
          raise solutions_errors.InvalidArgumentError(
              f"Field {field_name} with type {field_type} is not a well known"
              " type."
          )
    # 2. Compose a file descriptor set
    proto_filename = package + "_" + name
    proto_filename = proto_filename.replace(".", "_")
    proto_filename = proto_filename + ".proto"
    msg_descriptor = descriptor_pb2.DescriptorProto(name=name)
    for field_number, field in enumerate(fields.items()):
      field_name, field_type = field
      if isinstance(field_type, str):
        msg_descriptor.field.append(
            descriptor_pb2.FieldDescriptorProto(
                name=field_name,
                number=field_number + 1,
                type_name=field_type,
                type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
                label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
            )
        )
      elif isinstance(field_type, type):
        # There are multiple proto types mapping to the same python type. Thus
        # when inverting the mapping here we must pick a type, e.g., a python
        # int is TYPE_INT64.
        if field_type == int:
          proto_field_type = descriptor_pb2.FieldDescriptorProto.TYPE_INT64
        elif field_type == float:
          proto_field_type = descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE
        elif field_type == str:
          proto_field_type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
        elif field_type == bool:
          proto_field_type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL
        elif field_type == bytes:
          proto_field_type = descriptor_pb2.FieldDescriptorProto.TYPE_BYTES
        else:
          raise solutions_errors.InvalidArgumentError(
              f"Field {field_name} does not have a supported type:"
              f" {field_type}."
          )
        msg_descriptor.field.append(
            descriptor_pb2.FieldDescriptorProto(
                name=field_name,
                number=field_number + 1,
                type=proto_field_type,
                label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
            )
        )
      else:
        raise solutions_errors.InvalidArgumentError(
            f"For field {field_name}, type {field_type} is not supported"
        )
    file_descriptor_set = self.compose(
        proto_filename, package, [msg_descriptor]
    )

    # 3. Construct the message out of the file descriptor set
    desc_pool = descriptors.create_descriptor_pool(file_descriptor_set)
    message_type = desc_pool.FindMessageTypeByName(package + "." + name)
    assert message_type is not None

    return skill_utils.get_message_class(message_type)()
