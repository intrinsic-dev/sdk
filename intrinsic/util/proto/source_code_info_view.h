// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_UTIL_PROTO_SOURCE_CODE_INFO_VIEW_H_
#define INTRINSIC_UTIL_PROTO_SOURCE_CODE_INFO_VIEW_H_

#include <memory>
#include <string>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/descriptor_database.h"
#include "google/protobuf/map.h"

namespace intrinsic {

// Provides convenient access to `source_code_info` from a
// google::protobuf::FileDescriptorSet.
class SourceCodeInfoView {
 public:
  SourceCodeInfoView() = default;

  // SourceCodeInfoView is move-only.
  SourceCodeInfoView(SourceCodeInfoView&& other) = default;
  SourceCodeInfoView& operator=(SourceCodeInfoView&& other) = default;

  // Initializes this with the given `file_descriptor_set`.
  //
  // Allows for files in the file_descriptor_set to be missing source_code_info.
  // When inspecting the SourceCodeInfoView via Get*() methods, the user will
  // receive an error on if the descriptor being inspected does not have source
  // code info associated with it.
  //
  // Returns an InvalidArgument error if the `file_descriptor_set` contains
  // multiple FileDescriptorProtos with the same filename.
  absl::Status Init(
      const google::protobuf::FileDescriptorSet& file_descriptor_set);

  // Initializes this with the given `file_descriptor_set`.
  //
  // Provides a more strict alternative initialization for when the user cares
  // that *all* files in the `file_descriptor_set` provide source_code_info.
  //
  // Returns an InvalidArgument error if the `file_descriptor_set` contains
  // multiple FileDescriptorProtos with the same filename.
  //
  // Returns a NotFound error if any FileDescriptorSet.file in the provided
  // file_descriptor_set is missing the `source_code_info` field.
  absl::Status InitStrict(
      const google::protobuf::FileDescriptorSet& file_descriptor_set);

  // Retrieves the leading comments for a field, specified by the full name of
  // the field. Returns an error if the field does not exist, or the
  // corresponding FileDescriptorProto does not contain `source_code_info`.
  absl::StatusOr<std::string> GetLeadingCommentsByFieldName(
      absl::string_view field_name) const;

  // Retrieves the leading comments for a message, specified by the full name of
  // the message. Returns an error if the message does not exist, or the
  // corresponding FileDescriptorProto does not contain `source_code_info`.
  absl::StatusOr<std::string> GetLeadingCommentsByMessageType(
      absl::string_view message_name) const;

  // Retrieves all field comments and message comments of the given message and
  // all of its nested submessages. They keys of the map are the full name of
  // the message or field that the comment applies to, the value is the comment.
  absl::StatusOr<google::protobuf::Map<std::string, std::string>>
  GetNestedFieldCommentMap(absl::string_view message_name);

 private:
  absl::Status GetNestedFieldCommentMap(
      const google::protobuf::Descriptor* message,
      google::protobuf::Map<std::string, std::string>& comment_map);

  struct Pool {
    Pool() : descriptor_pool(&descriptor_database) {}
    google::protobuf::SimpleDescriptorDatabase descriptor_database;
    google::protobuf::DescriptorPool descriptor_pool;
  };

  std::unique_ptr<Pool> pool_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_SOURCE_CODE_INFO_VIEW_H_
