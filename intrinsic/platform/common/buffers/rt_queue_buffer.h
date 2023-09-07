// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_BUFFER_H_
#define INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_BUFFER_H_

#include <atomic>
#include <cstddef>
#include <memory>

#include "absl/base/attributes.h"
#include "absl/functional/function_ref.h"
#include "absl/log/check.h"
#include "absl/memory/memory.h"
#include "absl/types/optional.h"

// IWYU pragma: no_forward_declare absl::FunctionRef

namespace intrinsic {
namespace internal {

// A buffer for performing spsc-queue style automatic operations.
template <typename T>
class RtQueueBuffer {
 public:
  explicit RtQueueBuffer(size_t capacity);

  RtQueueBuffer(size_t capacity, absl::FunctionRef<void(T*)> init_function);

  // Gets a pointer to the front element, or nullptr if empty. After a call to
  // Front(), must call DropFront() or KeepFront() prior to subsequent calls to
  // Front().
  ABSL_MUST_USE_RESULT T* Front();

  // Removes the front element; no-op if the queue is empty.
  void DropFront();

  // Keeps the front element.
  void KeepFront();

  // Gets a pointer to the next available element, or nullptr if the queue is
  // full. The element should be set and then FinishInsert must be called.
  ABSL_MUST_USE_RESULT T* PrepareInsert();

  // Make the element referenced by the return value of PrepareInsert
  // available to the reader.
  void FinishInsert();

  // Returns true when the buffer is empty. Thread-safe.
  bool Empty() const { return size_.load(std::memory_order_acquire) == 0; }

  // Returns true when the buffer is full. Thread-safe.
  bool Full() const {
    return size_.load(std::memory_order_acquire) == capacity_;
  }

  // Returns the capacity of the buffer.
  size_t Capacity() const { return capacity_; }

  void InitElements(absl::FunctionRef<void(T*)> init_function);

 private:
  // Increases the number of messages stored in the buffer by 1.
  void IncreaseSize() { size_.fetch_add(1, std::memory_order_seq_cst); }

  // Decreases the number of messages stored in the buffer by 1.
  void DecreaseSize() { size_.fetch_sub(1, std::memory_order_seq_cst); }

  bool insert_in_progress_ = false;
  size_t head_ = 0;

  bool front_accessed_ = false;
  size_t tail_ = 0;

  // Memory used as a ring buffer.
  std::atomic_size_t size_ = 0;  // number of messages stored in the buffer
  const size_t capacity_;        // the length of the buffer
  std::unique_ptr<T[]> buffer_;
};

// Implementation of RealtimeQueue functions.
template <typename T>
RtQueueBuffer<T>::RtQueueBuffer(size_t capacity)
    : capacity_(capacity), buffer_(std::make_unique<T[]>(capacity_)) {}

template <typename T>
RtQueueBuffer<T>::RtQueueBuffer(size_t capacity,
                                absl::FunctionRef<void(T*)> init_function)
    : capacity_(capacity), buffer_(std::make_unique<T[]>(capacity_)) {
  InitElements(init_function);
}

template <typename T>
void RtQueueBuffer<T>::InitElements(absl::FunctionRef<void(T*)> init_function) {
  for (size_t i = 0; i < Capacity(); ++i) {
    init_function(&buffer_[i]);
  }
}

// Implementation of RealtimeQueue::Reader functions.
template <typename T>
T* RtQueueBuffer<T>::Front() {
  CHECK(!front_accessed_)
      << "KeepFront or DropFront must be called before another "
         "call to Front is allowed.";
  if (Empty()) {
    return nullptr;
  }
  front_accessed_ = true;
  return &buffer_[tail_];
}

template <typename T>
void RtQueueBuffer<T>::KeepFront() {
  CHECK(front_accessed_) << "Front must be called before KeepFront.";
  front_accessed_ = false;
}

template <typename T>
void RtQueueBuffer<T>::DropFront() {
  CHECK(front_accessed_) << "Front must be called before DropFront.";
  front_accessed_ = false;
  DecreaseSize();
  tail_ = (tail_ + 1) % Capacity();
}

template <typename T>
T* RtQueueBuffer<T>::PrepareInsert() {
  CHECK(!insert_in_progress_)
      << "FinishInsert must be called before another call to "
         "PrepareInsert is allowed.";
  if (Full()) {
    return nullptr;
  }
  insert_in_progress_ = true;
  return &buffer_[head_];
}

template <typename T>
void RtQueueBuffer<T>::FinishInsert() {
  CHECK(insert_in_progress_)
      << "PrepareInsert must be called before FinishInsert.";
  insert_in_progress_ = false;
  head_ = (head_ + 1) % Capacity();
  IncreaseSize();
}

}  // namespace internal
}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_BUFFER_H_
