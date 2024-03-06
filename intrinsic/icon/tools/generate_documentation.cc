// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/tools/generate_documentation.h"

#include <algorithm>
#include <iterator>
#include <optional>
#include <string>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic {
namespace icon {
namespace {

struct Content {
  struct Entry {
    intrinsic_proto::icon::ActionSignature signature;
    std::optional<std::vector<std::string>> parts;
  };

  std::vector<Entry> entries;
};

// Joins N strings, using `join_back` to join the final string and `join_first`
// to join the remaining strings.
//
// GrammaticalJoin({}, ", ", " & ") => ""
// GrammaticalJoin({{"red"}, ", ", " &") => "red"
// GrammaticalJoin({"red", "green"}, ", ", " &") => "red & green"
// GrammaticalJoin({"red", "green", "blue"}, ", ", " &") => "red, green & blue"
std::string GrammaticalJoin(const absl::Span<std::string> strings,
                            absl::string_view join_first,
                            absl::string_view join_back) {
  if (strings.size() <= 2) {
    return absl::StrJoin(strings, join_back);
  }
  return absl::StrJoin(
      {absl::StrJoin(strings.first(strings.size() - 1), join_first),
       strings.back()},
      join_back);
}

std::string DisplayEntryMarkdown(const Content::Entry& entry) {
  std::string out;
  const intrinsic_proto::icon::ActionSignature& signature = entry.signature;
  absl::StrAppend(&out, "## ", signature.action_type_name(), "\n\n");

  const bool has_fixed_parameters =
      !signature.fixed_parameters_message_type().empty();
  const bool has_streaming_input = (signature.streaming_input_infos_size() > 0);
  const bool has_state_variables = (signature.state_variable_infos_size() > 0);
  const bool has_realtime_signals =
      (signature.realtime_signal_infos_size() > 0);

  absl::StrAppend(&out, signature.text_description(), "\n");

  // Briefly summarize what this action _does not_ have. E.g. "This action does
  // not have fixed parameters, streaming inputs or streaming outputs.".
  std::vector<std::string> does_not_have;
  if (!has_fixed_parameters) {
    does_not_have.emplace_back("fixed parameters");
  }
  if (!has_streaming_input) {
    does_not_have.emplace_back("streaming inputs");
  }
  if (!signature.has_streaming_output_info()) {
    does_not_have.emplace_back("streaming output");
  }
  if (!has_state_variables) {
    does_not_have.emplace_back("state variables");
  }
  if (!has_realtime_signals) {
    does_not_have.emplace_back("real-time signals");
  }
  if (!does_not_have.empty()) {
    absl::StrAppend(
        &out, "\n\nThis action does not have ",
        GrammaticalJoin(absl::Span<std::string>(does_not_have), ", ", " or "),
        ".\n");
  }

  if (entry.parts.has_value()) {
    absl::StrAppend(&out, "\n### Compatible Parts\n\n");
    if (entry.parts->empty()) {
      absl::StrAppend(&out, "(none)\n");
    } else {
      for (const std::string& part : *entry.parts) {
        absl::StrAppend(&out, "- `", part, "`\n");
      }
    }
  }

  if (has_fixed_parameters) {
    absl::StrAppend(&out, "\n### Fixed Parameters\n\n");
    absl::StrAppend(&out, "Message Type: `",
                    signature.fixed_parameters_message_type(), "`\n");
  }

  if (has_streaming_input) {
    absl::StrAppend(&out, "\n### Streaming Inputs\n\n");
    for (const intrinsic_proto::icon::ActionSignature::ParameterInfo& param :
         signature.streaming_input_infos()) {
      absl::StrAppend(&out, "#### ", param.parameter_name(), "\n");
      absl::StrAppend(&out, param.text_description(), "\n");
    }
  }

  if (signature.has_streaming_output_info()) {
    absl::StrAppend(&out, "\n### Streaming Output\n\n");
    absl::StrAppend(&out, "#### ",
                    signature.streaming_output_info().parameter_name(), "\n");
    absl::StrAppend(&out, signature.streaming_output_info().text_description(),
                    "\n");
  }

  if (has_realtime_signals) {
    absl::StrAppend(&out, "\n### Realtime Signals\n\n");
    for (const intrinsic_proto::icon::ActionSignature::RealtimeSignalInfo&
             param : signature.realtime_signal_infos()) {
      absl::StrAppend(&out, "#### ", param.signal_name(), "\n");
      absl::StrAppend(&out, param.text_description(), "\n");
    }
  }

  if (has_state_variables) {
    absl::StrAppend(&out, "\n### State Variables\n\n");
    for (const intrinsic_proto::icon::ActionSignature::StateVariableInfo&
             state_var : signature.state_variable_infos()) {
      absl::StrAppend(&out, "#### ", state_var.state_variable_name(), " ");
      switch (state_var.type()) {
        case intrinsic_proto::icon::ActionSignature::StateVariableInfo::
            TYPE_DOUBLE:
          absl::StrAppend(&out, "(double)\n");
          break;
        case intrinsic_proto::icon::ActionSignature::StateVariableInfo::
            TYPE_INT64:
          absl::StrAppend(&out, "(int64)\n");
          break;
        case intrinsic_proto::icon::ActionSignature::StateVariableInfo::
            TYPE_BOOL:
          absl::StrAppend(&out, "(bool)\n");
          break;
        default:
          absl::StrAppend(&out, "(unknown type)\n");
      }
      absl::StrAppend(&out, state_var.text_description(), "\n");
    }
  }
  return out;
}

std::string DisplayContentMarkdown(const Content& content, bool with_toc_header,
                                   bool with_devsite_header) {
  std::vector<std::string> entry_strings;
  std::transform(content.entries.begin(), content.entries.end(),
                 std::back_inserter(entry_strings),
                 [](const Content::Entry& entry) -> std::string {
                   return DisplayEntryMarkdown(entry);
                 });
  std::string markdown_content = absl::StrJoin(entry_strings, "\n\n");

  if (with_toc_header) {
    markdown_content = absl::StrCat(R"(# ICON Actions Reference

The following actions are supported by this release's ICON Server:

[TOC]

)",
                                    markdown_content);
  }

