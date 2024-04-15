// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/world/objects/world_object.h"

#include <iterator>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/algorithm/container.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/substitute.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/proto_conversion.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/object_entity_filter.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"
#include "intrinsic/world/proto/object_world_service.pb.h"

namespace intrinsic {
namespace world {

absl::StatusOr<std::shared_ptr<const WorldObject::Data>>
WorldObject::CreateWorldObjectData(intrinsic_proto::world::Object proto) {
  Pose3d parent_t_this;
  if (proto.type() != intrinsic_proto::world::ObjectType::ROOT) {
    if (!proto.has_object_component()) {
      return absl::InternalError("Missing object_component");
    }

    INTR_ASSIGN_OR_RETURN(
        parent_t_this,
        intrinsic_proto::FromProto(proto.object_component().parent_t_this()));
  }
  std::vector<Frame> frames;
  frames.reserve(proto.frames_size());
  for (const intrinsic_proto::world::Frame& frame_proto : proto.frames()) {
    INTR_ASSIGN_OR_RETURN(Frame frame, Frame::Create(frame_proto));
    frames.push_back(std::move(frame));
  }
  return std::make_shared<const Data>(std::move(proto), parent_t_this,
                                      std::move(frames));
}

absl::StatusOr<WorldObject> WorldObject::Create(
    intrinsic_proto::world::Object proto) {
  INTR_ASSIGN_OR_RETURN(std::shared_ptr<const Data> data,
                        CreateWorldObjectData(std::move(proto)));
  return WorldObject(std::move(data));
}

std::optional<WorldObject> WorldObject::FromTransformNode(
    const TransformNode& node) {
  std::shared_ptr<const Data> object_data =
      std::dynamic_pointer_cast<const Data>(node.data_);
  return object_data
             ? std::optional<WorldObject>(WorldObject(std::move(object_data)))
             : std::nullopt;
}

WorldObject::WorldObject(std::shared_ptr<const Data> data)
    : TransformNode(std::move(data)) {}

WorldObject WorldObject::AsWorldObject() {
  std::shared_ptr<const Data> data =
      std::dynamic_pointer_cast<const Data>(data_);
  CHECK(data) << "Safe dynamic cast to WorldObject failed.";
  return WorldObject(std::move(data));
}

WorldObjectName WorldObject::Name() const {
  return WorldObjectName(GetData().Proto().name());
}

ObjectWorldResourceId WorldObject::ParentId() const {
  return ObjectWorldResourceId(GetData().Proto().parent().id());
}

WorldObjectName WorldObject::ParentName() const {
  return WorldObjectName(GetData().Proto().parent().name());
}

std::vector<ObjectWorldResourceId> WorldObject::ChildIds() const {
  std::vector<ObjectWorldResourceId> result;
  for (const intrinsic_proto::world::IdAndName& child :
       GetData().Proto().children()) {
    result.emplace_back(child.id());
  }
  return result;
}

std::vector<WorldObjectName> WorldObject::ChildNames() const {
  std::vector<WorldObjectName> result;
  for (const intrinsic_proto::world::IdAndName& child :
       GetData().Proto().children()) {
    result.emplace_back(child.name());
  }
  return result;
}

std::vector<ObjectWorldResourceId> WorldObject::FrameIds() const {
  std::vector<ObjectWorldResourceId> result;
  for (const intrinsic_proto::world::Frame& frame :
       GetData().Proto().frames()) {
    result.emplace_back(frame.id());
  }
  return result;
}

std::vector<FrameName> WorldObject::FrameNames() const {
  std::vector<FrameName> result;
  for (const intrinsic_proto::world::Frame& frame :
       GetData().Proto().frames()) {
    result.emplace_back(frame.name());
  }
  return result;
}

std::vector<ObjectWorldResourceId> WorldObject::ChildFrameIds() const {
  std::vector<ObjectWorldResourceId> result;
  result.reserve(GetData().Proto().frames_size());
  for (const intrinsic_proto::world::Frame& frame :
       GetData().Proto().frames()) {
    if (frame.has_parent_frame()) continue;
    result.emplace_back(frame.id());
  }
  return result;
}

std::vector<FrameName> WorldObject::ChildFrameNames() const {
  std::vector<FrameName> result;
  result.reserve(GetData().Proto().frames_size());
  for (const intrinsic_proto::world::Frame& frame :
       GetData().Proto().frames()) {
    if (frame.has_parent_frame()) continue;
    result.emplace_back(frame.name());
  }
  return result;
}

std::vector<Frame> WorldObject::Frames() const { return GetData().Frames(); }

absl::StatusOr<Frame> WorldObject::GetFrame(const FrameName& name) const {
  for (const Frame& frame : GetData().Frames()) {
    if (frame.Name() == name) {
      return frame;
    }
  }
  return absl::NotFoundError(
      absl::Substitute("Frame \"$0\" not found under object \"$1\".",
                       name.value(), Name().value()));
}

std::vector<Frame> WorldObject::ChildFrames() const {
  std::vector<Frame> result;
  result.reserve(GetData().Frames().size());
  absl::c_copy_if(
      GetData().Frames(), std::back_inserter(result),
      [](const Frame& frame) { return !frame.ParentFrameId().has_value(); });
  return result;
}

intrinsic_proto::world::ObjectReference WorldObject::ObjectReference() const {
  intrinsic_proto::world::ObjectReference result;
  result.mutable_by_name()->set_object_name(GetData().Proto().name());
  return result;
}

intrinsic_proto::world::ObjectReferenceWithEntityFilter
WorldObject::ObjectReferenceWithEntityFilter(
    const world::ObjectEntityFilter& filter) const {
  intrinsic_proto::world::ObjectReferenceWithEntityFilter result;
  *result.mutable_reference() = ObjectReference();
  *result.mutable_entity_filter() = filter.ToProto();
  return result;
}

const intrinsic_proto::world::Object& WorldObject::Proto() const {
  return GetData().Proto();
}

const WorldObject::Data& WorldObject::GetData() const {
  // This has to succeed because instances of WorldObject are always only
  // created with an instance of WorldObject::Data or a subclass thereof.
  return static_cast<const WorldObject::Data&>(TransformNode::GetData());
}

WorldObject::Data::Data(intrinsic_proto::world::Object proto,
                        const Pose3d& parent_t_this, std::vector<Frame> frames)
    : proto_(std::move(proto)),
      parent_t_this_(parent_t_this),
      frames_(std::move(frames)) {}

ObjectWorldResourceId WorldObject::Data::Id() const {
  return ObjectWorldResourceId(proto_.id());
}

Pose3d WorldObject::Data::ParentTThis() const { return parent_t_this_; }

intrinsic_proto::world::TransformNodeReference
WorldObject::Data::TransformNodeReference() const {
  intrinsic_proto::world::TransformNodeReference result;
  result.mutable_by_name()->mutable_object()->set_object_name(proto_.name());
  return result;
}

const intrinsic_proto::world::Object& WorldObject::Data::Proto() const {
  return proto_;
}

const std::vector<Frame>& WorldObject::Data::Frames() const { return frames_; }

}  // namespace world
}  // namespace intrinsic
