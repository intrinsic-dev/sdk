# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrapper around the proto builder service."""

from __future__ import annotations

from google.protobuf import descriptor_pb2
import grpc
from intrinsic.executive.proto import proto_builder_pb2
from intrinsic.executive.proto import proto_builder_pb2_grpc
from intrinsic.util.grpc import error_handling


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
