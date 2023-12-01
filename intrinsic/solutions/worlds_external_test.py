# Copyright 2023 Intrinsic Innovation LLC

"""External tests for object_world."""

from unittest import mock

from absl.testing import absltest
from intrinsic.solutions import worlds
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.proto import object_world_service_pb2_grpc


class ObjectWorldExternalTest(absltest.TestCase):

  def test_object_world_access(self):
    my_object = object_world_service_pb2.Object(
        name='my_object',
        id='my_id',
        parent=object_world_service_pb2.IdAndName(id='root_id', name='root'),
        name_is_global_alias=True,
        object_component=object_world_service_pb2.ObjectComponent(),
    )

    with mock.patch.object(
        object_world_service_pb2_grpc, 'ObjectWorldServiceStub'
    ) as mock_object_world_service_stub:
      stub = mock.MagicMock()
      stub.GetObject.return_value = my_object
      stub.ListObjects.return_value = (
          object_world_service_pb2.ListObjectsResponse(objects=[my_object])
      )
      mock_object_world_service_stub.return_value = stub
      channel = mock.MagicMock()

      world = worlds.ObjectWorldExternal.connect('world', channel)
      self.assertEqual(world.my_object.name, 'my_object')


if __name__ == '__main__':
  absltest.main()
