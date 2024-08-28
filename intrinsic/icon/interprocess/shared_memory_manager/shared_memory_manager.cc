// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

inline constexpr mode_t kShmMode = 0644;
// Max string size as defined in `segment_info.fbs`
inline constexpr uint32_t kMaxSegmentStringSize = 255;
inline constexpr uint32_t kMaxSegmentSize = 200;

namespace {
absl::Status VerifyName(absl::string_view name) {
  if (name.empty()) {
    return absl::InvalidArgumentError("Shm segment name cannot be empty.");
  }
  if (name[0] != '/') {
    return absl::InvalidArgumentError(absl::StrCat(
        "Shm segment name \"", name, "\" must start with a forward slash."));
  }
  if (name.size() >= kMaxSegmentStringSize) {
    return absl::InvalidArgumentError(
        absl::StrCat("Shm segment name \"", name, "\" can't exceed ",
                     (kMaxSegmentStringSize - 1), " characters."));
  }
  if (std::find(name.begin() + 1, name.end(), '/') != name.end()) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Shm segment name \"", name,
        "\" can't have further forward slashes except the first one."));
  }

  return absl::OkStatus();
}

absl::Status VerifyName(const MemoryName& name) {
  return VerifyName(name.GetName());
}

SegmentInfo SegmentInfoFromHashMap(
    const absl::flat_hash_map<
        MemoryName, SharedMemoryManager::MemorySegmentInfo>& segments) {
  SegmentInfo segment_info(segments.size());
  uint32_t index = 0;
  for (const auto& [memory_name, buf] : segments) {
    SegmentName segment;
    segment.mutate_must_be_used(buf.must_be_used);
    // fbs doesn't have char as datatype, only int8_t which is byte compatible.
    auto* data = reinterpret_cast<char*>(segment.mutable_value()->Data());
    std::memset(data, '\0', kMaxSegmentStringSize);
    absl::SNPrintF(data, kMaxSegmentStringSize, "%s", memory_name.GetName());
    segment_info.mutable_names()->Mutate(index, segment);
    ++index;
  }

  return segment_info;
}
}  // namespace

SharedMemoryManager::~SharedMemoryManager() {
  // unlink all created shm segments
  for (const auto& segment : memory_segments_) {
    auto* header = reinterpret_cast<SegmentHeader*>(segment.second.data);
    // We've used placement new during the initialization. We have to call the
    // destructor explicitly to cleanup.
    header->~SegmentHeader();
    shm_unlink(segment.first.GetName());
  }
}

const SegmentHeader* SharedMemoryManager::GetSegmentHeader(
    const MemoryName& name) {
  uint8_t* header = GetRawHeader(name);
  return reinterpret_cast<SegmentHeader*>(header);
}

