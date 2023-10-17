// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/proto/source_code_info_view.h"

#include <algorithm>
#include <memory>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/descriptor_database.h"
#include "google/protobuf/repeated_field.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {

absl::Status SourceCodeInfoView::Init(
    const google::protobuf::FileDescriptorSet& file_descriptor_set) {
  pool_ = std::make_unique<Pool>();
  if (!std::all_of(
          file_descriptor_set.file().begin(), file_descriptor_set.file().end(),
          [pool =
               pool_.get()](const google::protobuf::FileDescriptorProto& file) {
            return pool->descriptor_database.Add(file);
          })) {
    pool_.reset();
    return absl::InvalidArgumentError(
        "`file_descriptor_set` contains duplicate files.");
  }

  return absl::OkStatus();
}

absl::Status SourceCodeInfoView::InitStrict(
    const google::protobuf::FileDescriptorSet& file_descriptor_set) {
  for (const google::protobuf::FileDescriptorProto& file :
       file_descriptor_set.file()) {
    if (!file.has_source_code_info()) {
      return absl::NotFoundError(absl::StrFormat(
          "FileDescriptorProto for file %s is missing source_code_info",
          file.name()));
    }
  }
  return Init(file_descriptor_set);
}

absl::StatusOr<std::string> SourceCodeInfoView::GetLeadingCommentsByMessageType(
    absl::string_view message_name) const {
  if (pool_ == nullptr) {
    return absl::FailedPreconditionError("SourceCodeInfoView not Init()ed.");
  }

  const google::protobuf::Descriptor* const message =
      // Need the std::string(.) conversion here because the external version of
      // the function does not have a version that takes absl::string_view.
      pool_->descriptor_pool.FindMessageTypeByName(
          std::string(message_name));  // NOLINT
  if (message == nullptr) {
    return absl::NotFoundError(
        absl::StrCat("Message does not exist with: ", message_name));
  }

  google::protobuf::SourceLocation source_location;
  if (!message->GetSourceLocation(&source_location)) {
    return absl::NotFoundError(
        "SourceLocation not available for FileDescriptor.");
  }

  return source_location.leading_comments;
}

absl::StatusOr<std::string> SourceCodeInfoView::GetLeadingCommentsByFieldName(
    absl::string_view field_name) const {
  if (pool_ == nullptr) {
    return absl::FailedPreconditionError("SourceCodeInfoView not Init()ed.");
  }

  const google::protobuf::FieldDescriptor* const field =
      // Need the std::string(.) conversion here because the external version of
      // the function does not have a version that takes absl::string_view.
      pool_->descriptor_pool.FindFieldByName(
          std::string(field_name));  // NOLINT
  if (field == nullptr) {
    return absl::NotFoundError(
        absl::StrCat("Field does not exist with: ", field_name));
  }

  google::protobuf::SourceLocation source_location;
  if (!field->GetSourceLocation(&source_location)) {
    return absl::NotFoundError(
        "SourceLocation not available for FileDescriptor.");
  }

  return source_location.leading_comments;
}

absl::StatusOr<google::protobuf::Map<std::string, std::string>>
SourceCodeInfoView::GetNestedFieldCommentMap(absl::string_view message_name) {
  if (pool_ == nullptr) {
    return absl::FailedPreconditionError("SourceCodeInfoView not Init()ed.");
  }

  const google::protobuf::Descriptor* const message =
      // Need the std::string(.) conversion here because the external version of
      // the function does not have a version that takes absl::string_view.
      pool_->descriptor_pool.FindMessageTypeByName(
          std::string(message_name));  // NOLINT

  if (message == nullptr) {
    return absl::NotFoundError(
        absl::StrCat("Message does not exist with: ", message_name));
  }

  google::protobuf::Map<std::string, std::string> comment_map;
  INTRINSIC_RETURN_IF_ERROR(GetNestedFieldCommentMap(message, comment_map));
  return comment_map;
}

absl::Status SourceCodeInfoView::GetNestedFieldCommentMap(
    const google::protobuf::Descriptor* message,
    google::protobuf::Map<std::string, std::string>& comment_map) {
  for (int field_index = 0; field_index < message->field_count();
       ++field_index) {
    const google::protobuf::FieldDescriptor* field =
        message->field(field_index);

    // Add leading comments for this field, i.e., the comments above the field.
    INTRINSIC_ASSIGN_OR_RETURN(
        std::string comment, GetLeadingCommentsByFieldName(field->full_name()));
    comment_map.insert({field->full_name(), comment});

    // Recursively process the message type of the field.
    const google::protobuf::FieldDescriptor* field_to_recursively_process =
        message->field(field_index);
    if (field->is_map()) {
      // If the field is a map, we'll recursively process the value only. The
      // key should always be a primitive type.
      const google::protobuf::Descriptor* msg_descriptor =
          field->message_type();
      field_to_recursively_process = msg_descriptor->map_value();
    }
    if (field_to_recursively_process->cpp_type() ==
        google::protobuf::FieldDescriptor::CPPTYPE_MESSAGE) {
      const google::protobuf::Descriptor* msg_descriptor =
          field_to_recursively_process->message_type();
      auto msg_iter = comment_map.find(msg_descriptor->full_name());
      if (msg_iter == comment_map.end()) {
        // Get top-level message comments
        INTRINSIC_ASSIGN_OR_RETURN(
            std::string comment,
            GetLeadingCommentsByMessageType(msg_descriptor->full_name()));
        comment_map.insert({msg_descriptor->full_name(), comment});
        INTRINSIC_RETURN_IF_ERROR(
            GetNestedFieldCommentMap(msg_descriptor, comment_map));
      }
    }
  }

  return absl::OkStatus();
}

}  // namespace intrinsic
