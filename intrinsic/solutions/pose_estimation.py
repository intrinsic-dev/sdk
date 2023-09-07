# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Pose estimator access within the workcell API."""

import datetime
from typing import Dict, List, Optional

from google.protobuf import empty_pb2
import grpc
from intrinsic.perception.proto import pose_estimator_id_pb2
from intrinsic.perception.service.proto import pose_estimation_service_pb2
from intrinsic.perception.service.proto import pose_estimation_service_pb2_grpc
from intrinsic.solutions import ipython
from intrinsic.solutions import structured_logging
from intrinsic.util.grpc import error_handling


_CSS_FAILURE_STYLE = (
    'color: #ab0000; font-family: monospace; font-weight: bold; '
    'padding-left: var(--jp-code-padding);'
)
_LAST_RESULT_TIMEOUT_SECONDS = 5


@error_handling.retry_on_grpc_unavailable
def _list_pose_estimator_configs(
    stub: pose_estimation_service_pb2_grpc.PoseEstimationServiceStub,
) -> pose_estimation_service_pb2.ListPoseEstimationConfigsResponse:
  return stub.ListPoseEstimationConfigs(empty_pb2.Empty())


class PoseEstimators:
  """Convenience wrapper for pose estimator access."""

  def __init__(
      self, grpc_channel: grpc.Channel, logs: structured_logging.StructuredLogs
  ):
    """Initializes all available pose estimator configs.

    Args:
      grpc_channel: gRPC channel to the intrinsic Box.
      logs: Structured logs containing annotated frames.
    """

    self._stub = pose_estimation_service_pb2_grpc.PoseEstimationServiceStub(
        grpc_channel
    )
    self._logs = logs

  def show_last_result(self, width: Optional[int] = None) -> None:
    """Queries newest annotated frame and shows it.

    Args:
      width: Optional width of shown image in pixels.
    """
    deadline = datetime.datetime.now() + datetime.timedelta(
        seconds=_LAST_RESULT_TIMEOUT_SECONDS
    )
    while datetime.datetime.now() < deadline:
      try:
        result = self._logs.perception_frames_annotated.peek()
        ipython.display_image_if_ipython(
            data=result.blob_payload.data, width=width
        )
        return
      except AttributeError:
        # We allow an attribute error to pass. For details see b/276282357.
        continue

    message = (
        'No annotated frame found within'
        f' {_LAST_RESULT_TIMEOUT_SECONDS} seconds. Please try again, as logging'
        ' is asynchronous and hence may take a while.'
    )
    ipython.display_html_or_print_msg(
        f'<span style="{_CSS_FAILURE_STYLE}">{message}</span>', message
    )

  def _get_pose_estimators(
      self,
  ) -> Dict[str, pose_estimator_id_pb2.PoseEstimatorId]:
    """Query pose estimators.

    Returns:
      A dict of pose estimator ids keyed by resource id.

    Raises:
      status.StatusNotOk: If the grpc request failed (propagates grpc error).
    """
    pose_estimator_ids = _list_pose_estimator_configs(
        self._stub
    ).pose_estimator_ids
    return {
        p: pose_estimator_id_pb2.PoseEstimatorId(id=p)
        for p in pose_estimator_ids
    }

  def __getattr__(
      self, pose_estimator_id: str
  ) -> pose_estimator_id_pb2.PoseEstimatorId:
    """Returns the id of the pose estimator.

    Args:
      pose_estimator_id: Resource id of the pose estimator.

    Returns:
      Pose estimator id.

    Raises:
      AttributeError: if there is no pose estimator resource id with the given
      name.
    """
    pose_estimators = self._get_pose_estimators()
    if pose_estimator_id not in pose_estimators:
      raise AttributeError(f'Pose estimator {pose_estimator_id} is unknown')
    return pose_estimators[pose_estimator_id]

  def __len__(self) -> int:
    """Returns the number of pose estimators."""
    return len(self._get_pose_estimators())

  def __str__(self) -> str:
    """Concatenates all pose estimator config paths into a string."""
    return '\n'.join(sorted(self._get_pose_estimators().keys()))

  def __dir__(self) -> List[str]:
    """Lists all pose estimators by key (sorted)."""
    return sorted(list(self._get_pose_estimators().keys()))

  def __getitem__(
      self, pose_estimator_id: str
  ) -> pose_estimator_id_pb2.PoseEstimatorId:
    """Returns the id of the pose estimator.

    Args:
      pose_estimator_id: Resource id of the pose estimator.

    Returns:
      Pose estimator id.

    Raises:
      AttributeError: if there is no pose estimator resource id with the given
      name.
    """
    return self._get_pose_estimators()[pose_estimator_id]
