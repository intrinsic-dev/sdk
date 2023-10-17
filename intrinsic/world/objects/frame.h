// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_OBJECTS_FRAME_H_
#define INTRINSIC_WORLD_OBJECTS_FRAME_H_

#include <memory>
#include <optional>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"
#include "intrinsic/world/proto/object_world_service.pb.h"

namespace intrinsic {
namespace world {

// A local copy of a frame in a remote world.
//
// A frame represents a pose relative to an object. If the parent object is the
// root object, the frame is a "global frame", otherwise the frame is a "local
// frame".
//
// Effectively, this is a convenience wrapper around an immutable
// intrinsic_proto::world::Frame.
class Frame : public TransformNode {
 public:
  // Creates a new instance from the given proto.
  static absl::StatusOr<Frame> Create(intrinsic_proto::world::Frame proto);

  // Returns the given TransformNode "downcasted" to a Frame or returns
  // std::nullopt if the given TransformNode is not a frame.
  static std::optional<Frame> FromTransformNode(const TransformNode& node);

  // Returns the name of this frame which is unique amongst all frames under the
  // same object.
  FrameName Name() const;

  // Returns the id of the parent object of this frame.
  ObjectWorldResourceId ObjectId() const;

  // Returns the name of the parent object of this frame.
  WorldObjectName ObjectName() const;

  // Returns the id of the parent frame to which this frame is attached, or
  // std::nullopt if the frame is attached directly to one of the links of the
  // parent object
  std::optional<ObjectWorldResourceId> ParentFrameId() const;

  // Returns the name of the parent frame to which this frame is attached, or
  // std::nullopt if the frame is attached directly to one of the links of the
  // parent object
  std::optional<FrameName> ParentFrameName() const;

  // Returns the ids of the child frames which have this frame as their parent
  // frame and which are not attached directly to the parent object. The result
  // is not sorted in any particular order.
  std::vector<ObjectWorldResourceId> ChildFrameIds() const;

  // Returns the names of the child frames which have this frame as their parent
  // frame and which are not attached directly to the parent object. The result
  // is not sorted in any particular order.
  std::vector<FrameName> ChildFrameNames() const;

  // Returns a reference to this frame as a FrameReference. If you need a
  // more a more general reference to a frame *or* object, see
  // TransformNode::TransformNodeReference().
  intrinsic_proto::world::FrameReference FrameReference() const;

  bool IsAttachmentFrame() const;

 protected:
  class Data final : public TransformNode::Data {
   public:
    explicit Data(intrinsic_proto::world::Frame proto,
                  const Pose3d& parent_t_this);
    ObjectWorldResourceId Id() const override;
    Pose3d ParentTThis() const override;
    intrinsic_proto::world::TransformNodeReference TransformNodeReference()
        const override;

    const intrinsic_proto::world::Frame& Proto() const;

   private:
    intrinsic_proto::world::Frame proto_;
    Pose3d parent_t_this_;
  };

 private:
  explicit Frame(std::shared_ptr<const Data> data);

  const Data& GetData() const;
};

}  // namespace world
}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_OBJECTS_FRAME_H_
