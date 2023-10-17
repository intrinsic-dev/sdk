// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_TOOLS_GENERATE_DOCUMENTATION_H_
#define INTRINSIC_ICON_TOOLS_GENERATE_DOCUMENTATION_H_

#include <string>
#include <vector>

#include "absl/status/statusor.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic {
namespace icon {

std::string GenerateActionNames(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures);

absl::StatusOr<std::string> GenerateSingleActionDocumentation(
    const intrinsic_proto::icon::ActionSignature& signature);

absl::StatusOr<std::string> GenerateDocumentation(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures);

absl::StatusOr<std::string> GenerateDocumentation(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures,
    absl::Span<const std::vector<std::string>> compatible_parts,
    bool with_toc_header = true, bool with_devsite_header = false);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_TOOLS_GENERATE_DOCUMENTATION_H_
