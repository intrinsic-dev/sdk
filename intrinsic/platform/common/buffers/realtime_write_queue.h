// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_PLATFORM_COMMON_BUFFERS_REALTIME_WRITE_QUEUE_H_
#define INTRINSIC_PLATFORM_COMMON_BUFFERS_REALTIME_WRITE_QUEUE_H_

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>

#include "absl/base/attributes.h"
#include "absl/log/log.h"
#include "absl/time/time.h"
#include "absl/types/optional.h"
#include "intrinsic/platform/common/buffers/internal/event_fd.h"
#include "intrinsic/platform/common/buffers/rt_queue_buffer.h"

namespace intrinsic {

// Possible results of a read.
enum class ReadResult {
  // An item was consumed.
  kConsumed,
  // The writer has closed the queue and all items have been consumed.
  kClosed,
  // The deadline was reached.
  kDeadlineExceeded
};

// Implements a single-producer single-consumer thread-safe queue with real-time
// safe non-blocking writes and non-real-time safe blocking reads. In
// particular, concurrent writes are unsafe, as are concurrent reads. Reads may
// be concurrent to writes.
//
// Example usage:
//
// RealtimeWriteQueue<int> queue;
// Thread writer([&queue]() {
//   for (int num = 0; num < 10; num++) {
//     queue.Writer().Write(num)
//   }
//   queue.Writer().Close();
// });
// Thread reader([&queue]() {
//   int num = 0;
//   while (queue.Reader().Read(num) == ReadResult::kConsumed) {
//   }
// });
// reader.Join();
// writer.Join();
template <typename T>
class RealtimeWriteQueue {
 public:
  class NonRtReader {
   public:
    // Blocks until either
    // (a) the next item has been read into *item; returns kConsumed.
    // (b) Close() has been called on the corresponding writer and all values
    //     have been consumed; returns kClosed.
    // (c) The deadline is reached; returns kDeadlineExceeded.
    // If the deadline is in the past, this function will not block, but it will
    // return kConsumed or kClosed if possible.
    ABSL_MUST_USE_RESULT ReadResult ReadWithTimeout(T& item,
                                                    absl::Time deadline);

    ABSL_MUST_USE_RESULT ReadResult Read(T& item) {
      return ReadWithTimeout(item, absl::InfiniteFuture());
    }

    // Returns true when the buffer is empty.
    bool Empty() const { return buffer_.Empty(); }

   private:
    friend RealtimeWriteQueue;
    explicit NonRtReader(internal::RtQueueBuffer<T>& buffer,
                         internal::EventFd& count_event_fd,
                         internal::EventFd& closed_event_fd);
    void PollEvents(absl::Time deadline);

    internal::RtQueueBuffer<T>& buffer_;
    internal::EventFd& count_event_fd_;
    internal::EventFd& closed_event_fd_;

    bool closed_ = false;
    bool timedout_ = false;
    uint64_t count_available_ = 0;
  };

  class RtWriter {
   public:
    // Returns true if the write succeeded. A write can fail if the queue is
    // full. It is invalid to call Write() after calling Close().
    ABSL_MUST_USE_RESULT bool Write(const T& item);

    // Marks the queue as 'closed', further attempts to Write() to the queue
    // are invalid.
    void Close();

    // Returns true if the queue is 'closed'.
    bool Closed() const;

   private:
    friend RealtimeWriteQueue;
    explicit RtWriter(internal::RtQueueBuffer<T>& buffer,
                      internal::EventFd& count_event_fd,
                      internal::EventFd& closed_event_fd);
    internal::RtQueueBuffer<T>& buffer_;
    internal::EventFd& count_event_fd_;
    internal::EventFd& closed_event_fd_;

    bool closed_ = false;
  };

  static constexpr size_t kDefaultBufferCapacity = 100;

  RealtimeWriteQueue();
  explicit RealtimeWriteQueue(size_t capacity);

  NonRtReader& Reader() { return reader_; }
  RtWriter& Writer() { return writer_; }

 private:
  void InitEventFds();

  internal::RtQueueBuffer<T> buffer_;
  // A non-blocking eventfd to signal when and how many items are in the queue.
  internal::EventFd count_event_fd_;
  // A non-blocking eventfd to signal when the queue is closed.
  internal::EventFd closed_event_fd_;

