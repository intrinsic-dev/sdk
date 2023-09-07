# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.workcell.pose_estimators."""

from unittest import mock

from absl.testing import absltest
from intrinsic.logging.proto import log_item_pb2
from intrinsic.perception.service.proto import pose_estimation_service_pb2
from intrinsic.perception.service.proto import pose_estimation_service_pb2_grpc
from intrinsic.solutions import ipython
from intrinsic.solutions import pose_estimation


class PoseEstimatorsTest(absltest.TestCase):

  def test_lists_pose_estimators(self):
    stub = mock.MagicMock()
    logs = mock.MagicMock()
    with mock.patch.object(
        pose_estimation_service_pb2_grpc,
        "PoseEstimationServiceStub",
        return_value=stub,
    ):
      stub.ListPoseEstimationConfigs.return_value = (
          pose_estimation_service_pb2.ListPoseEstimationConfigsResponse(
              pose_estimator_ids=["pose_estimator_1", "pose_estimator_2"]
          )
      )
      pose_estimators = pose_estimation.PoseEstimators(mock.MagicMock(), logs)

      self.assertLen(pose_estimators, 2)
      self.assertEqual(
          str(pose_estimators), "pose_estimator_1\npose_estimator_2"
      )
      self.assertEqual(pose_estimators.pose_estimator_1.id, "pose_estimator_1")
      self.assertEqual(pose_estimators.pose_estimator_2.id, "pose_estimator_2")


if __name__ == "__main__":
  absltest.main()
