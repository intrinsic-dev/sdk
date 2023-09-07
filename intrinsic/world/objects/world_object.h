// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_WORLD_OBJECTS_WORLD_OBJECT_H_
#define INTRINSIC_WORLD_OBJECTS_WORLD_OBJECT_H_

#include <memory>
#include <optional>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/object_entity_filter.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"
#include "intrinsic/world/proto/object_world_service.pb.h"

namespace intrinsic {
namespace world {

// A local copy of an object in a remote world.
//
// Each world consists of a hierarchy of objects, topped by the virtual "root"
// object which is always present. Some objects can have special properties and
// functionalities (see KinematicObject).
//
// Effectively, this is a convenience wrapper around an immutable
// intrinsic_proto::world::Object.
class WorldObject : public TransformNode {
 public:
  // Creates a new instance from the given proto. The caller must ensure that
  // the object is either the root object or has a set 'object_component' (i.e.,
  // it was retrieved with an apppropriately detailed ObjectView).
  static absl::StatusOr<WorldObject> Create(
      intrinsic_proto::world::Object proto);

  // Returns the given TransformNode "downcasted" to a WorldObject or returns
  // std::nullopt if the given TransformNode is not a world object.
  static std::optional<WorldObject> FromTransformNode(
      const TransformNode& node);

  // Returns any instance of a subclass as a WorldObject.
  WorldObject AsWorldObject();

  // Returns the name of this object which is unique within the world.
  WorldObjectName Name() const;

  // Returns the id of the parent object.
  ObjectWorldResourceId ParentId() const;

  // Returns the name of the parent object.
  WorldObjectName ParentName() const;

  // Returns the ids of the child objects.
  std::vector<ObjectWorldResourceId> ChildIds() const;

  // Returns the names of the child objects.
  std::vector<WorldObjectName> ChildNames() const;

  // Returns the ids of all frames under this object, including ones that are
  // attached indirectly to this object via another frame.
  std::vector<ObjectWorldResourceId> FrameIds() const;

  // Returns the names of all frames under this object, including ones that are
  // attached indirectly to this object via another frame.
  std::vector<FrameName> FrameNames() const;

  // Returns all frames under this object, including ones that are attached
  // indirectly to this object via another frame.
  std::vector<Frame> Frames() const;

  // Returns the frame with the given name under this object. Returns an error
  // if no such frame exists.
  absl::StatusOr<Frame> GetFrame(const FrameName& name) const;

  // Returns the ids of all immediate child frames of this object, excluding
  // ones that are attached indirectly to this object via another frame.
  std::vector<ObjectWorldResourceId> ChildFrameIds() const;

  // Returns the names of all immediate child frames of this object, excluding
  // ones that are attached indirectly to this object via another frame.
  std::vector<FrameName> ChildFrameNames() const;

  // Returns all immediate child frames of this object, excluding ones that are
  // attached indirectly to this object via another frame.
  std::vector<Frame> ChildFrames() const;

  // Returns a reference to this object as an ObjectReference. If you need a
  // more a more general reference to a frame *or* object, see
  // TransformNode::TransformNodeReference().
  intrinsic_proto::world::ObjectReference ObjectReference() const;

  // Returns a reference to this object as an ObjectReference with the
  // appropriate filter set.
  intrinsic_proto::world::ObjectReferenceWithEntityFilter
  ObjectReferenceWithEntityFilter(const ObjectEntityFilter& filter) const;

  // Returns the underlying object proto.
  const intrinsic_proto::world::Object& Proto() const;

 protected:
  class Data : public TransformNode::Data {
   public:
    explicit Data(intrinsic_proto::world::Object proto,
                  const Pose3d& parent_t_this, std::vector<Frame> frames);
    ObjectWorldResourceId Id() const override;
    Pose3d ParentTThis() const override;
    intrinsic_proto::world::TransformNodeReference TransformNodeReference()
        const override;

    const intrinsic_proto::world::Object& Proto() const;
    const std::vector<Frame>& Frames() const;

   private:
    intrinsic_proto::world::Object proto_;
    Pose3d parent_t_this_;
    std::vector<Frame> frames_;
  };

  static absl::StatusOr<std::shared_ptr<const Data>> CreateWorldObjectData(
      intrinsic_proto::world::Object proto);

  explicit WorldObject(std::shared_ptr<const Data> data);

  const Data& GetData() const;
};

}  // namespace world
}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_OBJECTS_WORLD_OBJECT_H_
