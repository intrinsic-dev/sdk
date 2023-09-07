// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/mman.h>
#include <unistd.h>

#include <algorithm>
#include <cstring>
#include <new>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/flatbuffers.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_generated.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic::icon {

inline constexpr mode_t kShmMode = 0644;
// Max string size as defined in `segment_info.fbs`
inline constexpr uint32_t kMaxSegmentStringSize = 255;
inline constexpr uint32_t kMaxSegmentSize = 100;

namespace {
absl::Status VerifyName(absl::string_view name) {
  if (name[0] != '/') {
    return absl::InvalidArgumentError(
        "shm segment name must start with a forward slash");
  }
  if (name.size() >= kMaxSegmentStringSize) {
    return absl::InvalidArgumentError(
        "shm segment name can't exceed 255 characters");
  }
  if (std::find(name.begin() + 1, name.end(), '/') != name.end()) {
    return absl::InvalidArgumentError(
        "shm segment name can't have further forward slashes except the first "
        "one");
  }

  return absl::OkStatus();
}

SegmentInfo SegmentInfoFromHashMap(
    const absl::flat_hash_map<std::string, uint8_t*>& segments) {
  SegmentInfo segment_info(segments.size());
  uint32_t index = 0;
  for (const auto& [segment_name, buf] : segments) {
    SegmentName segment;
    // fbs doesn't have char as datatype, only int8_t which is byte compatible.
    auto* data = reinterpret_cast<char*>(segment.mutable_value()->Data());
    std::memset(data, '\0', kMaxSegmentStringSize);
    size_t string_size = segment_name.size() < kMaxSegmentStringSize
                             ? segment_name.size()
                             : kMaxSegmentStringSize - 1;
    std::memcpy(data, segment_name.c_str(), string_size);

    segment_info.mutable_names()->Mutate(index, segment);
    ++index;
  }

  return segment_info;
}
}  // namespace

SharedMemoryManager::~SharedMemoryManager() {
  // unlink all created shm segments
  for (const auto& segment : memory_segments_) {
    auto* header = reinterpret_cast<SegmentHeader*>(segment.second);
    // We've used placement new during the initialization. We have to call the
    // destructor explicitly to cleanup.
    header->~SegmentHeader();
    shm_unlink(segment.first.c_str());
  }
}

const SegmentHeader* const SharedMemoryManager::GetSegmentHeader(
    const std::string& name) {
  uint8_t* header = GetRawHeader(name);
  return reinterpret_cast<SegmentHeader*>(header);
}

absl::Status SharedMemoryManager::InitSegment(const std::string& name,
                                              size_t segment_size,
                                              const std::string& type_id) {
  if (memory_segments_.size() >= kMaxSegmentSize) {
    return absl::ResourceExhaustedError(
        absl::StrCat("Unable to add ", name, ". Max size of ", kMaxSegmentSize,
                     " segments exceeded."));
  }
  if (type_id.size() > SegmentHeader::TypeInfo::kMaxSize) {
    return absl::InvalidArgumentError(
        absl::StrCat("type id [", type_id, "] exceeds max size of ",
                     SegmentHeader::TypeInfo::kMaxSize));
  }

  if (memory_segments_.contains(name)) {
    return absl::AlreadyExistsError(
        absl::StrCat("shm segment exists already: ", name));
  }
  INTRINSIC_RETURN_IF_ERROR(VerifyName(name));

  auto shm_fd = shm_open(name.c_str(), O_CREAT | O_EXCL | O_RDWR, kShmMode);
  if (shm_fd == -1 && errno == EEXIST) {
    LOG(WARNING) << "The shared memory segment '" << name
                 << "' already exists. It will be reused.";
    shm_fd = shm_open(name.c_str(), O_CREAT | O_RDWR, kShmMode);
  }
  if (shm_fd == -1) {
    return absl::InternalError(
        absl::StrCat("unable to open shared memory segment: ", name, "[",
                     strerror(errno), "]"));
  }

  if (ftruncate(shm_fd, segment_size) == -1) {
    return absl::InternalError(
        absl::StrCat("unable to resize shared memory segment: ", name, "[",
                     strerror(errno), "]"));
  }
  auto* data = static_cast<uint8_t*>(mmap(
      nullptr, segment_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0));
  if (data == nullptr) {
    return absl::InternalError(
        absl::StrCat("unable to map shared memory segment: ", name, "[",
                     strerror(errno), "]"));
  }

  // The fd can be closed after a call to mmap() without affecting the mapping.
  if (close(shm_fd) == -1) {
    LOG(WARNING) << "Failed to close shm_fd for '" << name << "'. "
                 << strerror(errno) << ". Continue anyways.";
  }

  // We use a placement new operator here to initialize the "raw" segment data
  // correctly.
  new (data) SegmentHeader(type_id);
  memory_segments_.insert({name, data});
  return absl::OkStatus();
}

uint8_t* SharedMemoryManager::GetRawHeader(const std::string& name) {
  return GetRawSegment(name);
}

uint8_t* SharedMemoryManager::GetRawValue(const std::string& name) {
  auto* data = GetRawSegment(name);
  if (data == nullptr) {
    return data;
  }
  return data + sizeof(SegmentHeader);
}

uint8_t* SharedMemoryManager::GetRawSegment(absl::string_view name) {
  auto result = memory_segments_.find(name);
  if (result == memory_segments_.end()) {
    return nullptr;
  }
  return result->second;
}

std::vector<std::string> SharedMemoryManager::GetRegisteredSegmentNames()
    const {
  std::vector<std::string> segment_names;
  segment_names.reserve(memory_segments_.size());
  for (const auto& [name, data_buffer] : memory_segments_) {
    segment_names.push_back(name);
  }
  return segment_names;
}

SegmentInfo SharedMemoryManager::GetSegmentInfo() const {
  return SegmentInfoFromHashMap(memory_segments_);
}

}  // namespace intrinsic::icon