  if (with_devsite_header) {
    markdown_content = absl::StrCat(R"(Project: /_project.yaml
Book: /_book.yaml

)",
                                    markdown_content);
  }

  return markdown_content;
}
}  // namespace

std::string GenerateActionNames(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures) {
  std::vector<std::string> entry_strings;
  std::transform(signatures.begin(), signatures.end(),
                 std::back_inserter(entry_strings),
                 [](const intrinsic_proto::icon::ActionSignature& signature)
                     -> std::string { return signature.action_type_name(); });
  return absl::StrCat(absl::StrJoin(entry_strings, "\n"), "\n");
}

absl::StatusOr<std::string> GenerateSingleActionDocumentation(
    const intrinsic_proto::icon::ActionSignature& signature) {
  return GenerateDocumentation({signature}, {}, false, true);
}

absl::StatusOr<std::string> GenerateDocumentation(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures) {
  return GenerateDocumentation(signatures, {});
}

absl::StatusOr<std::string> GenerateDocumentation(
    absl::Span<const intrinsic_proto::icon::ActionSignature> signatures,
    absl::Span<const std::vector<std::string>> compatible_parts,
    bool with_toc_header, bool with_devsite_header) {
  if (signatures.empty()) {
    return "(No actions available)\n";
  }
  if (!compatible_parts.empty() &&
      signatures.size() != compatible_parts.size()) {
    return absl::InvalidArgumentError(
        "compatible_parts must be same size as signatures or empty");
  }

  Content content;
  for (int i = 0; i < signatures.size(); ++i) {
    const intrinsic_proto::icon::ActionSignature& signature = signatures[i];
    Content::Entry entry;
    entry.signature = signature;
    if (!compatible_parts.empty()) {
      entry.parts = compatible_parts[i];
    }
    content.entries.emplace_back(entry);
  }
  return DisplayContentMarkdown(content, with_toc_header, with_devsite_header);
}

}  // namespace icon
}  // namespace intrinsic
