// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/world/objects/object_world_client_utils.h"

#include <optional>
#include <type_traits>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/objects/world_object.h"

namespace intrinsic::world {

absl::StatusOr<bool> IsObjectAncestorOfNode(
    const world::WorldObject& object, const world::TransformNode& node,
    const world::ObjectWorldClient& world) {
  if (object.Id() == RootObjectId()) {
    return true;
  }

  std::optional<world::WorldObject> current_obj =
      world::WorldObject::FromTransformNode(node);

  // If 'node' is a frame, get its parent object.
  if (!current_obj) {
    if (std::optional<world::Frame> frame =
            world::Frame::FromTransformNode(node);
        frame) {
      INTRINSIC_ASSIGN_OR_RETURN(current_obj,
                                 world.GetObject(frame->ObjectId()));
    } else {
      return absl::InvalidArgumentError("Unknown type of TransformNode.");
    }
  }

  // Traverse upwards util we find the object in question or stop at root.
  while (current_obj->Id() != RootObjectId()) {
    if (current_obj->Id() == object.Id()) {
      return true;
    }
    INTRINSIC_ASSIGN_OR_RETURN(current_obj,
                               world.GetObject(current_obj->ParentId()));
  }

  return false;
}

}  // namespace intrinsic::world
