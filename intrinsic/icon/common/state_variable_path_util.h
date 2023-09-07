// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_UTIL_H_
#define INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_UTIL_H_

#include <optional>
#include <string>

#include "absl/types/span.h"

namespace intrinsic::icon {

// This struct represents one node of a state variable path.
// A node consists of a name and optionally an array index.
struct StateVariablePathNode {
  std::string ToString() const;

  template <typename Sink>
  friend void AbslStringify(Sink& sink, const StateVariablePathNode& node) {
    sink.Append(node.ToString());
  }

  // Name of the node. Must not be empty.
  std::string name;
  // Optional index of an array that is represented by this node.
  std::optional<size_t> index;
};

inline bool operator==(const StateVariablePathNode& lhs,
                       const StateVariablePathNode& rhs) {
  return lhs.name == rhs.name && lhs.index == rhs.index;
}

// Builds a state variable path from a span of nodes by prepending
// `kStateVariablePathPrefix` and joining the nodes with
// `kStateVariablePathSeparator`.
std::string BuildStateVariablePath(
    absl::Span<const StateVariablePathNode> nodes);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_UTIL_H_
