# Copyright 2023 Intrinsic Innovation LLC

"""Tests for the externalized object_world_client."""

from unittest import mock

from absl.testing import absltest
from google.protobuf import any_pb2
from google.protobuf import struct_pb2
from google.protobuf import wrappers_pb2
from intrinsic.scene.proto.v1 import scene_object_pb2
from intrinsic.world.proto import geometry_component_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids


class ObjectWorldClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._stub = mock.MagicMock()
    self._geometry_service_stub = mock.MagicMock()

  def _create_object_proto(
      self,
      *,
      name: str = '',
      object_id: str = '',
      world_id: str = '',
      user_data=None,
  ) -> object_world_service_pb2.Object:
    return object_world_service_pb2.Object(
        world_id=world_id,
        name=name,
        name_is_global_alias=True,
        id=object_id,
        object_component=object_world_service_pb2.ObjectComponent(
            user_data=user_data
        ),
    )

  def test_get_object(self):
    my_object = self._create_object_proto(
        name='my_object', object_id='15', world_id='world'
    )
    self._stub.GetObject.return_value = my_object
    world_client = object_world_client.ObjectWorldClient(
        'world', self._stub, self._geometry_service_stub
    )

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
    world_client = object_world_client.ObjectWorldClient(
        'world', self._stub, self._geometry_service_stub
    )

    self.assertEqual(world_client.my_object.name, 'my_object')
    self.assertEqual(world_client.my_object.id, '15')

  def test_create_geometry(self):
    my_object = self._create_object_proto(
        name='foo', object_id='23', world_id='world'
    )
    self._stub.CreateObject.return_value = my_object
    world_client = object_world_client.ObjectWorldClient(
        'world', self._stub, self._geometry_service_stub
    )
    world_client.create_geometry_object(
        object_name='foo',
        geometry_component=geometry_component_pb2.GeometryComponent(),
    )

  def test_create_geometry_object_with_user_data(self):
    my_user_data_any = any_pb2.Any()
    my_user_data_any.Pack(wrappers_pb2.StringValue(value='my_value'))
    my_object = self._create_object_proto(
        name='bar',
        object_id='79',
        world_id='world',
        user_data={'my_key': my_user_data_any},
    )
    self._stub.CreateObject.return_value = my_object
    world_client = object_world_client.ObjectWorldClient(
        'world', self._stub, self._geometry_service_stub
    )
    world_client.create_geometry_object(
        object_name='bar',
        geometry_component=geometry_component_pb2.GeometryComponent(),
        user_data={'my_key': my_user_data_any},
    )

  def test_create_object_from_product_part(self):
    my_object = self._create_object_proto(
        name='foo', object_id='23', world_id='world'
    )
    self._stub.CreateObject.return_value = my_object
    world_client = object_world_client.ObjectWorldClient(
        'world', self._stub, self._geometry_service_stub
    )
    world_client.create_object_from_product(
        product_name='my_product',
        product_metadata=struct_pb2.Struct(),
        scene_object=scene_object_pb2.SceneObject(),
        object_name=object_world_ids.WorldObjectName('my_object'),
    )


if __name__ == '__main__':
  absltest.main()
