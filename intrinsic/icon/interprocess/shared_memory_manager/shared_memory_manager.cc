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
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/memory/memory.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/flatbuffers/flatbuffer_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

using ::intrinsic_fbs::FlatbufferArrayNumElements;

// Max string size as defined in `segment_info.fbs`
inline constexpr size_t kMaxSegmentStringSize =
    FlatbufferArrayNumElements(&intrinsic::icon::SegmentName::value);

inline constexpr size_t kMaxNumberOfSegments =
    FlatbufferArrayNumElements(&intrinsic::icon::SegmentInfo::names);

namespace {
absl::Status VerifyName(absl::string_view name) {
  if (name.empty()) {
    return absl::InvalidArgumentError("Shm segment name cannot be empty.");
  }
  if (name.size() >= kMaxSegmentStringSize) {
    return absl::InvalidArgumentError(
        absl::StrCat("Shm segment name \"", name, "\" can't exceed ",
                     (kMaxSegmentStringSize - 1), " characters."));
  }

  if (std::find(name.begin(), name.end(), '/') != name.end()) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Shm segment name \"", name, "\" can't have forward slashes."));
  }

  return absl::OkStatus();
}

SegmentInfo SegmentInfoFromHashMap(
    const absl::flat_hash_map<
        std::string, SharedMemoryManager::MemorySegmentInfo>& segments) {
  SegmentInfo segment_info(segments.size());
  uint32_t index = 0;
  for (const auto& [memory_name, buf] : segments) {
    SegmentName segment;
    segment.mutate_must_be_used(buf.must_be_used);
    // fbs doesn't have char as datatype, only int8_t which is byte compatible.
    auto* data = reinterpret_cast<char*>(segment.mutable_value()->Data());
    std::memset(data, '\0', kMaxSegmentStringSize);
    absl::SNPrintF(data, kMaxSegmentStringSize, "%s", memory_name);
    segment_info.mutable_names()->Mutate(index, segment);
    ++index;
  }

  return segment_info;
}
}  // namespace

SharedMemoryManager::SharedMemoryManager(
    absl::string_view module_name, absl::string_view shared_memory_namespace)
    : module_name_(std::string(module_name)),
      shared_memory_namespace_(std::string(shared_memory_namespace)) {}

// static
absl::StatusOr<std::unique_ptr<SharedMemoryManager>>
SharedMemoryManager::Create(absl::string_view shared_memory_namespace,
                            absl::string_view module_name) {
  if (module_name.empty()) {
    return absl::InvalidArgumentError("Module name can't be empty.");
  }

  return absl::WrapUnique(new SharedMemoryManager(
      /*module_name=*/module_name,
      /*shared_memory_namespace=*/shared_memory_namespace));
}

SharedMemoryManager::~SharedMemoryManager() {
  // unlink all created shm segments
  for (const auto& segment : memory_segments_) {
    auto* header = reinterpret_cast<SegmentHeader*>(segment.second.data);
    int fd = segment.second.fd;
    const std::string segment_name = segment.first;

    // We've used placement new during the initialization. We have to call the
    // destructor explicitly to cleanup.
    header->~SegmentHeader();

    if (close(fd) == -1) {
      LOG(WARNING) << "Failed to close shm_fd for '" << segment_name
                   << "'. with error: " << strerror(errno)
                   << ". Continuing anyways.";
    }
    if (segment.second.data != nullptr) {
      if (munmap(segment.second.data, segment.second.length) == -1) {
        LOG(WARNING) << "Failed to unmap memory for '" << segment_name
                     << "'. with error: " << strerror(errno)
                     << ". Continuing anyways.";
      }
    }
  }
}

const SegmentHeader* SharedMemoryManager::GetSegmentHeader(
    absl::string_view name) {
  uint8_t* header = GetRawSegment(name);
  return reinterpret_cast<SegmentHeader*>(header);
}

