# Copyright 2023 Intrinsic Innovation LLC

"""Interfaces for grasp planners, proposers, adapters and rankers."""

from __future__ import annotations

import abc
import dataclasses
from typing import Optional, Sequence

from intrinsic.icon.proto import joint_space_pb2
from intrinsic.manipulation.grasping import grasp_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.motion_planning import motion_planner_client
from intrinsic.perception.scene_perception.proto.scene import scene_container_pb2
from intrinsic.world.proto import geometric_constraints_pb2
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.python import object_world_client


@dataclasses.dataclass(frozen=True)
class GraspTarget:
  """A GraspTarget includes the object/type to grasp and the grasp constraint.

  object_category_or_reference: An object category or reference to be grasped.
        If a reference is given, it needs to exist in the object world.
        `object_category` maps to `product_part_name` in `SpawnProductParams`.
  grasp_constraint: The constraint for grasping the target. It is either a
        list of allowed object-inhand poses in the object frame, or a geometric
        constraint related to the grasp pose. We allow the constraint to be a
        list of poses (instead of always a geometric constraint) because the
        object frame may not be known before grasp planning happens, which is
        required in a geometric constraint. This will simplify after
        b/268223585.
  """

  object_category_or_reference: str | object_world_refs_pb2.ObjectReference
  grasp_constraint: (
      Sequence[pose_pb2.Pose]
      | geometric_constraints_pb2.GeometricConstraint
      | None
  ) = None

  def to_proto(self) -> grasp_pb2.GraspTarget:
    """Convert this GraspTarget to a proto."""
    params = {}
    if self.grasp_constraint is not None:
      if isinstance(self.grasp_constraint, list):
        params["grasp_constraint"] = grasp_pb2.GraspTarget.GraspConstraint(
            poses=grasp_pb2.GraspTarget.Poses(poses=self.grasp_constraint)
        )
      elif isinstance(
          self.grasp_constraint, geometric_constraints_pb2.GeometricConstraint
      ):
        params["grasp_constraint"] = grasp_pb2.GraspTarget.GraspConstraint(
            geometric_constraint=self.grasp_constraint
        )
    if isinstance(self.object_category_or_reference, str):
      params["object_category"] = self.object_category_or_reference
    elif isinstance(
        self.object_category_or_reference, object_world_refs_pb2.ObjectReference
    ):
      params["object_reference"] = self.object_category_or_reference
    return grasp_pb2.GraspTarget(**params)

  @classmethod
  def from_proto(cls, proto: grasp_pb2.GraspTarget) -> "GraspTarget":
    """Make a GraspTarget from a proto."""
    grasp_constraint = None
    if proto.HasField("grasp_constraint"):
      grasp_constraint = (
          list(proto.grasp_constraint.poses.poses)
          if proto.grasp_constraint.HasField("poses")
          else proto.grasp_constraint.geometric_constraint
      )
    return cls(
        object_category_or_reference=proto.object_category
        if proto.HasField("object_category")
        else proto.object_reference,
        grasp_constraint=grasp_constraint,
    )

  def __hash__(self):
    if isinstance(self.object_category_or_reference, str):
      return hash(self.object_category_or_reference)
    elif isinstance(
        self.object_category_or_reference, object_world_refs_pb2.ObjectReference
    ):
      if self.object_category_or_reference.HasField("id"):
        return hash(self.object_category_or_reference.id)
      return hash(self.object_category_or_reference.by_name.object_name)


