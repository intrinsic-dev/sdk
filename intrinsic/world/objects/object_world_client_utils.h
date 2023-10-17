// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_CLIENT_UTILS_H_
#define INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_CLIENT_UTILS_H_

#include "absl/status/statusor.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/transform_node.h"
#include "intrinsic/world/objects/world_object.h"

namespace intrinsic::world {

// Returns true if the given 'object' is an ancestor of the given frame or
// object 'node', i.e., if 'object' is equal to 'node' or is located on the path
// from 'node' to the root object.
absl::StatusOr<bool> IsObjectAncestorOfNode(
    const world::WorldObject& object, const world::TransformNode& node,
    const world::ObjectWorldClient& world);

}  // namespace intrinsic::world

#endif  // INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_CLIENT_UTILS_H_
