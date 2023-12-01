# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.executive.jupyter.workcell.pose_estimators."""

from unittest import mock

from absl.testing import absltest
from intrinsic.resources.proto import resource_registry_pb2
from intrinsic.solutions import pose_estimation


class PoseEstimatorsTest(absltest.TestCase):

  def test_lists_pose_estimators(self):
    resource_registry_client = mock.MagicMock()
    resource_registry_client.list_all_resource_instances.return_value = [
        resource_registry_pb2.ResourceInstance(id="pose_estimator_1"),
        resource_registry_pb2.ResourceInstance(id="pose_estimator_2"),
    ]

    pose_estimators = pose_estimation.PoseEstimators(
        resource_registry_client,
    )

    self.assertLen(pose_estimators, 2)
    self.assertEqual(str(pose_estimators), "pose_estimator_1\npose_estimator_2")
    self.assertEqual(pose_estimators.pose_estimator_1.id, "pose_estimator_1")
    self.assertEqual(pose_estimators.pose_estimator_2.id, "pose_estimator_2")
    resource_registry_client.list_all_resource_instances.assert_called_with(
        resource_family_id=pose_estimation._POSE_ESTIMATOR_RESOURCE_FAMILY_ID
    )


if __name__ == "__main__":
  absltest.main()
