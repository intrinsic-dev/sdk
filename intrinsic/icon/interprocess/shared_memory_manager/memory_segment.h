// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_

#include <stddef.h>
#include <stdint.h>

#include <string>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

// Each memory segment has to be created and initialized by a
// `SharedMemoryManager`. The Read-Only as well as Read-Write memory segment
// classes below only provide an access handle to these segments, but don't
// create these.
class MemorySegment {
 public:
  // Shared memory layout is: SegmentHeader | Data.
  struct SegmentDescriptor {
    // The starting address of the shared memory segment. Points to the
    // SegmentHeader.
    // Shared memory layout is described in:
    // intrinsic/icon/interprocess/shared_memory_manager/segment_header.h
    uint8_t* segment_start;
    // The size of the shared memory segment. This is the size of the entire
    // segment, including the SegmentHeader.
    size_t size;
  };

  // Returns whether the memory segment is initialized and points to a valid
  // shared memory location. Returns false if the segment class is default
  // constructed.
  bool IsValid() const;

  // Returns the name of the shared memory segment.
  std::string Name() const;

  // Returns the header information of the shared memory segment.
  const SegmentHeader& Header() const;

  // Marks the time that the segment was updated.
  // 'current_cycle' is the control cycle that the segment was updated.
  void UpdatedAt(Time time, uint64_t current_cycle) {
    HeaderPointer()->UpdatedAt(time, current_cycle);
  }

  // Returns the size of the value stored in the shared memory segment.
  // Returns 0 if the segment is invalid.
  size_t ValueSize() const;

 protected:
  MemorySegment() = default;

  // Accesses the shared memory location with `name` and maps it into
  // user-space.
  // Returns the pointer and the size of the shared memory segment.
  // Returns NotFoundError if the shared memory segment with the given
  // name is not in `segment_name_to_file_descriptor_map` e.g. not previously
  // allocated by a `SharedMemoryManager`.
  // Returns InternalError if mapping the segment fails, or if the size of the
  // segment is too small to hold a SegmentHeader and at least one byte of
  // payload.
  static absl::StatusOr<SegmentDescriptor> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view name);

  // Returns the SegmentHeader of the shared memory segment.
  SegmentHeader* HeaderPointer();

  // Returns the raw, untyped value of the shared memory segment.
  uint8_t* Value();
  const uint8_t* Value() const;

  MemorySegment(absl::string_view name, SegmentDescriptor segment);
  MemorySegment(const MemorySegment& other) noexcept;
  MemorySegment& operator=(const MemorySegment& other) noexcept = default;
  MemorySegment(MemorySegment&& other) noexcept;
  MemorySegment& operator=(MemorySegment&& other) noexcept = default;

 private:
  std::string name_ = "";

  // The segment header as well as the actual payload (value) are located in the
  // same shared memory segment. We separate the pointers by a simple offset.
  SegmentHeader* header_ = nullptr;
  uint8_t* value_ = nullptr;
  // The size of the shared memory segment. This is the size of the entire
  // segment, including the SegmentHeader.
  size_t size_ = 0;
};

// Checks that the size of the shared memory segment is big enough to
// hold a SegmentHeader and at least sizeof(T) bytes.
// This check is only accurate for trivially_copyable data types like flatbuffer
// structs. The validity of flatbuffer tables is checked in
// intrinsic/icon/hal/get_hardware_interface.h.
// The parameter `segment_size` is the size of the entire
// shared memory segment, including the SegmentHeader.
// The parameter `segment_name` is only used for error reporting.
// Returns InternalError if `segment_size` is too small to hold <T>.
template <class T>
absl::Status SharedMemorySegmentFitsLowerSizeBound(
    absl::string_view segment_name, size_t segment_size) {
  const size_t minimal_size = sizeof(T) + sizeof(SegmentHeader);
  if (segment_size < minimal_size) {
    return absl::InternalError(absl::StrCat(
        "Shared memory segment '", segment_name, "' of size ", segment_size,
        "bytes must be >= ", minimal_size,
        "bytes. This can be due to a version mismatch of your resources."));
  }
  return absl::OkStatus();
}

