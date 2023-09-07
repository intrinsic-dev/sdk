// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>

#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"

namespace intrinsic::icon {

inline constexpr mode_t kShmMode = 0644;

bool MemorySegment::IsValid() const { return value_ != nullptr; }

std::string MemorySegment::Name() const { return name_; }

const SegmentHeader& MemorySegment::Header() const {
  // The header will stay valid throughout the lifetime of the memory segment,
  // so it's safe to reference it.
  return *header_;
}

absl::StatusOr<uint8_t*> MemorySegment::Get(const std::string& name,
                                            size_t segment_size) {
  auto shm_fd = shm_open(name.c_str(), O_RDWR, kShmMode);
  if (shm_fd == -1) {
    return absl::InternalError(
        absl::StrCat("Unable to open shared memory segment: ", name, " [",
                     strerror(errno), "]"));
  }

  uint8_t* data = static_cast<uint8_t*>(mmap(
      nullptr, segment_size, PROT_WRITE | PROT_READ, MAP_SHARED, shm_fd, 0));
  if (data == nullptr) {
    return absl::InternalError(
        absl::StrCat("Unable to map shared memory segment: ", name, " [",
                     strerror(errno), "]"));
  }

  // The fd can be closed after a call to mmap() without affecting the mapping.
  if (close(shm_fd) == -1) {
    LOG(WARNING) << "Failed to close shm_fd for '" << name << "'. "
                 << strerror(errno) << ". Continue anyways.";
  }

  return data;
}

MemorySegment::MemorySegment(absl::string_view name, uint8_t* segment)
    : name_(name),
      header_(reinterpret_cast<SegmentHeader*>(segment)),
      value_(segment + sizeof(SegmentHeader)) {}

MemorySegment::MemorySegment(const MemorySegment& other) noexcept
    : name_(other.name_), header_(other.header_), value_(other.value_) {}

MemorySegment::MemorySegment(MemorySegment&& other) noexcept
    : name_(std::exchange(other.name_, "")),
      header_(std::exchange(other.header_, nullptr)),
      value_(std::exchange(other.value_, nullptr)) {}

SegmentHeader* MemorySegment::HeaderPointer() { return header_; }

uint8_t* MemorySegment::Value() { return value_; }
const uint8_t* MemorySegment::Value() const { return value_; }

}  // namespace intrinsic::icon
