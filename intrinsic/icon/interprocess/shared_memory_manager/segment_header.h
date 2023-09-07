// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_HEADER_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_HEADER_H_

#include <semaphore.h>
#include <stddef.h>

#include <bitset>
#include <cstring>
#include <initializer_list>
#include <string>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/utils/clock.h"

namespace intrinsic::icon {

// SegmentHeader is meta information about the shared memory segment.
// Each allocated segment is offset by this header information before its actual
// payload.
// An example shared memory segment for a single `int` type would look like the
// following:
//
// [SegmentHeader][payload = int]
//
// The payload for the allocated `int` can thus be natively accessed by
// offsetting the shared memory segment by the size of this header struct.
//
// The SegmentHeader class is aligned to 64bit in order to guarantee a valid
// data representation across different platforms.
class alignas(64) SegmentHeader final {
 public:
  // The TypeInfo class contains convenience functions around the type string
  // associated with the shm segment payload.
  class alignas(64) TypeInfo {
   public:
    // The max size a type id can have.
    constexpr static size_t kMaxSize = 100;

    // Creates a new TypeInfo instance.
    explicit TypeInfo(const std::string& type_id) {
      std::memset(&type_id_, '\0', kMaxSize);
      size_t string_size =
          type_id.size() < kMaxSize ? type_id.size() : kMaxSize - 1;
      std::memcpy(&type_id_, type_id.c_str(), string_size);
      type_id_size_ = type_id.size();
    }

    // Returns the type id string.
    absl::string_view TypeID() const { return type_id_; }

    // Comparison operators.
    bool operator==(const TypeInfo& rhs) const {
      return type_id_size_ == rhs.type_id_size_ &&
             std::strcmp(type_id_, rhs.type_id_) == 0;
    }
    bool operator!=(const TypeInfo& rhs) const { return !(*this == rhs); }

   private:
    size_t type_id_size_;
    char type_id_[kMaxSize];
  };

  enum class Flags : int {
    // Creates an exclusively owned memory segment.
    // Indicates that the memory segment is exclusively created by a single
    // owner. The shared memory manager shall not repurpose or override the
    // shared memory segment if this flag is set.
    kExclusiveOwnership = 0,
  };

  // The SegmentHeader class is move-only.
  SegmentHeader() noexcept;
  explicit SegmentHeader(const std::string& type_id) noexcept;
  SegmentHeader(const std::string& type_id,
                const std::initializer_list<Flags>& flags) noexcept;
  SegmentHeader(const SegmentHeader& other) noexcept = delete;
  SegmentHeader& operator=(const SegmentHeader& other) noexcept = delete;
  SegmentHeader(SegmentHeader&& other) noexcept = default;
  SegmentHeader& operator=(SegmentHeader&& other) noexcept = default;
  ~SegmentHeader() noexcept;

  // Gets the current reference count of read-only access handles.
  int ReaderRefCount() const;
  // Increments the current reference count of read-only access handles.
  void IncrementReaderRefCount();
  // Decrements the current reference count of read-only access handles.
  void DecrementReaderRefCount();

  // Gets the current reference count of writer access handles.
  int WriterRefCount() const;
  // Increments the current reference count of writer access handles.
  void IncrementWriterRefCount();
  // Decrements the current reference count of writer access handles.
  void DecrementWriterRefCount();

  // Returns the type information for this segment.
  TypeInfo Type() const;

  // Queries if a specified flag is set.
  bool FlagIsSet(Flags flag) const;

  // Returns intrinsic::Clock::Zero() if no update has occurred yet.
  Time LastUpdatedTime() const;

  // Returns the number of updates made to the segment.
  int64_t NumUpdates() const;

  // Sets the time the associated segment was updated and increments the number
  // of updates.
  //
  // Important: Typically, the time passed should be obtained from a monotonic
  // clock to ensure there is no bad behavior caused by the clock changing in
  // unexpected ways (for example, going backwards in time).
  void UpdatedAt(Time time);

 private:
  // Unnamed process-shared semaphore to protect header modifications.
  mutable sem_t mutex_;

  // A reference counter on read-only access handles.
  int ref_count_reader_ = 0;

  // A reference counter on writer access handles.
  int ref_count_writer_ = 0;

  // The type information associated with that segment.
  TypeInfo type_info_;

  // Bitmask for single bit flags.
  std::bitset<8> flags_;

  // Time for the last time the segment was updated. This is used to detect
  // stale information in segments.
  //
  // It is up to the user of the segment to mark when it is updated. This
  // reduces the number of times we need to grab the clock, for example, the
  // user might record the time once at the start of a cycle, and use the same
  // time when updating all segments.
  Time last_updated_time_ = Clock::Zero();

  // Counter for updates to the segment. This is used by the reader to detect
  // missed updates.
  //
  // Given that a segment can contain arbitrary data, we won't make assumptions
  // about the access to the segment, and instead allow the writer of the
  // segment to tick it when appropriate.
  int64_t update_counter_ = 0;
};

template <class T>
struct SegmentTraits {
  static constexpr size_t kSegmentSize = sizeof(SegmentHeader) + sizeof(T);
  static constexpr size_t kDataOffset = sizeof(SegmentHeader);
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_HEADER_H_
