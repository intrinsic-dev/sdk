// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_

#include <stddef.h>
#include <stdint.h>

#include <string>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

// Base class for handling a generic, untyped shared memory segment.
// Each memory segment has to be created and initialized by a
// `SharedMemoryManager`. The Read-Only as well as Read-Write memory segment
// classes below only provide an access handle to these segments, but don't
// create these.
class MemorySegment {
 public:
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

 protected:
  MemorySegment() = default;

  // Accesses the shared memory location with `name`.
  // Returns a pointer to the untyped memory segment and maps it into
  // user-space.
  // Returns NotFoundError if the shared memory segment with the given
  // name is not in `segment_name_to_file_descriptor_map` e.g. not previously
  // allocated by a `SharedMemoryManager`.
  // Returns InternalError if mapping the segment fails.
  static absl::StatusOr<uint8_t*> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view name, size_t segment_size);

  // Returns the SegmentHeader of the shared memory segment.
  SegmentHeader* HeaderPointer();

  // Returns the raw, untyped value of the shared memory segment.
  uint8_t* Value();
  const uint8_t* Value() const;

  MemorySegment(absl::string_view name, uint8_t* segment);
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
};

// Read-Only access to a shared memory segment of type `T`.
template <class T>
class ReadOnlyMemorySegment final : public MemorySegment {
 public:
  // Gets read-only access to a shared memory segment called `segment_name`.
  // Returns NotFoundError if the shared memory segment with the given
  // name is not in `segment_name_to_file_descriptor_map` e.g. not previously
  // allocated by a `SharedMemoryManager`.
  // Returns InternalError if mapping the segment fails.
  static absl::StatusOr<ReadOnlyMemorySegment> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view segment_name) {
    INTR_ASSIGN_OR_RETURN(
        uint8_t* segment,
        MemorySegment::Get(segment_name_to_file_descriptor_map, segment_name,
                           SegmentTraits<T>::kSegmentSize));
    return ReadOnlyMemorySegment<T>(segment_name, segment);
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
  ReadOnlyMemorySegment(absl::string_view name, uint8_t* segment)
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
  // Returns InternalError if mapping the segment fails.
  static absl::StatusOr<ReadWriteMemorySegment> Get(
      const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
      absl::string_view segment_name) {
    INTR_ASSIGN_OR_RETURN(
        uint8_t* segment,
        MemorySegment::Get(segment_name_to_file_descriptor_map, segment_name,
                           SegmentTraits<T>::kSegmentSize));
    return ReadWriteMemorySegment<T>(segment_name, segment);
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
  ReadWriteMemorySegment(absl::string_view name, uint8_t* segment)
      : MemorySegment(name, segment) {
    HeaderPointer()->IncrementWriterRefCount();
  }
};

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
