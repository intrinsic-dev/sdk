// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/common/state_variable_path_util.h"

#include <iterator>
#include <string>
#include <vector>

#include "absl/algorithm/container.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "intrinsic/icon/common/state_variable_path_constants.h"

namespace intrinsic::icon {

std::string BuildStateVariablePath(
    const absl::Span<const StateVariablePathNode> nodes) {
  std::vector<std::string> node_strings;
  absl::c_transform(
      nodes, std::back_inserter(node_strings),
      [](const StateVariablePathNode& node) { return node.ToString(); });
  return absl::StrCat(kStateVariablePathPrefix,
                      absl::StrJoin(node_strings, kStateVariablePathSeparator));
}

std::string StateVariablePathNode::ToString() const {
  std::string result = name;
  if (index.has_value()) {
    result += absl::StrCat("[", index.value(), "]");
  }
  return result;
}
}  // namespace intrinsic::icon
