// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_OBJECTS_KINEMATIC_OBJECT_H_
#define INTRINSIC_WORLD_OBJECTS_KINEMATIC_OBJECT_H_

#include <memory>
#include <optional>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/kinematics/types/cartesian_limits.h"
#include "intrinsic/kinematics/types/joint_limits_xd.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/objects/world_object.h"
#include "intrinsic/world/proto/object_world_service.pb.h"

namespace intrinsic {
namespace world {

// A local copy of an object in a remote world that has movable joints.
//
// Can represent an actuated robot, but can also represent, e.g., finger
// grippers or fixtures with moveable clamps.
//
// Effectively, this is a convenience wrapper around an immutable
// intrinsic_proto::world::Object which has a KinematicObjectComponent and
// type==KINEMATIC_OBJECT.
class KinematicObject : public WorldObject {
 public:
  // Creates a new instance from the given proto. The caller must ensure that
  // the object has 'type'==ObjectType::KINEMATIC_OBJECT and has a set
  // 'kinematic_object_component' (i.e., it was retrieved with an apppropriately
  // detailed ObjectView).
  static absl::StatusOr<KinematicObject> Create(
      intrinsic_proto::world::Object proto);

  // Returns the given TransformNode "downcasted" to a KinematicObject or
  // returns std::nullopt if the given TransformNode is not a kinematic object.
  static std::optional<KinematicObject> FromTransformNode(
      const TransformNode& node);

  // Returns the joint positions in radians (for revolute joints) or meters
  // (for prismatic joints).
  eigenmath::VectorXd JointPositions() const;

  // Returns the system joint limits.
  const JointLimitsXd& JointSystemLimits() const;

  // Returns the application joint limits.
  const JointLimitsXd& JointApplicationLimits() const;

  // Returns the frames (or their ids/names) on this kinematic object which mark
  // flanges according to the ISO 9787 standard. Not every kinematic object has
  // flange frames, but callers can expect this method to return one flange
  // frame for every "robot arm" contained in the kinematic object.
  std::vector<ObjectWorldResourceId> IsoFlangeFrameIds() const;
  std::vector<FrameName> IsoFlangeFrameNames() const;
  std::vector<Frame> IsoFlangeFrames() const;

  // If IsoFlangeFrames() returns exactly one flange frame, returns this flange
  // frame. Otherwise returns an error.
  absl::StatusOr<Frame> GetSingleIsoFlangeFrame() const;

  // Gets the cartesian limits for this kinematic object.
  absl::StatusOr<intrinsic::CartesianLimits> GetCartesianLimits() const;

  // Gets the current control frequency in hertz if it exists, nullopt
  // otherwise.
  absl::StatusOr<std::optional<double>> GetControlFrequencyHz() const;

 private:
  class Data final : public WorldObject::Data {
   public:
    Data(WorldObject::Data data, JointLimitsXd joint_system_limits,
         JointLimitsXd joint_application_limits,
         intrinsic::CartesianLimits cartesian_limits,
         std::optional<double> control_frequency_hz);

    const JointLimitsXd& JointSystemLimits() const;
    const JointLimitsXd& JointApplicationLimits() const;
    const intrinsic::CartesianLimits& CartesianLimits() const;
    const std::optional<double>& ControlFrequencyHz() const;

   private:
    JointLimitsXd joint_system_limits_;
    JointLimitsXd joint_application_limits_;
    intrinsic::CartesianLimits cartesian_limits_;
    std::optional<double> control_frequency_hz_;
  };

  explicit KinematicObject(std::shared_ptr<const Data> data);

  const Data& GetData() const;
};

}  // namespace world
}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_OBJECTS_KINEMATIC_OBJECT_H_
