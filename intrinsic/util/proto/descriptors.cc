// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/util/proto/descriptors.h"

#include <string>
#include <utility>

#include "absl/container/flat_hash_map.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"

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
  if (!file_descriptors->insert({current_file.name(), &current_file}).second) {
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

}  // namespace intrinsic
