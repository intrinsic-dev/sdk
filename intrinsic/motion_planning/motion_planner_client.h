// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MOTION_PLANNING_MOTION_PLANNER_CLIENT_H_
#define INTRINSIC_MOTION_PLANNING_MOTION_PLANNER_CLIENT_H_

#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/empty.pb.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/geometry/service/transformed_geometry_storage_refs.pb.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/motion_planning/proto/motion_planner_config.pb.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.grpc.pb.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.pb.h"
#include "intrinsic/motion_planning/proto/motion_specification.pb.h"
#include "intrinsic/motion_planning/proto/motion_target.pb.h"
#include "intrinsic/world/objects/kinematic_object.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/proto/collision_settings.pb.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"

namespace intrinsic {
namespace motion_planning {

// Provides access to the motion planning service for a specific world in the
// world service.
class MotionPlannerClient {
 public:
  // Creates a client for the world with the given id.
  MotionPlannerClient(
      absl::string_view world_id,
      std::shared_ptr<
          intrinsic_proto::motion_planning::MotionPlannerService::StubInterface>
          motion_planner_service);

  // Options for motion planning.
  struct MotionPlanningOptions {
    // Timeout for path planning algorithms.
    double path_planning_time_out = 30;

    // Optionally generate and return the swept volume for the computed path.
    bool compute_swept_volume = false;

    // Optional configuration for saving or loading a motion.
    std::optional<intrinsic_proto::motion_planning::LockMotionConfiguration>
        lock_motion_configuration = std::nullopt;

    // Returns the default set of options to use with the plan path requests.
    static const MotionPlanningOptions& Defaults();
  };

  // Wrapped result from calling PlanTrajectory. Contains both the trajectory
  // and an optional set of shapes that correspond to the swept volume of the
  // trajectory.
  struct PlanTrajectoryResult {
    intrinsic_proto::icon::JointTrajectoryPVA trajectory;
    std::vector<intrinsic_proto::geometry::TransformedGeometryStorageRefs>
        swept_volume;
  };

  // Plans a trajectory for a given motion planning problem and robot.
  // caller_id: The id used for logging the request in the motion planner
  // service.
  absl::StatusOr<PlanTrajectoryResult> PlanTrajectory(
      const intrinsic_proto::motion_planning::RobotSpecification&
          robot_specification,
      const intrinsic_proto::motion_planning::MotionSpecification&
          motion_specification,
      const MotionPlanningOptions& options = MotionPlanningOptions::Defaults(),
      const std::string& caller_id = "Anonymous",
      const intrinsic_proto::data_logger::Context& context =
          intrinsic_proto::data_logger::Context());

  // Options for ik.
  struct IkOptions {
    // The starting joint configuration to use. If empty (=default), the current
    // position of a robot in the world will be used.
    eigenmath::VectorXd starting_joints;

    // The maximum number of solutions to be returned. If not set (== 0), the
    // underlying implementation has the freedom to choose. Negative values are
    // invalid.
    //
    // Choosing a smaller value may make some implementations faster, but this
    // depends on the underlying implementation and is not guaranteed.
    std::optional<int> max_num_solutions;

    // Optional collision settings. Leaving it empty means NO collision
    // checking.
    std::optional<intrinsic_proto::world::CollisionSettings> collision_settings;

    // Optional same branch IK flag. Defaults to false.
    bool ensure_same_branch = false;

    // Optional same branch Ik flag that will prefer solutions on the same
    // kinematic branch over those close to the starting_joint configuration.
    // Defaults to false.
    bool prefer_same_branch = false;
  };

  // Computes inverse kinematics. max_num_solutions = 0 allows the server to
  // pick the number of solutions.
  absl::StatusOr<std::vector<eigenmath::VectorXd>> ComputeIk(
      const world::KinematicObject& robot,
      const intrinsic_proto::motion_planning::CartesianMotionTarget&
          cartesian_target,
      const IkOptions& options = {.ensure_same_branch = false,
                                  .prefer_same_branch = false});

  // Computes inverse kinematics. max_num_solutions = 0 allows the server to
  // pick the number of solutions.
  absl::StatusOr<std::vector<eigenmath::VectorXd>> ComputeIk(
      const world::KinematicObject& robot,
      const intrinsic_proto::world::geometric_constraints::GeometricConstraint&
          geometric_target,
      const IkOptions& options = {.ensure_same_branch = false,
                                  .prefer_same_branch = false});

  // Computes forward kinematics.
  //
  // The returned transform is reference_t_target, i.e. the frame of "target" in
  // the frame of "reference".
  //
  // Typically, some of the joints of the robot should lie in between these
  // two frames, otherwise you wouldn't see any changes to the returned
  // transform.
  //
  // As an example, "reference" could be the base link of a robot, and target
  // might be the robot's end-effector.
  absl::StatusOr<Pose3d> ComputeFk(
      const world::KinematicObject& robot,
      const eigenmath::VectorXd& joint_values,
      const intrinsic_proto::world::TransformNodeReferenceByName& reference,
      const intrinsic_proto::world::TransformNodeReferenceByName& target);
  // Overload for the case where the reference and target are provided in the
  // form of objects retrieved from ObjectWorldClient.
  absl::StatusOr<Pose3d> ComputeFk(const world::KinematicObject& robot,
                                   const eigenmath::VectorXd& joint_values,
                                   const world::TransformNode& reference,
                                   const world::TransformNode& target);
  // Options for check collisions.
  struct CheckCollisionsOptions {
    // Optional collision settings.
    std::optional<intrinsic_proto::world::CollisionSettings> collision_settings;
  };

  // Checks collisions for a given path.
  absl::StatusOr<intrinsic_proto::motion_planning::CheckCollisionsResponse>
  CheckCollisions(const world::KinematicObject& robot,
                  const std::vector<eigenmath::VectorXd>& waypoints,
                  const CheckCollisionsOptions& options = {});

  // Clear the PlanTrajectory caches.
  absl::StatusOr<google::protobuf::Empty> ClearCache();

 private:
  std::string world_id_;
  std::shared_ptr<
      intrinsic_proto::motion_planning::MotionPlannerService::StubInterface>
      motion_planner_service_;
};

}  // namespace motion_planning
}  // namespace intrinsic

#endif  // INTRINSIC_MOTION_PLANNING_MOTION_PLANNER_CLIENT_H_
