# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.skills.python.skill_registry_client."""

from unittest import mock

from absl.testing import absltest
from intrinsic.resources.client import resource_registry_client
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.resources.proto import resource_registry_pb2


class ResourceRegistryClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()

    self._resource_registry_stub = mock.MagicMock()
    self._client = resource_registry_client.ResourceRegistryClient(
        self._resource_registry_stub
    )

  def test_get_resource_instance(self):
    camera_instance = resource_registry_pb2.ResourceInstance(
        id='my_camera', resource_family_id='camera'
    )
    self._resource_registry_stub.GetResourceInstance.return_value = (
        camera_instance
    )

    self.assertEqual(
        self._client.get_resource_instance('my_camera'),
        camera_instance,
    )
    self._resource_registry_stub.GetResourceInstance.assert_called_with(
        resource_registry_pb2.GetResourceInstanceRequest(id='my_camera')
    )

  def test_list_all_resource_instances(self):
    camera_instance = resource_registry_pb2.ResourceInstance(
        id='my_camera', resource_family_id='camera'
    )
    robot_instance = resource_registry_pb2.ResourceInstance(
        id='my_robot', resource_family_id='robot'
    )
    self._resource_registry_stub.ListResourceInstances.return_value = (
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[
                camera_instance,
                robot_instance,
            ],
        )
    )

    self.assertEqual(
        self._client.list_all_resource_instances(),
        [camera_instance, robot_instance],
    )
    self._resource_registry_stub.ListResourceInstances.assert_called_with(
        resource_registry_pb2.ListResourceInstanceRequest(
            page_size=resource_registry_client._RESOURCE_REGISTRY_MAX_PAGE_SIZE
        )
    )

  def test_list_all_resource_instances_paged(self):
    camera_instance = resource_registry_pb2.ResourceInstance(
        id='my_camera', resource_family_id='camera'
    )
    robot_instance = resource_registry_pb2.ResourceInstance(
        id='my_robot', resource_family_id='robot'
    )
    self._resource_registry_stub.ListResourceInstances.side_effect = [
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[camera_instance],
            next_page_token='the_next_page',
        ),
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[robot_instance],
            next_page_token=None,
        ),
    ]

    result = self._client.list_all_resource_instances()

    self._resource_registry_stub.ListResourceInstances.assert_called_with(
        resource_registry_pb2.ListResourceInstanceRequest(
            page_size=resource_registry_client._RESOURCE_REGISTRY_MAX_PAGE_SIZE,
            page_token='the_next_page',
        )
    )
    self.assertEqual(result, [camera_instance, robot_instance])

  def test_list_all_resource_instances_with_family_filter(self):
    model_instance = resource_registry_pb2.ResourceInstance(
        id='my_model', resource_family_id='perception_model'
    )
    other_model_instance = resource_registry_pb2.ResourceInstance(
        id='my_other_model', resource_family_id='perception_model'
    )

    self._resource_registry_stub.ListResourceInstances.return_value = (
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[
                model_instance,
                other_model_instance,
            ],
        )
    )

    self.assertEqual(
        self._client.list_all_resource_instances(
            resource_family_id='perception_model'
        ),
        [model_instance, other_model_instance],
    )
    self._resource_registry_stub.ListResourceInstances.assert_called_with(
        resource_registry_pb2.ListResourceInstanceRequest(
            page_size=resource_registry_client._RESOURCE_REGISTRY_MAX_PAGE_SIZE,
            strict_filter=resource_registry_pb2.ListResourceInstanceRequest.StrictFilter(
                resource_family_id='perception_model'
            ),
        )
    )

  def test_list_all_resource_handles(self):
    self._resource_registry_stub.ListResourceInstances.return_value = (
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[
                resource_registry_pb2.ResourceInstance(
                    resource_handle=resource_handle_pb2.ResourceHandle(
                        name='my_camera'
                    )
                ),
                resource_registry_pb2.ResourceInstance(
                    resource_handle=resource_handle_pb2.ResourceHandle(
                        name='my_robot'
                    )
                ),
            ],
        )
    )

    result = self._client.list_all_resource_handles()

    self.assertEqual(
        result,
        [
            resource_handle_pb2.ResourceHandle(name='my_camera'),
            resource_handle_pb2.ResourceHandle(name='my_robot'),
        ],
    )

  def test_list_all_resource_handles_with_capabilities_filter(self):
    my_robot_handle = resource_handle_pb2.ResourceHandle(
        name='my_robot',
        resource_data={
            'RobotApi': resource_handle_pb2.ResourceHandle.ResourceData(),
            'GripperApi': resource_handle_pb2.ResourceHandle.ResourceData(),
        },
    )
    self._resource_registry_stub.ListResourceInstances.return_value = (
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[
                resource_registry_pb2.ResourceInstance(
                    resource_handle=my_robot_handle,
                ),
            ],
        )
    )

    result = self._client.list_all_resource_handles(
        capability_names=['RobotApi', 'GripperApi']
    )

    self._resource_registry_stub.ListResourceInstances.assert_called_with(
        resource_registry_pb2.ListResourceInstanceRequest(
            page_size=resource_registry_client._RESOURCE_REGISTRY_MAX_PAGE_SIZE,
            strict_filter=(
                resource_registry_pb2.ListResourceInstanceRequest.StrictFilter(
                    capability_names=['RobotApi', 'GripperApi']
                )
            ),
        )
    )
    self.assertEqual(result, [my_robot_handle])

  def test_batch_list_all_resource_handles(self):
    my_robot_and_gripper_handle = resource_handle_pb2.ResourceHandle(
        name='my_robot_and_gripper',
        resource_data={
            'RobotApi': resource_handle_pb2.ResourceHandle.ResourceData(),
            'GripperApi': resource_handle_pb2.ResourceHandle.ResourceData(),
        },
    )
    my_robot_handle = resource_handle_pb2.ResourceHandle(
        name='my_robot',
        resource_data={
            'RobotApi': resource_handle_pb2.ResourceHandle.ResourceData(),
            'SpeakerApi': resource_handle_pb2.ResourceHandle.ResourceData(),
        },
    )
    my_camera_handle = resource_handle_pb2.ResourceHandle(
        name='my_camera',
        resource_data={
            'CameraApi': resource_handle_pb2.ResourceHandle.ResourceData(),
        },
    )
    self._resource_registry_stub.ListResourceInstances.return_value = (
        resource_registry_pb2.ListResourceInstanceResponse(
            instances=[
                resource_registry_pb2.ResourceInstance(
                    resource_handle=my_robot_and_gripper_handle,
                ),
                resource_registry_pb2.ResourceInstance(
                    resource_handle=my_robot_handle,
                ),
                resource_registry_pb2.ResourceInstance(
                    resource_handle=my_camera_handle,
                ),
            ],
        )
    )

    result = self._client.batch_list_all_resource_handles(
        capability_names_batch=[
            ['RobotApi'],
            ['RobotApi', 'GripperApi'],
            ['ApiWhichIsNotSupportedByAnyResource'],
        ]
    )

    self.assertEqual(
        result,
        [
            [my_robot_and_gripper_handle, my_robot_handle],
            [my_robot_and_gripper_handle],
            [],
        ],
    )

  def test_batch_list_all_resource_handles_with_empty_batch(self):
    result = self._client.batch_list_all_resource_handles(
        capability_names_batch=[]
    )

    self.assertEqual(result, [])
    self._resource_registry_stub.ListResourceInstances.assert_not_called()


if __name__ == '__main__':
  absltest.main()
