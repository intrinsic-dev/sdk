# Copyright 2023 Intrinsic Innovation LLC

"""Empty test that imports ICON python protos."""

# pylint: disable=unused-import
import grpc  # for some reason gRPC codegen needs this?
# pylint: enable=unused-import

from absl.testing import absltest

# pylint: disable=unused-import
from intrinsic.icon.proto import cart_space_pb2
from intrinsic.icon.proto import ik_options_pb2
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.icon.proto import matrix_pb2
from intrinsic.icon.proto import part_status_pb2
from intrinsic.icon.proto import service_pb2
from intrinsic.icon.proto import service_pb2_grpc
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.icon.proto import types_pb2
# pylint: enable=unused-import

if __name__ == '__main__':
  absltest.main()
