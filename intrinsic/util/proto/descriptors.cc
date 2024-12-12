// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/proto/descriptors.h"

#include <string>
#include <utility>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/strings/str_format.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/descriptor_database.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
namespace {
// Recursively adds `current_file` and all files it imports to
// `file_descriptors`.
//
// `file_descriptors` is keyed by filename, so that we avoid adding an import
// multiple times.
void AddFileAndImports(
    absl::flat_hash_map<std::string, const google::protobuf::FileDescriptor*>*
        file_descriptors,
    const google::protobuf::FileDescriptor& current_file) {
  // Add current file.
  if (!file_descriptors->try_emplace(current_file.name(), &current_file)
           .second) {
    // There's already a file descriptor with that name, so the dependencies
    // will be there too. Bail out.
    return;
  }

  // Add imports, recursively.
  for (int i = 0; i < current_file.dependency_count(); i++) {
    AddFileAndImports(file_descriptors, *current_file.dependency(i));
  }
}
}  // namespace

google::protobuf::FileDescriptorSet GenFileDescriptorSet(
    const google::protobuf::Descriptor& descriptor) {

  // Keyed by filename.
  absl::flat_hash_map<std::string, const google::protobuf::FileDescriptor*>
      file_descriptors;

  // Add root file and imports, recursively.
  AddFileAndImports(&file_descriptors, *descriptor.file());

  // Convert to FileDescriptorSet proto.
  google::protobuf::FileDescriptorSet out;
  for (auto& [name, file_descriptor] : file_descriptors) {
    file_descriptor->CopyTo(out.add_file());
  }
  return out;
}

absl::Status AddToDescriptorDatabase(
    google::protobuf::SimpleDescriptorDatabase* db,
    const google::protobuf::FileDescriptorProto& file_descriptor,
    absl::flat_hash_map<std::string, google::protobuf::FileDescriptorProto>&
        file_by_name) {
  for (const std::string& dependency : file_descriptor.dependency()) {
    if (auto fd_iter = file_by_name.find(dependency);
        fd_iter != file_by_name.end()) {
      // add dependency now and remove from elements to visit
      google::protobuf::FileDescriptorProto dependency_file_descriptor =
          fd_iter->second;
      file_by_name.erase(fd_iter);
      INTR_RETURN_IF_ERROR(AddToDescriptorDatabase(
          db, dependency_file_descriptor, file_by_name));
    }
  }
  if (!db->Add(file_descriptor)) {
    return absl::InvalidArgumentError(
        absl::StrFormat("Failed to add descriptor '%s' to descriptor database",
                        file_descriptor.name()));
  }
  return absl::OkStatus();
}

absl::Status PopulateDescriptorDatabase(
    google::protobuf::SimpleDescriptorDatabase* db,
    const google::protobuf::FileDescriptorSet& file_descriptor_set) {
  absl::flat_hash_map<std::string, google::protobuf::FileDescriptorProto>
      file_by_name;
  for (const google::protobuf::FileDescriptorProto& file_descriptor :
       file_descriptor_set.file()) {
    file_by_name[file_descriptor.name()] = file_descriptor;
  }
  while (!file_by_name.empty()) {
    google::protobuf::FileDescriptorProto file_descriptor =
        file_by_name.begin()->second;
    file_by_name.erase(file_by_name.begin());
    INTR_RETURN_IF_ERROR(
        AddToDescriptorDatabase(db, file_descriptor, file_by_name));
  }
  return absl::OkStatus();
}

}  // namespace intrinsic
