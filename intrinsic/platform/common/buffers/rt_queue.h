// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_H_
#define INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_H_

#include <cstddef>
#include <functional>
#include <memory>
#include <optional>

#include "absl/base/attributes.h"
#include "absl/memory/memory.h"
#include "absl/types/optional.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/platform/common/buffers/rt_queue_buffer.h"

namespace intrinsic {

// Empty base class for the RealtimeQueue, for type erasure.
class RealtimeQueueBase {
 public:
  virtual ~RealtimeQueueBase() = default;
};

// Implementation of a Realtime-safe queue.
//
// This is a first-in-first-out (FIFO) lock-free queue with a fixed size that's
// thread safe for a single producer and single consumer. It can be used
// without deep copying elements, making it safe to use in a realtime thread.
//
// This queue recycles its elements without any automatic reset or clearing,
// to avoid any unintentional memory allocation or deallocation. Therefore, if
// you change an element during an insert, you will eventually see an element
// with that change again. You may optionally provide a reset function to the
// writer which will be applied to every element before it is inserted.
//
// The template type T must be copyable. If T is not *trivially* copyable, then
// Insert and Pop will not be realtime safe, however it's still possible to read
// from and write to the queue in a realtime safe way; see below for details.
//
// Basic Usage:
//
// auto queue = std::make_unique<RealtimeQueue<int>>();
// queue->InitElements([](int* v) { v = ...; });  // optional.
// RealtimeQueue<int>::Reader* reader = queue->reader();
// RealtimeQueue<int>::Writer* reader = queue->writer();
//
// // Insert returns true on success, or false if queue was full.
// bool success = writer->Insert(5);
//
// // Pop returns absl::nullopt if queue was empty.
// auto optional_value = reader->Pop();
// if (optional_value) {
//   int value = optional_value.value();
// }
//
// The above usage will copy the value, which is not realtime safe for
// non-trivial types. Realtime safe usage for non-trivial element types
// (eg RealtimeQueue<MyProtoType>):
//
// writer->SetElementResetFunction([](MyProtoType* v) { v->...; }); // optional.
// MyProtoType* item = writer->PrepareInsert();
// if (item) {  // nullptr if queue is full.
//   item->set_...;
//   writer->FinishInsert();
// }
//
// const MyProtoType* item = reader->Front();
// if (item) {  // nullptr if queue is empty.
//   DoSomething(*item);
//   reader->DropFront();  // or reader->KeepFront() to leave item in queue.
// }
//
// If PrepareInsert returns a non-null value, it must be followed by a call to
// FinishInsert before it can be called again. Likewise, if Front returns a
// non-null value, it must be followed by a call to DropFront or KeepFront
// before it can be called again. If you do not pair up the calls correctly
// (eg, calling PrepareInsert twice without calling FinishInsert, calling
// DropFront without first calling Front, etc), it will abort. If PrepareInsert
// or Front return nullptr, then you should *not* call
// FinishInsert/DropFront/KeepFront, as shown above.
//
// You may mix the access methods too- eg, a non-realtime writing thread can
// use Insert while a realtime reading thread uses Front/DropFront.
//
// The Reader and Writer classes are thread compatible, so you can have multiple
// non-realtime readers or writers by protecting their access with an external
// mutex. It is not possible to have multiple realtime readers or writers.
template <typename T>
class RealtimeQueue : public RealtimeQueueBase {
 public:
  // Reader accesses and removes elements from the queue.
  // It is thread-safe with respect to a writer, and thread-compatible for
  // multiple reading threads.
  class Reader {
   public:
    // Not copyable or moveable.
    Reader(const Reader&) = delete;
    Reader(Reader&&) = delete;

    using value_type = T;

    // Gets a pointer to the front element, or nullptr if empty. If not empty,
    // KeepFront, or DropFront, must be called before another call to Front is
    // allowed.
    ABSL_MUST_USE_RESULT T* Front() { return buffer_.Front(); }
    // Keeps the front element. This signals that leaving that element in place
    // is deliberate, and allows Front to be called again.
    void KeepFront() { buffer_.KeepFront(); }
    // Removes the front element; no-op if the queue is empty.
    void DropFront() { buffer_.DropFront(); }
    // Removes and returns a copy of the first element, or nullopt if empty.
    // Due to the copy, this is not realtime safe for non-trivially-copyable
    // objects; use Front/DropFront for realtime safety with non-trivial types.
    ABSL_MUST_USE_RESULT std::optional<T> Pop();
    // Returns true when the buffer is empty.
    bool Empty() const { return buffer_.Empty(); }