// Read-Only access to a shared memory segment of type `T`.
template <class T>
class ReadOnlyMemorySegment final : public MemorySegment {
 public:
  // Gets read-only access to a shared memory segment called `segment_name`.
  // Returns NotFoundError if the shared memory segment with the given
  // name is not in `segment_name_to_file_descriptor_map` e.g. not previously
  // allocated by a `SharedMemoryManager`.
  // Returns InternalError if mapping the segment fails, or if the size of the
  // segment is too small to hold a SegmentHeader and at least sizeof(T) bytes.
  static absl::StatusOr<ReadOnlyMemorySegment> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view segment_name) {
    INTR_ASSIGN_OR_RETURN(
        SegmentDescriptor segment_info,
        MemorySegment::Get(segment_name_to_file_descriptor_map, segment_name));
    INTR_RETURN_IF_ERROR(SharedMemorySegmentFitsLowerSizeBound<T>(
        segment_name, segment_info.size));

    return ReadOnlyMemorySegment<T>(segment_name, segment_info);
  }

  ReadOnlyMemorySegment() = default;
  ReadOnlyMemorySegment(const ReadOnlyMemorySegment& other) noexcept
      : MemorySegment(other) {
    HeaderPointer()->IncrementReaderRefCount();
  }
  ReadOnlyMemorySegment& operator=(
      const ReadOnlyMemorySegment& other) noexcept = default;
  ReadOnlyMemorySegment(ReadOnlyMemorySegment&& other) noexcept = default;
  ReadOnlyMemorySegment& operator=(ReadOnlyMemorySegment&& other) noexcept =
      default;
  ~ReadOnlyMemorySegment() {
    if (HeaderPointer()) {
      HeaderPointer()->DecrementReaderRefCount();
    }
  }

  // Accesses the value of the shared memory segment.
  const T& GetValue() const { return *reinterpret_cast<const T*>(Value()); }
  const uint8_t* GetRawValue() const { return Value(); }

 private:
  ReadOnlyMemorySegment(absl::string_view name, SegmentDescriptor segment)
      : MemorySegment(name, segment) {
    HeaderPointer()->IncrementReaderRefCount();
  }
};

// Read-Write access to a shared memory segment of type `T`.
// The Read-Write is thread-compatible, however there is currently no
// concurrency model implemented, which means that multiple writers are
// potentially introducing a data race when trying to update the same shared
// memory segments at the same time. Note that depending on the data type of the
// shared memory segment, there might also be a race between a single writer and
// a single reader in which the reader might potentially read an inconsistent
// value while the writer updates it. It's therefore the application's
// responsibility to guarantee a safe execution when featuring multiple writers.
template <class T>
class ReadWriteMemorySegment final : public MemorySegment {
 public:
  // Gets read-write access to a shared memory segment called `segment_name`.
  // Returns NotFoundError if the shared memory segment with the given
  // name is not in `segment_name_to_file_descriptor_map` e.g. not previously
  // allocated by a `SharedMemoryManager`.
  // Returns InternalError if mapping the segment fails, or if the size of the
  // segment is too small to hold a SegmentHeader and at least sizeof(T) bytes.
  static absl::StatusOr<ReadWriteMemorySegment> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view segment_name) {
    INTR_ASSIGN_OR_RETURN(
        SegmentDescriptor segment_info,
        MemorySegment::Get(segment_name_to_file_descriptor_map, segment_name));

    INTR_RETURN_IF_ERROR(SharedMemorySegmentFitsLowerSizeBound<T>(
        segment_name, segment_info.size));

    return ReadWriteMemorySegment<T>(segment_name, segment_info);
  }

  ReadWriteMemorySegment() = default;
  ReadWriteMemorySegment(const ReadWriteMemorySegment& other) noexcept
      : MemorySegment(other) {
    HeaderPointer()->IncrementWriterRefCount();
  }
  ReadWriteMemorySegment& operator=(
      const ReadWriteMemorySegment& other) noexcept = default;
  ReadWriteMemorySegment(ReadWriteMemorySegment&& other) noexcept = default;
  ReadWriteMemorySegment& operator=(ReadWriteMemorySegment&& other) noexcept =
      default;
  ~ReadWriteMemorySegment() {
    if (HeaderPointer()) {
      HeaderPointer()->DecrementWriterRefCount();
    }
  }

  // Accesses the value of the shared memory segment.
  T& GetValue() { return *reinterpret_cast<T*>(Value()); }
  const T& GetValue() const { return *reinterpret_cast<const T*>(Value()); }
  uint8_t* GetRawValue() { return Value(); }
  const uint8_t* GetRawValue() const { return Value(); }

  // Updates the value of the shared memory segment.
  void SetValue(const T& value) { *reinterpret_cast<T*>(Value()) = value; }

 private:
  ReadWriteMemorySegment(absl::string_view name, SegmentDescriptor segment)
      : MemorySegment(name, segment) {
    HeaderPointer()->IncrementWriterRefCount();
  }
};

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
