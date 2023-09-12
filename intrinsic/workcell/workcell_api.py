# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Intrinsic Workcell Python API top-level entry point.

DEPRECATED: We are migrating to a new entry point. Please use
intrinsic.solutions.deployments instead of this module.

See intrinsic/solutions/deployments.py.
"""

from typing import Any, Dict, Optional, Union

import grpc
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2_grpc
from intrinsic.math.python import data_types as intrinsic_types
from intrinsic.perception.proto import hand_eye_calibration_pb2
from intrinsic.skills.apps.calibration import collect_calibration_data_pb2
from intrinsic.skills.apps.calibration import sample_calibration_poses_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import behavior_tree
from intrinsic.solutions import deployments
from intrinsic.solutions import equipment as equipment_mod
from intrinsic.solutions import errors as solution_errors
from intrinsic.solutions import execution
from intrinsic.solutions import perception
from intrinsic.solutions import pose_estimation
from intrinsic.solutions import providers
from intrinsic.solutions import structured_logging
from intrinsic.solutions import utils
from intrinsic.solutions import worlds
from intrinsic.solutions.internal import behavior_call
from intrinsic.world.python import object_world_resources


# pylint: disable=g-doc-args
# pylint: disable=g-doc-return-or-yield
def connect(
    grpc_channel_or_hostport: Optional[Union[grpc.Channel, str]] = None,
    *,
    grpc_channel: Optional[grpc.Channel] = None,
    address: Optional[str] = None,
    project: Optional[str] = None,
    solution: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> deployments.Solution:
  """Connects to executive and registries and return Workcell client.

  DEPRECATED: Instead use
  intrinsic.solutions.deployments.connect.
  """
  solution = deployments.connect(
      grpc_channel_or_hostport=grpc_channel_or_hostport,
      grpc_channel=grpc_channel,
      address=address,
      project=project,
      solution=solution,
      options=options,
  )

  installer_stub = installer_pb2_grpc.InstallerServiceStub(
      solution.grpc_channel
  )
  # pylint: disable-next=protected-access
  solution_status = deployments._get_solution_status_with_retry(installer_stub)
  backend_names = [s.name for s in solution_status.services]

  ## Simple hacks for migrating from the Workcell to the Solution class that
  ## work well in non-type checked code (Jupyter notebooks). Provide callers of
  ## this method with a Workcell-like object.

  # `Workcell.simulation` was renamed to `Solution.simulator`.
  solution.simulation = solution.simulator

  # `Workcell.cameras` has been removed and now has to be created separately
  # from the `Solution` class.
  solution.cameras = None
  if "camera" in backend_names or "camera-sim" in backend_names:
    solution.cameras = perception.Cameras.for_solution(solution)

  return solution


# DEPRECATED: Instead use
# intrinsic.solutions.deployments.create_grpc_channel.
create_grpc_channel = deployments.create_grpc_channel

# Type forwarding, to enable instantiating these without loading the respective
# modules in client code.

Workcell = deployments.Solution
Executive = execution.Executive
Action = behavior_call.Action
BehaviorTree = behavior_tree.BehaviorTree
StructuredLogs = structured_logging.StructuredLogs
EventSourceWindow = structured_logging.EventSourceWindow
Pose3 = intrinsic_types.Pose3
Rotation3 = intrinsic_types.Rotation3
Quaternion = intrinsic_types.Quaternion
vec6_to_pose3 = intrinsic_types.vec6_to_pose3
Error = solution_errors.Error
BackendNoWorkcellError = solution_errors.BackendNoWorkcellError
VectorNdValue = skills_pb2.VectorNdValue
HandEyeCalibrationRequest = hand_eye_calibration_pb2.HandEyeCalibrationRequest
RandomizedBoxParams = sample_calibration_poses_pb2.RandomizedBoxParams
PreCalibrationParams = sample_calibration_poses_pb2.PreCalibrationParams
CalibrationMotionType = collect_calibration_data_pb2.MotionType
SampleCalibrationPosesResult = (
    sample_calibration_poses_pb2.SampleCalibrationPosesResult
)
SkillProvider = providers.SkillProvider
TransformNode = object_world_resources.TransformNode
WorldObject = object_world_resources.WorldObject
KinematicObject = object_world_resources.KinematicObject
Frame = object_world_resources.Frame
JointConfiguration = object_world_resources.JointConfiguration
ObjectWorld = worlds.ObjectWorld
CartesianMotionTarget = worlds.CartesianMotionTarget
PointConstraint = worlds.PointConstraint
PoseConstraint = worlds.PoseConstraint
PoseFreeAxisConstraint = worlds.PoseWithFreeAxisConstraint
PoseConeConstraint = worlds.PoseConeConstraint
PositionEllipsoidConstraint = worlds.PositionEllipsoidConstraint
PositionPlaneConstraint = worlds.PositionPlaneConstraint
JointPositionLimitsConstraint = worlds.JointPositionLimitsConstraint
ConstrainedMotionTarget = worlds.ConstrainedMotionTarget
Constraint = worlds.Constraint
CollisionSettings = worlds.CollisionSettings
PrefixOptions = utils.PrefixOptions
ExecutionFailedError = execution.ExecutionFailedError
PoseEstimators = pose_estimation.PoseEstimators
EquipmentHandle = equipment_mod.EquipmentHandle


class JointMotionTarget(object_world_resources.JointConfiguration):
  """Represents motion targets in joint space.

  DEPRECATED: Use JointConfiguration instead.

  Attributes:
    joint_position: [float] storing the joint position values.
  """
