// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_

#include <stddef.h>
#include <stdint.h>

#include <string>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {
namespace hal {
static constexpr char kDelimiter[] = "__";
}  // namespace hal

// A strong type for filenames of shared memory segments. Ensures that the
// filename follows a pattern "/namespacemodule__operation" and this format is
// defined only here.
struct MemoryName {
  MemoryName(absl::string_view shm_namespace, absl::string_view module_name) {
    name = absl::StrFormat("/%s%s", shm_namespace, module_name);
  }
  MemoryName(absl::string_view shm_namespace, absl::string_view module_name,
             absl::string_view operation) {
    name = absl::StrFormat("/%s%s%s%s", shm_namespace, module_name,
                           hal::kDelimiter, operation);
  }
  const char* GetName() const { return name.c_str(); }
  void Append(absl::string_view suffix) { name.append(suffix); }
  template <typename H>
  friend H AbslHashValue(H h, const MemoryName& m) {
    return H::combine(std::move(h), m.name);
  }
  bool operator==(const MemoryName& rhs) const {
    return (this->name == rhs.name);
  }

 private:
  std::string name;
};

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

  // Access the shared memory location.
  // Returns a pointer to the untyped memory segment and maps it into
  // user-space. Fails if the shared memory segment with the given name was not
  // previously allocated by the `SharedMemoryManager`.
  static absl::StatusOr<uint8_t*> Get(const MemoryName& name, size_t size);

  // Returns the SegmentHeader of the shared memory segment.
  SegmentHeader* HeaderPointer();

  // Returns the raw, untyped value of the shared memory segment.
  uint8_t* Value();
  const uint8_t* Value() const;

  MemorySegment(const MemoryName& name, uint8_t* segment);
  MemorySegment(const MemorySegment& other) noexcept;
  MemorySegment& operator=(const MemorySegment& other) noexcept = default;
  MemorySegment(MemorySegment&& other) noexcept;
  MemorySegment& operator=(MemorySegment&& other) noexcept = default;

 private:
  MemoryName name_ = MemoryName("", "");

  // The segment header as well as the actual payload (value) are located in the
  // same shared memory segment. We separate the pointers by a simple offset.
  SegmentHeader* header_ = nullptr;
  uint8_t* value_ = nullptr;
};

// Read-Only access to a shared memory segment of type `T`.
template <class T>
class ReadOnlyMemorySegment final : public MemorySegment {
 public:
  // Gets read-only access to a shared memory segment specified by a name.
  // Returns `absl::InternalError` if a POSIX call to access the shared memory
  // failed.
  static absl::StatusOr<ReadOnlyMemorySegment> Get(const MemoryName& name) {
    INTR_ASSIGN_OR_RETURN(
        uint8_t* segment,
        MemorySegment::Get(name, SegmentTraits<T>::kSegmentSize));
    return ReadOnlyMemorySegment<T>(name, segment);
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
  ReadOnlyMemorySegment(const MemoryName& name, uint8_t* segment)
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
// responsiblity to guarantee a safe execution when featuring multiple writers.
template <class T>
class ReadWriteMemorySegment final : public MemorySegment {
 public:
  // Gets read-write access to a shared memory segment specified by a name.
  // Returns `absl::InternalError` if a POSIX call to access the shared memory
  // failed.
  static absl::StatusOr<ReadWriteMemorySegment> Get(const MemoryName& name) {
    INTR_ASSIGN_OR_RETURN(
        uint8_t* segment,
        MemorySegment::Get(name, SegmentTraits<T>::kSegmentSize));
    return ReadWriteMemorySegment<T>(name, segment);
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
  ReadWriteMemorySegment(const MemoryName& name, uint8_t* segment)
      : MemorySegment(name, segment) {
    HeaderPointer()->IncrementWriterRefCount();
  }
};

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_MEMORY_SEGMENT_H_
