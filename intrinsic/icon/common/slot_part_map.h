// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_COMMON_SLOT_PART_MAP_H_
#define INTRINSIC_ICON_COMMON_SLOT_PART_MAP_H_

#include <string>

#include "absl/container/btree_map.h"
#include "absl/container/flat_hash_map.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic::icon {

// A SlotPartMap defines a mapping from the slot names used by an Action to
// Application Layer Part names. Uses btree_map since that, unlike
// flat_hash_map, is an ordered container and has equality operators and
// absl::Hash support.
using SlotPartMap = absl::btree_map<std::string, std::string>;

SlotPartMap SlotPartMapFromProto(
    const intrinsic_proto::icon::SlotPartMap& proto);
intrinsic_proto::icon::SlotPartMap ToProto(const SlotPartMap& part_map);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_COMMON_SLOT_PART_MAP_H_