   private:
    friend RealtimeQueue;
    explicit Reader(internal::RtQueueBuffer<T>& buffer) : buffer_(buffer) {}
    internal::RtQueueBuffer<T>& buffer_;
  };

  // Writer adds elements to the queue.
  // It is thread-safe with respect to a reader, and thread-compatible for
  // multiple writing threads.
  class Writer {
   public:
    using value_type = T;

    // Not copyable or moveable.
    Writer(const Writer&) = delete;
    Writer(Writer&&) = delete;

    // Gets a pointer to the next available element, or nullptr if the queue is
    // full. The element should be set and then FinishInsert must be called.
    ABSL_MUST_USE_RESULT T* PrepareInsert() {
      T* element = buffer_.PrepareInsert();
      if (reset_function_) {
        reset_function_(element);
      }
      return element;
    }
    // Make the element referenced by the return value of PrepareInsert
    // available to the reader.
    void FinishInsert() { buffer_.FinishInsert(); }
    // Copy item into the queue and return true if there is space, or false if
    // it was not copied because the queue was full. Due to the copy, this is
    // not realtime safe for non-trivially-copyable objects; use
    // PrepareInsert/FinishInsert for realtime safety with non-trivial types.
    ABSL_MUST_USE_RESULT bool Insert(const T& item);
    // Sets a function which is called by PrepareInsert to reset the recycled
    // element before it's inserted.
    void SetElementResetFunction(std::function<void(T*)> reset_function) {
      reset_function_ = reset_function;
    }

   private:
    friend RealtimeQueue;
    explicit Writer(internal::RtQueueBuffer<T>& buffer) : buffer_(buffer) {}
    internal::RtQueueBuffer<T>& buffer_;
    std::function<void(T*)> reset_function_ = nullptr;
  };

  static constexpr size_t kDefaultBufferCapacity = 100;
  using value_type = T;

  // Not copyable or moveable (that would invalidate the reader/writer).
  RealtimeQueue(const RealtimeQueue&) = delete;
  RealtimeQueue(RealtimeQueue&&) = delete;

  explicit RealtimeQueue(std::optional<size_t> capacity = std::nullopt,
                         std::function<void(T*)> init_function = nullptr);

  // Get a pointer to the reader.
  Reader* reader() { return &reader_; }

  // Get a pointer to the writer.
  Writer* writer() { return &writer_; }

  // Initialize all the elements in the buffer. This function is not thread-safe
  // and cannot be called concurrently with read/write operations.
  void InitElements(absl::FunctionRef<void(T*)> init_function) {
    buffer_.InitElements(init_function);
  }

  // Returns true when the buffer is empty. Thread-safe.
  bool Empty() const { return buffer_.Empty(); }

  // Returns true when the buffer is full. Thread-safe.
  bool Full() const { return buffer_.Full(); }

  // Returns the capacity of the buffer.
  size_t Capacity() const { return buffer_.Capacity(); }

 private:
  internal::RtQueueBuffer<T> buffer_;

  Reader reader_;
  Writer writer_;
};

// Implementation of RealtimeQueue functions.
template <typename T>
RealtimeQueue<T>::RealtimeQueue(std::optional<size_t> capacity,
                                std::function<void(T*)> init_function)
    : buffer_(capacity.value_or(kDefaultBufferCapacity)),
      reader_(buffer_),
      writer_(buffer_) {
  if (init_function != nullptr) {
    buffer_.InitElements(init_function);
  }
}

template <typename T>
std::optional<T> RealtimeQueue<T>::Reader::Pop() {
  if (!std::is_trivially_copyable<T>::value) {
    INTRINSIC_ASSERT_NON_REALTIME();
  }
  const T* front_ptr = buffer_.Front();
  if (front_ptr) {
    T front = *front_ptr;
    buffer_.DropFront();
    return front;
  } else {
    return std::nullopt;
  }
}

template <typename T>
bool RealtimeQueue<T>::Writer::Insert(const T& item) {
  if (!std::is_trivially_copyable<T>::value) {
    INTRINSIC_ASSERT_NON_REALTIME();
  }
  T* item_ptr = PrepareInsert();
  if (item_ptr) {
    *item_ptr = item;
    FinishInsert();
    return true;
  } else {
    return false;
  }
}

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_QUEUE_H_
