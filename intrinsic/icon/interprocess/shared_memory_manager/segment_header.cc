// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"

#include <semaphore.h>

#include <initializer_list>
#include <string>

#include "absl/log/log.h"
#include "intrinsic/icon/utils/log.h"

namespace intrinsic::icon {
namespace {
void IncrementRefCount(int& counter, sem_t* mutex) {
  sem_wait(mutex);
  ++counter;
  sem_post(mutex);
}

void DecrementRefCount(int& counter, sem_t* mutex) {
  sem_wait(mutex);
  // A reference counter can't be lower than zero.
  if (counter > 0) {
    --counter;
  }
  sem_post(mutex);
}
}  // namespace

SegmentHeader::SegmentHeader() noexcept : SegmentHeader("UNDEFINED") {}

SegmentHeader::SegmentHeader(const std::string& type_id) noexcept
    : type_info_(TypeInfo(type_id)), flags_(0) {
  // Initialize the unnamed semaphore as process-shared by setting second
  // argument to non-zero. See
  // https://man7.org/linux/man-pages/man3/sem_init.3.html for details.
  // We can feature an unnamed semaphore here as this header information will
  // be part of the shared memory segment and thus shared between multiple
  // processes.
  sem_init(&mutex_, 1, 1);
}

SegmentHeader::SegmentHeader(const std::string& type_id,
                             const std::initializer_list<Flags>& flags) noexcept
    : SegmentHeader(type_id) {
  for (const auto flag : flags) {
    flags_.set(static_cast<int>(flag));
  }
}

SegmentHeader::~SegmentHeader() noexcept {
  if (ref_count_reader_ != 0 || ref_count_writer_ != 0) {
    LOG(WARNING) << "Shared memory segment cleaned up while being used by "
                 << (ref_count_reader_ + ref_count_writer_)
                 << " other entities.";
  }

  flags_.reset();
  sem_destroy(&mutex_);
}

int SegmentHeader::ReaderRefCount() const { return ref_count_reader_; }
void SegmentHeader::IncrementReaderRefCount() {
  IncrementRefCount(ref_count_reader_, &mutex_);
}
void SegmentHeader::DecrementReaderRefCount() {
  DecrementRefCount(ref_count_reader_, &mutex_);
}

int SegmentHeader::WriterRefCount() const { return ref_count_writer_; }
void SegmentHeader::IncrementWriterRefCount() {
  return IncrementRefCount(ref_count_writer_, &mutex_);
}
void SegmentHeader::DecrementWriterRefCount() {
  return DecrementRefCount(ref_count_writer_, &mutex_);
}

SegmentHeader::TypeInfo SegmentHeader::Type() const { return type_info_; }

bool SegmentHeader::FlagIsSet(SegmentHeader::Flags flag) const {
  return flags_.test(static_cast<int>(flag));
}

Time SegmentHeader::LastUpdatedTime() const { return last_updated_time_; }

int64_t SegmentHeader::NumUpdates() const { return update_counter_; }

void SegmentHeader::UpdatedAt(Time time) {
  if (time < last_updated_time_) {
    INTRINSIC_RT_LOG_THROTTLED(WARNING)
        << "Update for segment of type: " << type_info_.TypeID()
        << " goes backwards in time.";
  }
  last_updated_time_ = time;
  update_counter_++;
}
}  // namespace intrinsic::icon
