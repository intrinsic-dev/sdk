# Copyright 2023 Intrinsic Innovation LLC

"""Defines the MotionPlannerClient class.

The MotionPlannerClient provides access to computations on top of the world.
This includes:
  * IK/FK
  * path planning
"""

import dataclasses
from typing import List, Optional

# This import is required to use the *_grpc imports.
# pylint: disable=unused-import
import grpc

from google.protobuf import empty_pb2
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.motion_planning.proto import motion_planner_config_pb2
from intrinsic.motion_planning.proto import motion_planner_service_pb2
from intrinsic.motion_planning.proto import motion_planner_service_pb2_grpc
from intrinsic.motion_planning.proto import motion_specification_pb2
from intrinsic.motion_planning.proto import motion_target_pb2
from intrinsic.motion_planning.proto import robot_specification_pb2
from intrinsic.world.proto import collision_settings_pb2
from intrinsic.world.proto import geometric_constraints_pb2
from intrinsic.world.python import object_world_ids


def _repeated_vec_to_list_of_floats(
    vectors: List[joint_space_pb2.JointVec],
) -> List[List[float]]:
  return [list(vector.joints) for vector in vectors]


@dataclasses.dataclass
class CheckCollisionsOptions:
  """Options for Collision settings.

  Attributes:
    collision_settings: Settings for collision checking.
  """

  collision_settings: collision_settings_pb2.CollisionSettings | None = None


@dataclasses.dataclass
class IKOptions:
  """Options for IK.

  Attributes:
    max_num_solutions: The maximum number of solutions to be returned from IK
      computation. If not set (== 0), the underlying implementation has the
      freedom to choose. Negative values are invalid.
    starting_joints: The starting joint configuration to use. If not set, the
      current position of the robot in the world will be used.
    collision_settings: Collision Settings. If left empty, no collision checking
      is done.
    ensure_same_branch: Flag to choose IK solution is on the same kinematic
      branch as the starting joints of the robot.
    prefer_same_branch:  Flag that will prefer solutions on the same kinematic
      branch over those close to the starting_joints configuration.
  """

  max_num_solutions: int = 0
  starting_joints: list[float] | None = None
  collision_settings: collision_settings_pb2.CollisionSettings | None = None
  ensure_same_branch: bool = False
  prefer_same_branch: bool = False


@dataclasses.dataclass
class MotionPlanningOptions:
  """Options for Motion Planning.

  Attributes:
    path_planning_time_out: Timeout for path planning algorithms.
    lock_motion_configuration: Optional configuration for saving or loading a
      motion.
  """

  path_planning_time_out: int = 30
  lock_motion_configuration: (
      motion_planner_config_pb2.LockMotionConfiguration | None
  ) = None