absl::Status SharedMemoryManager::InitSegment(const MemoryName& name,
                                              bool must_be_used,
                                              size_t segment_size,
                                              const std::string& type_id) {
  if (memory_segments_.size() >= kMaxSegmentSize) {
    return absl::ResourceExhaustedError(
        absl::StrCat("Unable to add \"", name.GetName(), "\". Max size of ",
                     kMaxSegmentSize, " segments exceeded."));
  }
  if (type_id.size() > SegmentHeader::TypeInfo::kMaxSize) {
    return absl::InvalidArgumentError(
        absl::StrCat("Type id [", type_id, "] exceeds max size of [",
                     SegmentHeader::TypeInfo::kMaxSize, "]."));
  }
  if (memory_segments_.contains(name)) {
    return absl::AlreadyExistsError(
        absl::StrCat("Shm segment \"", name.GetName(), "\" exists already."));
  }
  INTR_RETURN_IF_ERROR(VerifyName(name));

  auto shm_fd = shm_open(name.GetName(), O_CREAT | O_EXCL | O_RDWR, kShmMode);
  bool reusing_segment = false;
  if (shm_fd == -1 && errno == EEXIST) {
    LOG(WARNING) << "The shared memory segment \"" << name.GetName()
                 << "\" already exists. It will be reused.";
    shm_fd = shm_open(name.GetName(), O_CREAT | O_RDWR, kShmMode);
    reusing_segment = true;
  }
  if (shm_fd == -1) {
    return absl::InternalError(
        absl::StrCat("Unable to open shared memory segment \"", name.GetName(),
                     "\" with error: ", strerror(errno), "."));
  }

  if (reusing_segment) {
    // Checks the size of the existing segment as additional safeguard against
    // version mismatches.
    struct stat file_attributes;
    if (fstat(shm_fd, &file_attributes) == -1) {
      return absl::InternalError(absl::StrCat(
          "Fstat failed for shared memory segment \"", name.GetName(),
          "\" with error: ", strerror(errno), "."));
    }
    if (file_attributes.st_size != segment_size) {
      LOG(ERROR) << "Size mismatch for existing shared memory segment \""
                 << name.GetName() << "\" Expected " << segment_size
                 << " bytes got " << file_attributes.st_size
                 << " bytes. This can be caused by a version mismatch between "
                    "resources. Ensure you are using the latest version of all "
                    "resources involved.";
      // return absl::FailedPreconditionError(absl::StrCat(
      //     "Size mismatch for existing shared memory segment \"",
      //     name.GetName(),
      //     "\" Expected ", segment_size, " bytes got ",
      //     file_attributes.st_size, " bytes. This can be caused by a version
      //     mismatch between resources. " "Ensure you are using the latest
      //     version of all resources " "involved."));
      //   }
      // } else if (ftruncate(shm_fd, segment_size) == -1) {
      //   // Resizes new shm segments.
      //   return absl::InternalError(
      //       absl::StrCat("Unable to resize shared memory segment \"",
      //                    name.GetName(), "\" with error: ", strerror(errno),
      //                    "."));
    }
  }
  if (ftruncate(shm_fd, segment_size) == -1) {
    // Resizes new shm segments.
    return absl::InternalError(
        absl::StrCat("Unable to resize shared memory segment \"",
                     name.GetName(), "\" with error: ", strerror(errno), "."));
  }
  auto* data = static_cast<uint8_t*>(mmap(
      nullptr, segment_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0));
  if (data == nullptr) {
    return absl::InternalError(
        absl::StrCat("Unable to map shared memory segment \"", name.GetName(),
                     "\" with error: ", strerror(errno), "."));
  }

  // The fd can be closed after a call to mmap() without affecting the
  // mapping.
  if (close(shm_fd) == -1) {
    LOG(WARNING) << "Failed to close shm_fd for \"" << name.GetName()
                 << "\". with error: " << strerror(errno)
                 << ". Continuing anyways.";
  }

  if (reusing_segment) {
    // Checks the version information of the header. fd is already closed so
    // we can simply return an error.
    const auto* existing_header = reinterpret_cast<const SegmentHeader*>(data);
    QCHECK_NE(existing_header, nullptr);
    // No segfault because the version is the first member.
    const size_t expected_version = SegmentHeader::ExpectedVersion();
    const size_t existing_version = existing_header->Version();
    if (expected_version != existing_version) {
      LOG(ERROR) << "Incompatible version of shared memory segment \""
                 << name.GetName() << "\" Expected [" << expected_version
                 << "] got [" << existing_version
                 << "]. Ensure you are using the latest version of all "
                    "resources involved.";
    }
  }

  // We use a placement new operator here to initialize the "raw" segment
  // data correctly.
  new (data) SegmentHeader(type_id);
  memory_segments_.insert({name, {.data = data, .must_be_used = must_be_used}});
  return absl::OkStatus();
}

uint8_t* SharedMemoryManager::GetRawHeader(const MemoryName& name) {
  return GetRawSegment(name);
}

uint8_t* SharedMemoryManager::GetRawValue(const MemoryName& name) {
  auto* data = GetRawSegment(name);
  if (data == nullptr) {
    return data;
  }
  return data + sizeof(SegmentHeader);
}

uint8_t* SharedMemoryManager::GetRawSegment(const MemoryName& name) {
  auto result = memory_segments_.find(name);
  if (result == memory_segments_.end()) {
    return nullptr;
  }
  return result->second.data;
}

std::vector<MemoryName> SharedMemoryManager::GetRegisteredMemoryNames() const {
  std::vector<MemoryName> result;
  result.reserve(memory_segments_.size());
  for (const auto& [name, unused] : memory_segments_) {
    result.push_back(name);
  }
  return result;
}

SegmentInfo SharedMemoryManager::GetSegmentInfo() const {
  return SegmentInfoFromHashMap(memory_segments_);
}

}  // namespace intrinsic::icon
