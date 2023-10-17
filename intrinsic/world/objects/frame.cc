// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/world/objects/frame.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/proto_conversion.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"
#include "intrinsic/world/proto/object_world_service.pb.h"

namespace intrinsic {
namespace world {

absl::StatusOr<Frame> Frame::Create(intrinsic_proto::world::Frame proto) {
  INTRINSIC_ASSIGN_OR_RETURN(Pose3d parent_t_this,
                             intrinsic_proto::FromProto(proto.parent_t_this()));
  return Frame(std::make_shared<const Data>(std::move(proto), parent_t_this));
}

std::optional<Frame> Frame::FromTransformNode(const TransformNode& node) {
  std::shared_ptr<const Frame::Data> frame_data =
      std::dynamic_pointer_cast<const Frame::Data>(node.data_);
  return frame_data ? std::optional<Frame>(Frame(std::move(frame_data)))
                    : std::nullopt;
}

Frame::Frame(std::shared_ptr<const Data> data)
    : TransformNode(std::move(data)) {}

FrameName Frame::Name() const { return FrameName(GetData().Proto().name()); }

ObjectWorldResourceId Frame::ObjectId() const {
  return ObjectWorldResourceId(GetData().Proto().object().id());
}

WorldObjectName Frame::ObjectName() const {
  return WorldObjectName(GetData().Proto().object().name());
}

std::optional<ObjectWorldResourceId> Frame::ParentFrameId() const {
  return GetData().Proto().parent_frame().id().empty()
             ? std::optional<ObjectWorldResourceId>()
             : ObjectWorldResourceId(GetData().Proto().parent_frame().id());
}

std::optional<FrameName> Frame::ParentFrameName() const {
  return GetData().Proto().parent_frame().name().empty()
             ? std::optional<FrameName>()
             : FrameName(GetData().Proto().parent_frame().name());
}

std::vector<ObjectWorldResourceId> Frame::ChildFrameIds() const {
  std::vector<ObjectWorldResourceId> result;
  result.reserve(GetData().Proto().child_frames_size());
  for (const intrinsic_proto::world::IdAndName& child_frame :
       GetData().Proto().child_frames()) {
    result.emplace_back(child_frame.id());
  }
  return result;
}

std::vector<FrameName> Frame::ChildFrameNames() const {
  std::vector<FrameName> result;
  result.reserve(GetData().Proto().child_frames_size());
  for (const intrinsic_proto::world::IdAndName& child_frame :
       GetData().Proto().child_frames()) {
    result.emplace_back(child_frame.name());
  }
  return result;
}

intrinsic_proto::world::FrameReference Frame::FrameReference() const {
  intrinsic_proto::world::FrameReference result;
  result.mutable_by_name()->set_frame_name(GetData().Proto().name());
  result.mutable_by_name()->set_object_name(GetData().Proto().object().name());
  return result;
}

bool Frame::IsAttachmentFrame() const {
  return GetData().Proto().is_attachment_frame();
}

const Frame::Data& Frame::GetData() const {
  // This has to succeed because instances of Frame are always only created with
  // an instance of Frame::Data.
  return static_cast<const Frame::Data&>(TransformNode::GetData());
}

Frame::Data::Data(intrinsic_proto::world::Frame proto,
                  const Pose3d& parent_t_this)
    : proto_(std::move(proto)), parent_t_this_(parent_t_this) {}

ObjectWorldResourceId Frame::Data::Id() const {
  return ObjectWorldResourceId(proto_.id());
}

Pose3d Frame::Data::ParentTThis() const { return parent_t_this_; }

intrinsic_proto::world::TransformNodeReference
Frame::Data::TransformNodeReference() const {
  intrinsic_proto::world::TransformNodeReference result;
  result.mutable_by_name()->mutable_frame()->set_object_name(
      proto_.object().name());
  result.mutable_by_name()->mutable_frame()->set_frame_name(proto_.name());
  return result;
}

const intrinsic_proto::world::Frame& Frame::Data::Proto() const {
  return proto_;
}

}  // namespace world
}  // namespace intrinsic