class GraspPlanner(metaclass=abc.ABCMeta):
  """Grasp planner interface.

  To differentiate GraspPlanner and GraspProposer, a proposer only proposes
  grasps without adapting or ranking grasps. A grasp planner usually contains
  a grasp proposer, adapters and rankers.
  """

  @abc.abstractmethod
  def plan_grasps(
      self,
      world: object_world_client.ObjectWorldClient,
      motion_planner: motion_planner_client.MotionPlannerClient,
      workspace_id: str,
      grasp_targets: Sequence[GraspTarget],
      scene: Optional[scene_container_pb2.SceneContainer] = None,
      recent_grasps: Optional[Sequence[grasp_pb2.AttemptedGrasp]] = None,
  ) -> GraspPlan:
    """Plans grasps.

    Assumptions:
      If any `grasp_targets` has an object reference, it needs to exist in the
      object world.
      If any `grasp_targets` has an object categoary, `scene` cannot be None.

    Args:
      world: The object world for getting poses of objects/frames.
      motion_planner: The motion planner for collision, IK checking.
      workspace_id: The ID of the target grasp workspace.
      grasp_targets: A list of grasp targets. If there are multiple, grasping
        any one is allowed.
      scene: The scene associated with the planning event. If None, the planner
        gets detections directly from the object world based on
        "object_categories_or_instances"; otherwise the planner gets detections
        from the scene based on object categories in
        "object_categories_or_instances".
      recent_grasps: A list of recently attempted grasps and whether each one
        succeeded.

    Returns:
      The planned grasps.
    """

  @abc.abstractmethod
  def notify_grasp_results(
      self,
      executed_grasps: Sequence[grasp_pb2.AttemptedGrasp],
  ) -> None:
    """Feeds execution results to the grasp planner.

    So the planner can adapt future plans based on past results.

    Args:
      executed_grasps: The executed grasp results.
    """


class GraspProposer(metaclass=abc.ABCMeta):
  """Grasp proposer interface.

  To differentiate GraspPlanner and GraspProposer, a proposer only proposes
  grasps without adapting or ranking grasps. A grasp planner usually contains
  a grasp proposer, adapters and rankers.
  """

  @abc.abstractmethod
  def propose_grasps(
      self,
      world: object_world_client.ObjectWorldClient,
      motion_planner: motion_planner_client.MotionPlannerClient,
      workspace_id: str,
      grasp_targets: Sequence[GraspTarget],
      scene: Optional[scene_container_pb2.SceneContainer] = None,
  ) -> list[grasp_pb2.Grasp]:
    """Proposes grasps according to the proposer algorithm.

    For example, a pose-based grasp proposer proposes grasps based on poses of
    detected objects in the scene; a plane-based proposer proposes based on
    detected planes.

    Args:
      world: See GraspPlanner.plan_grasps.
      motion_planner: See GraspPlanner.plan_grasps.
      workspace_id: See GraspPlanner.plan_grasps.
      grasp_targets: See GraspPlanner.plan_grasps.
      scene: See GraspPlanner.plan_grasps.

    Returns:
      The proposed grasps.
    """


class GraspAdapter(metaclass=abc.ABCMeta):
  """Grasp adapter interface.

  A grasp adapter extends and adapts a list of grasp candidates.
  """

  @abc.abstractmethod
  def adapt_grasps(
      self,
      grasps: Sequence[grasp_pb2.Grasp],
      world: object_world_client.ObjectWorldClient,
      motion_planner: motion_planner_client.MotionPlannerClient,
      workspace_id: str,
      scene: Optional[scene_container_pb2.SceneContainer] = None,
  ) -> list[grasp_pb2.Grasp]:
    """Adapts grasps according to a heuristic or an algorithm.

    This is to increase the chance of grasping success. An example
    heuristic can be tilting grasps away from workspace boundaries to
    avoid collisions. The output grasps may be a subset/superset/same set of the
    input grasps.

    Args:
      grasps: The candidate grasps.
      world: See GraspPlanner.plan_grasps.
      motion_planner: See GraspPlanner.plan_grasps.
      workspace_id: See GraspPlanner.plan_grasps.
      scene: See GraspPlanner.plan_grasps.

    Returns:
      The adapted grasps.
    """