class MotionPlannerClient:
  """Helper class for calling the rpcs in the MotionPlannerService.

  Provides additional computations on top of the world.
    * IK/FK
    * Path planning
  """

  def __init__(
      self,
      world_id: str,
      stub: motion_planner_service_pb2_grpc.MotionPlannerServiceStub,
  ):
    self._world_id: str = world_id
    self._stub: motion_planner_service_pb2_grpc.MotionPlannerServiceStub = stub

  def plan_trajectory(
      self,
      robot_specification: robot_specification_pb2.RobotSpecification,
      motion_specification: motion_specification_pb2.MotionSpecification,
      options: MotionPlanningOptions = MotionPlanningOptions(),
      caller_id: str = "Anonymous",
  ) -> joint_space_pb2.JointTrajectoryPVA:
    """Plan trajectory for a given motion planning problem and robot.

    This method calls the Plan trajectory rpc.

    Args:
      robot_specification: Robot specification
      motion_specification: Motion specification, see MotionSpecification proto.
      options: Motion planning options that allows the path planning timeout to
        be set.
      caller_id: The id used for logging the request in the motion planner
        service.

    Returns:
      Discretized trajectory
    """
    request = motion_planner_service_pb2.MotionPlanningRequest(
        world_id=self._world_id,
        robot_specification=robot_specification,
        motion_specification=motion_specification,
        caller_id=caller_id,
    )
    request.motion_planner_config.timeout_sec.seconds = (
        options.path_planning_time_out
    )
    if options.lock_motion_configuration:
      request.motion_planner_config.lock_motion_configuration.CopyFrom(
          options.lock_motion_configuration
      )
    response = self._stub.PlanTrajectory(request)
    return response.discretized

  def compute_ik(
      self,
      robot_name: object_world_ids.WorldObjectName,
      target: (
          motion_target_pb2.CartesianMotionTarget
          | geometric_constraints_pb2.GeometricConstraint
      ),
      starting_joints: Optional[List[float]] = None,
      options: Optional[IKOptions] = None,
  ) -> List[List[float]]:
    """Calls the ComputeIk rpc, doing argument conversion as necessary.

    Args:
      robot_name: Name of robot, must map to a kinematic object
      target: a target pose to compute ik for
      starting_joints: used as seed for ik, optional
      options: See IKOptions.

    Returns:
      A list of IK solutions
    """
    request = motion_planner_service_pb2.IkRequest(world_id=self._world_id)
    request.robot_reference.object_id.by_name.object_name = robot_name

    # Convert CartesianMotionTarget to GeometricConstraint::PoseEquality.
    if isinstance(target, motion_target_pb2.CartesianMotionTarget):
      request.target.pose_equality.moving_frame.CopyFrom(target.tool)
      request.target.pose_equality.target_frame.CopyFrom(target.frame)
      if target.HasField("offset"):
        request.target.pose_equality.target_frame_offset.CopyFrom(target.offset)
    else:
      request.target.CopyFrom(target)

    if starting_joints is not None:
      request.starting_joints.joints.extend(starting_joints)
    if options is not None:
      if options.collision_settings:
        request.collision_settings.CopyFrom(options.collision_settings)
      if options.ensure_same_branch:
        request.ensure_same_branch = options.ensure_same_branch
      if options.prefer_same_branch:
        request.prefer_same_branch = options.prefer_same_branch
      if options.max_num_solutions:
        request.max_num_solutions = options.max_num_solutions

    # Make the rpc.
    response = self._stub.ComputeIk(request)
    return _repeated_vec_to_list_of_floats(response.solutions)

  def compute_fk(
      self,
      robot_name: object_world_ids.WorldObjectName,
      joints: List[float],
      reference: object_world_ids.WorldObjectName,
      target: object_world_ids.WorldObjectName,
      reference_frame: Optional[object_world_ids.FrameName] = None,
      target_frame: Optional[object_world_ids.FrameName] = None,
  ) -> data_types.Pose3:
    """Calls the ComputeIk rpc, doing argument conversion as necessary.

    If reference_frame is not specified, the WorldObject 'reference' will be
    used directly. The same applies for target_frame/target.

    Args:
      robot_name: Name of robot, must map to a kinematic object
      joints: the joint configuration values to compute fk for
      reference: object name for the reference of the returned pose
      target: object name for the target of the returned pose
      reference_frame: name that specifies a frame under 'reference', optional
      target_frame: name that specifies a frame under 'target', optional

    Returns:
      The reference_t_target pose, i.e. the pose of 'target' in the frame of
      'reference'
    """
    request = motion_planner_service_pb2.FkRequest(world_id=self._world_id)
    request.robot_reference.object_id.by_name.object_name = robot_name
    request.joints.joints.extend(joints)
    if reference_frame is not None:
      # If frame is not None, then we'll assume the user is specifying a frame,
      # and otherwise the user is specifying an object.
      request.reference.by_name.frame.object_name = reference
      request.reference.by_name.frame.frame_name = reference_frame
    else:
      request.reference.by_name.object.object_name = reference
    if target_frame is not None:
      # If frame is not None, then we'll assume the user is specifying a frame,
      # and otherwise the user is specifying an object.
      request.target.by_name.frame.object_name = target
      request.target.by_name.frame.frame_name = target_frame
    else:
      request.target.by_name.object.object_name = target

    # Make the rpc.
    response = self._stub.ComputeFk(request)
    return math_proto_conversion.pose_from_proto(response.reference_t_target)

  def check_collisions(
      self,
      robot_name: object_world_ids.WorldObjectName,
      waypoints: list[joint_space_pb2.JointVec],
      options: CheckCollisionsOptions,
  ) -> motion_planner_service_pb2.CheckCollisionsResponse:
    """Calls the CheckCollisions rpc.

    Args:
      robot_name: Name of robot, must map to a kinematic object.
      waypoints: The waypoints define the path for which we check the collision.
        We also check the linear interpolation between the waypoints.
      options: Check collision options

    Returns:
      CheckCollisionResponse. See flag `has_collision` in response
      which indicates a collision.
    """

    request = motion_planner_service_pb2.CheckCollisionsRequest(
        world_id=self._world_id,
        robot_reference=robot_specification_pb2.RobotReference(),
        waypoint=waypoints,
        collision_settings=options.collision_settings,
    )
    request.robot_reference.object_id.by_name.object_name = robot_name
    response = self._stub.CheckCollisions(request)
    return response

  def clear_cache(self) -> empty_pb2.Empty:
    """Calls the ClearCache rpc."""
    return self._stub.ClearCache(empty_pb2.Empty())
