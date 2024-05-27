// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/common/buffers/rt_queue_multi_writer.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <optional>

#include "absl/status/status.h"
#include "intrinsic/platform/common/buffers/rt_queue.h"
#include "intrinsic/util/testing/gtest_wrapper.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic {
namespace {

using ::intrinsic::testing::StatusIs;
using ::testing::Optional;

TEST(RealtimeQueueMultiWriterTest, SingleInsert) {
  RealtimeQueue<int> queue;
  RealtimeQueueMultiWriter<int> writer(*queue.writer());

  ASSERT_OK(writer.Insert(123));
  ASSERT_THAT(queue.reader()->Pop(), Optional(123));
}

TEST(RealtimeQueueMultiWriterTest, ReportsFullQueue) {
  RealtimeQueue<int> queue(/*capacity=*/1);
  RealtimeQueueMultiWriter<int> writer(*queue.writer());

  // Fill up the one available slot in the queue.
  ASSERT_OK(writer.Insert(123));
  EXPECT_TRUE(queue.Full());

  EXPECT_THAT(writer.Insert(456),
              StatusIs(absl::StatusCode::kResourceExhausted));
}

TEST(RealtimeQueueMultiWriterTest, ConcurrentInsert) {
  constexpr size_t kIterations = 1000;
  // Use a non-trivially-copyable type to make things a bit harder.
  // The queue has room for exactly as many elements as we're planning to write.
  // This reduces the complexity of the test code below because we know that
  // Insert() operations will always succeed.
  RealtimeQueue<std::unique_ptr<int>> queue(/*capacity=*/kIterations);
  RealtimeQueueMultiWriter<std::unique_ptr<int>> writer(*queue.writer());

  // This thread inserts even integers.
  intrinsic::Thread write_thread_1([&writer]() {
    for (int i = 0; i < kIterations; i += 2) {
      ASSERT_OK(writer.Insert(std::make_unique<int>(i)));
    }
  });
  // This thread inserts odd integers.
  intrinsic::Thread write_thread_2([&writer]() {
    for (int i = 1; i < kIterations; i += 2) {
      ASSERT_OK(writer.Insert(std::make_unique<int>(i)));
    }
  });

  write_thread_1.Join();
  write_thread_2.Join();

  // Now the queue should be full. Assert this because otherwise the final
  // expectation has no hope of being met.
  ASSERT_TRUE(queue.Full());

  RealtimeQueue<std::unique_ptr<int>>::Reader& reader = *queue.reader();

  size_t receive_count = 0;
  std::optional<int> old_value;
  // Mirror the range of the first send thread.
  while (!queue.Empty()) {
    std::optional<std::unique_ptr<int>> optional_value;
    std::unique_ptr<int>* front = reader.Front();
    ASSERT_NE(front, nullptr);

    // We can't assume subsequent received indices will increase
    // monotonically, but they must be different.
    EXPECT_NE(**front, old_value);
    old_value = **front;
    reader.DropFront();
    receive_count++;
  }

  // The number of received items should add up.
  EXPECT_EQ(receive_count, kIterations);
}

}  // namespace
}  // namespace intrinsic
