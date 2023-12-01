# Copyright 2023 Intrinsic Innovation LLC

"""Pose estimator access within the workcell API."""

import datetime
from typing import Dict, List, Optional

from intrinsic.perception.proto import pose_estimator_id_pb2
from intrinsic.resources.client import resource_registry_client
from intrinsic.solutions import ipython
from intrinsic.util.grpc import error_handling


_CSS_FAILURE_STYLE = (
    'color: #ab0000; font-family: monospace; font-weight: bold; '
    'padding-left: var(--jp-code-padding);'
)
_LAST_RESULT_TIMEOUT_SECONDS = 5
_POSE_ESTIMATOR_RESOURCE_FAMILY_ID = 'perception_model'


class PoseEstimators:
  """Convenience wrapper for pose estimator access."""

  _resource_registry: resource_registry_client.ResourceRegistryClient

  def __init__(
      self,
      resource_registry: resource_registry_client.ResourceRegistryClient,
  ):
    # pyformat: disable
    """Initializes all available pose estimator configs.

    Args:
      resource_registry: Client for the resource registry.
    """
    # pyformat: enable

    self._resource_registry = resource_registry

  @error_handling.retry_on_grpc_unavailable
  def _get_pose_estimators(
      self,
  ) -> Dict[str, pose_estimator_id_pb2.PoseEstimatorId]:
    """Query pose estimators.

    Returns:
      A dict of pose estimator ids keyed by resource id.

    Raises:
      status.StatusNotOk: If the grpc request failed (propagates grpc error).
    """
    pose_estimator_resources = (
        self._resource_registry.list_all_resource_instances(
            resource_family_id=_POSE_ESTIMATOR_RESOURCE_FAMILY_ID
        )
    )
    return {
        resource_instance.id: pose_estimator_id_pb2.PoseEstimatorId(
            id=resource_instance.id
        )
        for resource_instance in pose_estimator_resources
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