  NonRtReader reader_;
  RtWriter writer_;
};

template <typename T>
ReadResult RealtimeWriteQueue<T>::NonRtReader::ReadWithTimeout(
    T& item, absl::Time deadline) {
  // Block until items are ready.
  if (count_available_ == 0 && closed_) {
    return ReadResult::kClosed;
  }

  if (count_available_ == 0) {
    PollEvents(deadline);
  }

  if (timedout_) {
    return ReadResult::kDeadlineExceeded;
  }

  if (count_available_ == 0) {
    return ReadResult::kClosed;  // must have closed.
  }

  T* element = buffer_.Front();
  // This is guaranteed to never happen, since we check that
  // `count_available_` is not zero before calling `buffer_.Front()`, and during
  // Writer::Write() the count is incremented after inserting to the queue.
  CHECK(element != nullptr) << "Attempted to read when no count_available_";
  item = *element;
  buffer_.DropFront();

  count_available_--;
  return ReadResult::kConsumed;
}

template <typename T>
RealtimeWriteQueue<T>::NonRtReader::NonRtReader(
    internal::RtQueueBuffer<T>& buffer, internal::EventFd& count_event_fd,
    internal::EventFd& closed_event_fd)
    : buffer_(buffer),
      count_event_fd_(count_event_fd),
      closed_event_fd_(closed_event_fd) {}

namespace internal {

struct Events {
  std::optional<uint64_t> count = std::nullopt;
  bool closed = false;
  bool timedout = false;
};

Events PollEvents(const internal::EventFd& count_event_fd,
                  const internal::EventFd& closed_event_fd,
                  absl::Time deadline);

}  // namespace internal

template <typename T>
void RealtimeWriteQueue<T>::NonRtReader::PollEvents(absl::Time deadline) {
  internal::Events events =
      internal::PollEvents(count_event_fd_, closed_event_fd_, deadline);
  closed_ = events.closed;
  timedout_ = events.timedout;
  if (events.count) {
    count_available_ = *events.count;
  }
}

template <typename T>
bool RealtimeWriteQueue<T>::RtWriter::Write(const T& item) {
  CHECK(!closed_) << "Invalid to Write() after Close()ing the queue";
  T* element = buffer_.PrepareInsert();
  if (element == nullptr) {
    return false;
  }
  *element = item;
  buffer_.FinishInsert();
  count_event_fd_.Signal();
  return true;
}

template <typename T>
void RealtimeWriteQueue<T>::RtWriter::Close() {
  closed_ = true;
  closed_event_fd_.Signal();
}

template <typename T>
bool RealtimeWriteQueue<T>::RtWriter::Closed() const {
  return closed_;
}

template <typename T>
RealtimeWriteQueue<T>::RtWriter::RtWriter(internal::RtQueueBuffer<T>& buffer,
                                          internal::EventFd& count_event_fd,
                                          internal::EventFd& closed_event_fd)
    : buffer_(buffer),
      count_event_fd_(count_event_fd),
      closed_event_fd_(closed_event_fd) {}

template <typename T>
RealtimeWriteQueue<T>::RealtimeWriteQueue()
    : buffer_(kDefaultBufferCapacity),
      reader_(buffer_, count_event_fd_, closed_event_fd_),
      writer_(buffer_, count_event_fd_, closed_event_fd_) {
  InitEventFds();
}

template <typename T>
RealtimeWriteQueue<T>::RealtimeWriteQueue(size_t capacity)
    : buffer_(capacity),
      reader_(buffer_, count_event_fd_, closed_event_fd_),
      writer_(buffer_, count_event_fd_, closed_event_fd_) {
  InitEventFds();
}

template <typename T>
void RealtimeWriteQueue<T>::InitEventFds() {
  bool count_inited = count_event_fd_.Init();
  // NB: This can only fail due to limits on file descriptors allowed by the
  // OS being exceeded or insufficient memory or inability to mount, which
  // are all indicitive of an unrecoverable state for the process.
  CHECK(count_inited) << "Failed to init count_event_fd_ with error: "
                      << std::strerror(errno);

  bool closed_inited = closed_event_fd_.Init();
  CHECK(closed_inited) << "Failed to init closed_event_fd_ with error: "
                       << std::strerror(errno);
}

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_COMMON_BUFFERS_REALTIME_WRITE_QUEUE_H_
