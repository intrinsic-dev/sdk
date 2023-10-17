// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_OBJECTS_TRANSFORM_NODE_H_
#define INTRINSIC_WORLD_OBJECTS_TRANSFORM_NODE_H_

#include <memory>

#include "intrinsic/math/pose3.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"

namespace intrinsic {
namespace world {

// A resource in the object-based-view onto a remote world that has a pose.
//
// Effectively, this is a convenience wrapper around an immutable object-world
// proto such as intrinsic_proto::world::Object or
// intrinsic_proto::world::Frame.
class TransformNode {
 public:
  // Returns any instance of a subclass as a TransformNode.
  TransformNode AsTransformNode();

  // Returns the unique id of this transform node.
  ObjectWorldResourceId Id() const;

  // Returns the pose of this transform node in the space of the parent
  // objects's origin/base. Returns identity if called on the root object.
  Pose3d ParentTThis() const;

  // Returns a reference to this transform node as a TransformNodeReference. If
  // you need more a more specific reference, see WorldObject::ObjectReference()
  // and Frame::FrameReference().
  intrinsic_proto::world::TransformNodeReference TransformNodeReference() const;

 protected:
  // Abstraction for internal data holders for implementations of TransformNode.
  // Implementations of this interface hold object world resource protos (e.g.
  // Object or Frame).
  class Data {
   public:
    Data() = default;
    virtual ~Data() = default;
    virtual ObjectWorldResourceId Id() const = 0;
    virtual Pose3d ParentTThis() const = 0;
    virtual intrinsic_proto::world::TransformNodeReference
    TransformNodeReference() const = 0;
  };

  explicit TransformNode(std::shared_ptr<const Data> data);

  const Data& GetData() const;

 private:
  // Shared pointer to immutable internal data so that subclasses can be copied
  // safely and efficiently.
  std::shared_ptr<const Data> data_;

  friend class Frame;
  friend class WorldObject;
  friend class KinematicObject;
};

}  // namespace world
}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_OBJECTS_TRANSFORM_NODE_H_