class GraspRanker(metaclass=abc.ABCMeta):
  """Grasp ranker interface.

  A grasp ranker scores grasp candidates according to some heuristics or
  algorithms.

  Attributes:
    name: Name of the ranker.
  """

  @abc.abstractmethod
  def score_grasp(
      self,
      grasp: grasp_pb2.Grasp,
      world: object_world_client.ObjectWorldClient,
      motion_planner: motion_planner_client.MotionPlannerClient | None,
      recent_grasps: list[tuple[grasp_pb2.Grasp, bool]] | None = None,
  ) -> grasp_pb2.HeuristicResult:
    """Scores a grasp according to the heuristic/algorithm (e.g., IK checks).

    Each ranker has their own scoring heuristics/algorithms. Higher score means
    higher chance of grasping success.

    Args:
      grasp: The candidate grasp.
      world: The object world to use for scoring this grasp.
      motion_planner: The motion planner to use. Can be None if the method
        doesn't use it.
      recent_grasps: Recently executed grasps and their outcomes.

    Returns:
      The heuristic result.
    """

  @property
  @abc.abstractmethod
  def name(self) -> str:
    """Name of the ranker.

    Useful when mapping ranker names to their weights in the overall grasp
    score. We only require name for `GraspRanker` instead of all interfaces,
    since other interfaces don't require such mappings.
    """


@dataclasses.dataclass(frozen=True)
class GraspPlan:
  """Result of a grasp planning behavior.

  This class assumes the following planning procedure:
    - A set of candidate grasps are proposed at an initial stage, and possibly
    adapted.
    - Some set of these grasps are examined, and some are not, according to some
    internal criteria.
    - Some of the examined ones are filtered out.
    - The remaining recommended/unfiltered grasps are ordered by grasp score.

  Attributes:
    filtered_grasps: Candidate grasps that have been filtered out. The order
      doesn't matter. (See class description for more info.)
    grasps: The resulting recommended grasps, ordered by grasp score from high
      to low. This doesn't include unexamined grasps (see class description for
      more info).
    success: True if and only if `grasps` is not empty.
    unexamined_grasps: Candidate grasps that have not been examined. The order
      doesn't matter. (See class description for more info.)
    timing_info: Tracks timing information for propose, adapt, plan and rank.
      time.
    scene_uuid: Scene ID if this grasp plan is computed from a perception scene.
  """

  filtered_grasps: Sequence[grasp_pb2.Grasp]
  grasps: Sequence[grasp_pb2.Grasp]
  unexamined_grasps: Sequence[grasp_pb2.Grasp]
  timing_info: dict[str, float]
  scene_uuid: str | None = None

  @property
  def success(self) -> bool:
    return bool(self.grasps)

  def to_proto(self) -> grasp_pb2.GraspPlan:
    """Converts a GraspPlan to a proto."""
    return grasp_pb2.GraspPlan(
        filtered_grasps=self.filtered_grasps,
        grasps=self.grasps,
        unexamined_grasps=self.unexamined_grasps,
        debug_info=grasp_pb2.GraspPlan.DebugInfo(
            timing_info=self.timing_info, scene_uuid=self.scene_uuid
        ),
    )

  @classmethod
  def from_proto(cls, proto: grasp_pb2.GraspPlan) -> "GraspPlan":
    """Creates a GraspPlan from a proto."""
    params = {
        "filtered_grasps": proto.filtered_grasps,
        "grasps": proto.grasps,
        "unexamined_grasps": proto.unexamined_grasps,
        "timing_info": dict(),
    }
    if proto.HasField("debug_info"):
      params["timing_info"] = dict(proto.debug_info.timing_info)
      if proto.debug_info.HasField("scene_uuid"):
        params["scene_uuid"] = proto.debug_info.scene_uuid
    return cls(**params)


