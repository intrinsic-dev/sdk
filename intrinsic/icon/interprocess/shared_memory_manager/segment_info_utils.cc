// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_utils.h"

#include <stddef.h>
#include <string.h>

#include <cstdint>
#include <string>
#include <vector>

#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"

namespace intrinsic::icon {

namespace {

inline static std::string InterfaceNameFromSegment(const SegmentName& name) {
  const char* data = reinterpret_cast<const char*>(name.value()->Data());
  return std::string(data, strnlen(data, name.value()->size()));
}

}  // namespace

std::vector<std::string> GetNamesFromSegmentInfo(
    const SegmentInfo& segment_info) {
  std::vector<std::string> names;
  names.reserve(segment_info.size());

  for (uint32_t i = 0; i < segment_info.size(); ++i) {
    names.emplace_back(InterfaceNameFromSegment(*segment_info.names()->Get(i)));
  }

  return names;
}

std::vector<std::string> GetNamesFromFileDescriptorNames(
    const FileDescriptorNames& file_descriptor_names) {
  std::vector<std::string> names;
  names.reserve(file_descriptor_names.size());

  for (uint32_t i = 0; i < file_descriptor_names.size(); ++i) {
    names.emplace_back(
        InterfaceNameFromSegment(*file_descriptor_names.names()->Get(i)));
  }

  return names;
}

std::vector<std::string> GetRequiredInterfaceNamesFromSegmentInfo(
    const SegmentInfo& segment_info) {
  std::vector<std::string> names;
  names.reserve(segment_info.size());

  for (uint32_t i = 0; i < segment_info.size(); ++i) {
    const SegmentName* name = segment_info.names()->Get(i);
    if (!name->must_be_used()) {
      continue;
    }
    names.emplace_back(InterfaceNameFromSegment(*name));
  }

  return names;
}

}  // namespace intrinsic::icon
