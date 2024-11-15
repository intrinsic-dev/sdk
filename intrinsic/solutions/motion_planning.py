# Copyright 2023 Intrinsic Innovation LLC

"""A wrapper of MotionPlannerClientExternal that is more convenient to use."""

from intrinsic.motion_planning import motion_planner_client
from intrinsic.motion_planning.proto import motion_planner_service_pb2_grpc
from intrinsic.solutions import deployments


class MotionPlannerClient(motion_planner_client.MotionPlannerClientBase):
  """A wrapper of MotionPlannerClientBase that is more convenient to use."""

  @classmethod
  def for_solution(
      cls, solution: deployments.Solution
  ) -> "MotionPlannerClient":
    """Connects to the motion planner gRPC service for a given solution."""
    return cls(
        world_id=solution.world.world_id,
        stub=motion_planner_service_pb2_grpc.MotionPlannerServiceStub(
            solution.grpc_channel
        ),
    )
