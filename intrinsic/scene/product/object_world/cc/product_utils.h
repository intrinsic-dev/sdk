// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SCENE_PRODUCT_OBJECT_WORLD_CC_PRODUCT_UTILS_H_
#define INTRINSIC_SCENE_PRODUCT_OBJECT_WORLD_CC_PRODUCT_UTILS_H_

#include <optional>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/struct.pb.h"
#include "intrinsic/scene/product/proto/product_world_object_data.pb.h"
#include "intrinsic/scene/proto/v1/scene_object.pb.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/world_object.h"

// A collection of utility functions for creating and working with product
// objects based on a user_data field convention.
namespace intrinsic {
namespace product {

constexpr absl::string_view kProductUserDataKey = "FLOWSTATE_product";
// Returns true if the given object is a product by the convention of having
// a product name keyed by `kProductNameUserDataKey`.
absl::StatusOr<bool> IsProduct(const world::WorldObject& object);

// Returns the product name of the given object if it is a product by the
// convention of having a product name keyed by `kProductNameUserDataKey` in
// `user_data`.
absl::StatusOr<std::optional<std::string>> GetProductName(
    const world::WorldObject& object);

// Returns the product metadata of the given object if it is a product by the
// convention of having a product metadata `google::protobuf::Struct` keyed by
// `kProductMetadataUserDataKey` in `user_data`.
absl::StatusOr<std::optional<google::protobuf::Struct>> GetProductMetadata(
    const world::WorldObject& object);

struct CreateObjectFromProductParams {
  // The original product name.
  std::string product_name;
  // The scene_object geometry representation of the product this object is
  // created from.
  intrinsic_proto::scene_object::v1::SceneObject scene_object;

  // Optional product metadata.
  google::protobuf::Struct product_metadata;
};

absl::Status CreateObjectFromProduct(
    world::ObjectWorldClient& object_world, const WorldObjectName& object_name,
    const world::ObjectWorldClient::CreateObjectOptions& create_object_options,
    const CreateObjectFromProductParams& params);

}  // namespace product
}  // namespace intrinsic

#endif  // INTRINSIC_SCENE_PRODUCT_OBJECT_WORLD_CC_PRODUCT_UTILS_H_