absl::Status SharedMemoryManager::InitSegment(absl::string_view name,
                                              bool must_be_used,
                                              size_t payload_size,
                                              const std::string& type_id) {
  if (memory_segments_.size() >= kMaxNumberOfSegments) {
    return absl::ResourceExhaustedError(
        absl::StrCat("Unable to add \"", name, "\". Max number of segments (",
                     kMaxNumberOfSegments, ") exceeded."));
  }
  if (type_id.size() > SegmentHeader::TypeInfo::kMaxSize) {
    return absl::InvalidArgumentError(
        absl::StrCat("Type id [", type_id, "] exceeds max size of [",
                     SegmentHeader::TypeInfo::kMaxSize, "]."));
  }
  if (memory_segments_.contains(name)) {
    return absl::AlreadyExistsError(
        absl::StrCat("Shm segment \"", name, "\" exists already."));
  }
  INTR_RETURN_IF_ERROR(VerifyName(name));

  // Creates an anonymous memory segment and stores the fd
  // https://man7.org/linux/man-pages/man2/memfd_create.2.html
  // Default flags are O_RDWR | O_LARGEFILE.
  int shm_fd = memfd_create(name.data(), 0);
  if (shm_fd == -1) {
    return absl::InternalError(
        absl::StrCat("Failed to create shm segment \"", name,
                     "\" with error: ", strerror(errno), "."));
  }

  const auto segment_size = sizeof(SegmentHeader) + payload_size;
  if (ftruncate(shm_fd, segment_size) == -1) {
    // Resizes new shm segments.
    return absl::InternalError(
        absl::StrCat("Unable to resize shared memory segment \"", name,
                     "\" with error: ", strerror(errno), "."));
  }

  struct stat shared_memory_stats;
  if (fstat(shm_fd, &shared_memory_stats) != 0) {
    // Return an error and forward errno
    return absl::InternalError(
        absl::StrCat("Failed to read size of segment \"", name,
                     "\". 'fstat' failed with:", strerror(errno)));
  }
  // The opening logic depends on the size of the segment.
  if (shared_memory_stats.st_size != segment_size) {
    return absl::InternalError(absl::StrCat(
        "The size of the shared memory segment \"", name, "\" of ",
        shared_memory_stats.st_size, "bytes is not the expected size of ",
        segment_size, "bytes."));
  }

  auto* data =
      static_cast<uint8_t*>(mmap(nullptr, segment_size, PROT_READ | PROT_WRITE,
                                 MAP_SHARED | MAP_LOCKED, shm_fd, 0));
  if (data == nullptr || data == MAP_FAILED) {
    return absl::InternalError(
        absl::StrCat("Unable to map shared memory segment \"", name,
                     "\" with error: ", strerror(errno), "."));
  }

  // Additionally locking the pages as recommended by
  // https://man7.org/linux/man-pages/man2/mmap.2.html, because major faults are
  // not acceptable after the initialization of the mapping.
  if (mlock(/*__addr=*/data, /*__len=*/segment_size) != 0) {
    return absl::InternalError(
        absl::StrCat("Unable to mlock shared memory segment \"", name,
                     "\" with error: ", strerror(errno), "."));
  }

  const std::string name_str(name);
  segment_name_to_file_descriptor_map_.insert({name_str, shm_fd});
  // We use a placement new operator here to initialize the "raw" segment
  // data correctly.
  new (data) SegmentHeader(type_id);
  memory_segments_.insert({
      name_str,
      {
          .data = data,
          .length = segment_size,
          .must_be_used = must_be_used,
          .fd = shm_fd,
      },
  });
  return absl::OkStatus();
}

uint8_t* SharedMemoryManager::GetRawValue(absl::string_view name) {
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
  return result->second.data;
}

std::vector<std::string> SharedMemoryManager::GetRegisteredMemoryNames() const {
  std::vector<std::string> result;
  result.reserve(memory_segments_.size());
  for (const auto& [name, unused] : memory_segments_) {
    result.push_back(name);
  }
  return result;
}

std::string SharedMemoryManager::ModuleName() const { return module_name_; }

std::string SharedMemoryManager::SharedMemoryNamespace() const {
  return shared_memory_namespace_;
}

SegmentInfo SharedMemoryManager::GetSegmentInfo() const {
  return SegmentInfoFromHashMap(memory_segments_);
}

}  // namespace intrinsic::icon
