// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/world/objects/object_entity_filter.h"

#include <set>
#include <string>

#include "absl/strings/string_view.h"
#include "intrinsic/world/objects/object_world_ids.h"
#include "intrinsic/world/proto/object_world_refs.pb.h"

namespace intrinsic {
namespace world {

ObjectEntityFilter& ObjectEntityFilter::IncludeBaseEntity() {
  include_base_entity_ = true;
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::IncludeFinalEntity() {
  include_final_entity_ = true;
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::IncludeAllEntities() {
  include_base_entity_ = false;
  include_final_entity_ = false;
  include_all_entities_ = true;
  entity_ids_.clear();
  entity_names_.clear();
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::IncludeEntityId(
    ObjectWorldResourceId entity_id) {
  entity_ids_.insert(entity_id);
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::ClearExplicitEntityIds() {
  entity_ids_.clear();
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::IncludeEntityName(
    absl::string_view entity_name) {
  entity_names_.insert(std::string(entity_name));
  return *this;
}

ObjectEntityFilter& ObjectEntityFilter::ClearExplicitEntityNames() {
  entity_names_.clear();
  return *this;
}

intrinsic_proto::world::ObjectEntityFilter ObjectEntityFilter::ToProto() const {
  intrinsic_proto::world::ObjectEntityFilter filter;
  if (include_all_entities_) {
    filter.set_include_all_entities(true);
    return filter;
  }

  if (include_base_entity_) {
    filter.set_include_base_entity(true);
  }
  if (include_final_entity_) {
    filter.set_include_final_entity(true);
  }
  for (const auto& entity_id : entity_ids_) {
    filter.add_entity_references()->set_id(entity_id.value());
  }
  for (const auto& entity_name : entity_names_) {
    filter.add_entity_names(entity_name);
  }
  return filter;
}

ObjectEntityFilter ObjectEntityFilter::FromProto(
    const ::intrinsic_proto::world::ObjectEntityFilter& entity_filter) {
  ObjectEntityFilter result;
  result.include_all_entities_ = entity_filter.include_all_entities();
  result.include_base_entity_ = entity_filter.include_base_entity();
  result.include_final_entity_ = entity_filter.include_final_entity();
  for (const auto& entity : entity_filter.entity_references()) {
    result.entity_ids_.insert(ObjectWorldResourceId(entity.id()));
  }
  result.entity_names_ = std::set<std::string>{
      entity_filter.entity_names().begin(), entity_filter.entity_names().end()};
  return result;
}

const ObjectEntityFilter& ObjectEntityFilter::BaseEntity() {
  static const ObjectEntityFilter filter =  // NOLINT
      ObjectEntityFilter().IncludeBaseEntity();
  return filter;
}

const ObjectEntityFilter& ObjectEntityFilter::FinalEntity() {
  static const ObjectEntityFilter filter =  // NOLINT
      ObjectEntityFilter().IncludeFinalEntity();
  return filter;
}

const ObjectEntityFilter& ObjectEntityFilter::AllEntities() {
  static const ObjectEntityFilter filter =  // NOLINT
      ObjectEntityFilter().IncludeAllEntities();
  return filter;
}

}  // namespace world
}  // namespace intrinsic