@dataclasses.dataclass(frozen=True)
class GraspExecutionPlan:
  """A grasp execution plan.

  Includes trajectories from starting position to pregrasp, grasp and post
  grasp position in a sequence.

  Attributes:
    traj_to_pregrasp: Trajectory to move from starting position to pregrasp
      position/pose. If None, then traj_to_grasp moves from starting position to
      grasp position/pose via pregrasp position/pose in a single trajectory.
    traj_to_grasp: If traj_to_pregrasp is not None, then this trajectory moves
      from pregrasp position/pose to grasp position/pose; otherwise this moves
      from start to rasp via pregrasp in a single trajectory.
    traj_to_postgrasp: Trajectory to move from grasp position to post
      position/pose.
  """

  traj_to_grasp: joint_space_pb2.JointTrajectoryPVA
  traj_to_postgrasp: joint_space_pb2.JointTrajectoryPVA
  traj_to_pregrasp: joint_space_pb2.JointTrajectoryPVA | None = None

  def to_proto(self) -> grasp_pb2.GraspExecutionPlan:
    params = {
        "traj_to_grasp": self.traj_to_grasp,
        "traj_to_postgrasp": self.traj_to_postgrasp,
    }
    if self.traj_to_pregrasp is not None:
      params["traj_to_pregrasp"] = self.traj_to_pregrasp
    return grasp_pb2.GraspExecutionPlan(**params)

  @classmethod
  def from_proto(
      cls, proto: grasp_pb2.GraspExecutionPlan
  ) -> "GraspExecutionPlan":
    return cls(
        traj_to_pregrasp=proto.traj_to_pregrasp
        if proto.HasField("traj_to_pregrasp")
        else None,
        traj_to_grasp=proto.traj_to_grasp,
        traj_to_postgrasp=proto.traj_to_postgrasp,
    )


@dataclasses.dataclass(frozen=True)
class GraspExecutionPlanningResult:
  """Result of a grasp execution planning.

  Attributes:
    grasp_id: The ID of the grasp that we were asked to plan for.
    plan_or_failure_reason: The actual grasp execution plan if successful, or
      cause of failure otherwise.
    planning_time_in_seconds: The total time took to plan this grasp execution.
    debug_message: Additional information for debugging.
    success: Whether this grasp execution planning is successful or not.
    plan: If planning result is successful, return the plan.
    failure_reason: If planning failed, return the failure reason.
  """

  grasp_id: str
  plan_or_failure_reason: (
      GraspExecutionPlan | grasp_pb2.GraspExecutionPlanningResult.FailureReason
  )
  planning_time_in_seconds: float
  debug_message: str = ""

  @property
  def success(self) -> bool:
    return isinstance(self.plan_or_failure_reason, GraspExecutionPlan)

  @property
  def plan(self) -> GraspExecutionPlan:
    """Returns the grasp execution plan if successful."""
    if not isinstance(self.plan_or_failure_reason, GraspExecutionPlan):
      raise ValueError("Failed execution planning result does not have a plan.")
    return self.plan_or_failure_reason

  @property
  def failure_reason(
      self,
  ) -> grasp_pb2.GraspExecutionPlanningResult.FailureReason:
    """Returns the grasp execution failure reason if not successful."""
    if isinstance(self.plan_or_failure_reason, GraspExecutionPlan):
      raise ValueError(
          "Successful execution planning result does not have a failure reason."
      )
    return self.plan_or_failure_reason

  def to_proto(self) -> grasp_pb2.GraspExecutionPlanningResult:
    params = {
        "grasp_id": self.grasp_id,
        "planning_time_in_seconds": self.planning_time_in_seconds,
        "debug_message": self.debug_message,
    }
    if isinstance(self.plan_or_failure_reason, GraspExecutionPlan):
      params["grasp_execution_plan"] = self.plan_or_failure_reason.to_proto()
    else:
      params["failure_reason"] = self.plan_or_failure_reason
    return grasp_pb2.GraspExecutionPlanningResult(**params)

  @classmethod
  def from_proto(
      cls, proto: grasp_pb2.GraspExecutionPlanningResult
  ) -> "GraspExecutionPlanningResult":
    if proto.HasField("grasp_execution_plan"):
      plan_or_failure_reason = GraspExecutionPlan.from_proto(
          proto.grasp_execution_plan
      )
    else:
      plan_or_failure_reason = proto.failure_reason
    return cls(
        grasp_id=proto.grasp_id,
        plan_or_failure_reason=plan_or_failure_reason,
        planning_time_in_seconds=proto.planning_time_in_seconds,
        debug_message=proto.debug_message
        if proto.HasField("debug_message")
        else "",
    )
