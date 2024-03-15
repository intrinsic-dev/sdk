# Copyright 2023 Intrinsic Innovation LLC

from unittest import mock

from absl.testing import absltest
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.solutions import provided
from intrinsic.solutions.internal import resources as resources_mod


class ResourcesTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._resource_registry_client = mock.MagicMock()

  def test_dir_resources(self):
    self._resource_registry_client.list_all_resource_handles.return_value = [
        resource_handle_pb2.ResourceHandle(name='my_camera'),
        resource_handle_pb2.ResourceHandle(name='my_robot'),
    ]
    resources = resources_mod.Resources(self._resource_registry_client)

    self.assertEqual(dir(resources), ['my_camera', 'my_robot'])

  def test_dir_resources_with_special_characters_in_name(self):
    self._resource_registry_client.list_all_resource_handles.return_value = [
        resource_handle_pb2.ResourceHandle(name='some!strange+name'),
    ]
    resources = resources_mod.Resources(self._resource_registry_client)

    # Test dir() only returns cleaned names.
    self.assertEqual(dir(resources), ['some_strange_name'])

    # Test we can access the resource with the original and the cleaned name
    self.assertEqual(resources['some!strange+name'].name, 'some!strange+name')
    self.assertEqual(resources['some_strange_name'].name, 'some!strange+name')

  def test_resource_handle_repr(self):
    """Tests proper repr() implementation."""
    handle = provided.ResourceHandle.create('Foo', ['type1', 'type2'])

    self.assertEqual(
        repr(handle),
        'ResourceHandle.create(name="Foo", types=["type1", "type2"])',
    )


if __name__ == '__main__':
  absltest.main()
