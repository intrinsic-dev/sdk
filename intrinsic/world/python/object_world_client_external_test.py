# Copyright 2023 Intrinsic Innovation LLC

"""Tests for the externalized object_world_client."""

from unittest import mock

from absl.testing import absltest
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids


class ObjectWorldClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._stub = mock.MagicMock()

  def _create_object_proto(
      self, *, name: str = '', object_id: str = '', world_id: str = ''
  ) -> object_world_service_pb2.Object:
    return object_world_service_pb2.Object(
        world_id=world_id,
        name=name,
        name_is_global_alias=True,
        id=object_id,
        object_component=object_world_service_pb2.ObjectComponent(),
    )

  def test_get_object(self):
    self._stub.GetObject.return_value = self._create_object_proto(
        name='my_object', object_id='15', world_id='world'
    )
    world_client = object_world_client.ObjectWorldClient('world', self._stub)

    self.assertEqual(
        world_client.get_object(
            object_world_ids.WorldObjectName('my_object')
        ).name,
        'my_object',
    )
    self.assertEqual(
        world_client.get_object(
            object_world_ids.WorldObjectName('my_object')
        ).id,
        '15',
    )

  def test_object_attribute(self):
    my_object = self._create_object_proto(
        name='my_object', object_id='15', world_id='world'
    )
    self._stub.GetObject.return_value = my_object
    self._stub.ListObjects.return_value = (
        object_world_service_pb2.ListObjectsResponse(objects=[my_object])
    )
    world_client = object_world_client.ObjectWorldClient('world', self._stub)

    self.assertEqual(world_client.my_object.name, 'my_object')
    self.assertEqual(world_client.my_object.id, '15')


if __name__ == '__main__':
  absltest.main()
