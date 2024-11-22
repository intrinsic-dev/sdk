// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/scene/product/object_world/cc/product_utils.h"

#include <optional>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/strings/substitute.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/struct.pb.h"
#include "google/protobuf/wrappers.pb.h"
#include "intrinsic/scene/product/proto/product_world_object_data.pb.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/objects/world_object.h"

namespace intrinsic {
namespace product {

namespace {
absl::StatusOr<std::optional<intrinsic_proto::product::ProductWorldObjectData>>
GetProductData(const world::WorldObject& object) {
  if (!object.Proto().object_component().user_data().contains(
          kProductUserDataKey)) {
    return std::nullopt;
  }
  const google::protobuf::Any& product_any =
      object.Proto().object_component().user_data().at(kProductUserDataKey);
  intrinsic_proto::product::ProductWorldObjectData product_data;
  if (!product_any.UnpackTo(&product_data)) {
    return absl::FailedPreconditionError(absl::Substitute(
        "Failed to unpack product data from user data. Expect "
        "type [$0] in user data google.protobuf.Any. Got type url [$1] "
        "instead.",
        intrinsic_proto::product::ProductWorldObjectData::descriptor()
            ->full_name(),
        product_any.type_url()));
  }
  return product_data;
}
}  // namespace

absl::StatusOr<bool> IsProduct(const world::WorldObject& object) {
  INTR_ASSIGN_OR_RETURN(auto product_data, GetProductData(object));
  return product_data.has_value();
}

absl::StatusOr<std::optional<std::string>> GetProductName(
    const world::WorldObject& object) {
  INTR_ASSIGN_OR_RETURN(auto product_data, GetProductData(object));
  if (!product_data.has_value()) {
    return std::nullopt;
  }
  return product_data->product_name();
}

absl::StatusOr<std::optional<google::protobuf::Struct>> GetProductMetadata(
    const world::WorldObject& object) {
  INTR_ASSIGN_OR_RETURN(auto product_data, GetProductData(object));
  if (!product_data.has_value()) {
    return std::nullopt;
  }
  return product_data->metadata();
}

absl::Status CreateObjectFromProduct(
    world::ObjectWorldClient& object_world, const WorldObjectName& object_name,
    const world::ObjectWorldClient::CreateObjectOptions& create_object_options,
    const CreateObjectFromProductParams& params) {
  auto options_with_product_data = create_object_options;
  intrinsic_proto::product::ProductWorldObjectData product_data;
  *product_data.mutable_product_name() = params.product_name;
  *product_data.mutable_metadata() = params.product_metadata;
  google::protobuf::Any product_data_any;
  product_data_any.PackFrom(product_data);
  if (options_with_product_data.user_data.contains(kProductUserDataKey)) {
    return absl::InvalidArgumentError(absl::Substitute(
        "CreateObjectOptions already contains reserved product user data kay "
        "'$0'.",
        kProductUserDataKey));
  }

  options_with_product_data.user_data[kProductUserDataKey] = product_data_any;

  INTR_RETURN_IF_ERROR(object_world.CreateObjectFromSceneObject(
      params.scene_object, object_name, options_with_product_data));

  return absl::OkStatus();
}

}  // namespace product
}  // namespace intrinsic
