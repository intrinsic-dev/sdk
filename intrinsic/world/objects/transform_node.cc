// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/world/objects/transform_node.h"

#include <memory>
#include <utility>

#include "intrinsic/math/pose3.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"

namespace intrinsic {
namespace world {

TransformNode::TransformNode(std::shared_ptr<const Data> data)
    : data_(std::move(data)) {}

TransformNode TransformNode::AsTransformNode() { return TransformNode(data_); }

ObjectWorldResourceId TransformNode::Id() const { return data_->Id(); }

Pose3d TransformNode::ParentTThis() const { return data_->ParentTThis(); }

intrinsic_proto::world::TransformNodeReference
TransformNode::TransformNodeReference() const {
  return data_->TransformNodeReference();
}

const TransformNode::Data& TransformNode::GetData() const { return *data_; }

}  // namespace world
}  // namespace intrinsic
