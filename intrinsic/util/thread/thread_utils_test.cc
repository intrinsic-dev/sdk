// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread_utils.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <functional>
#include <memory>
#include <utility>

#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/util/testing/gtest_wrapper.h"
#include "intrinsic/util/thread/stop_token.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic {
namespace {

// This timeout should never be hit. The notification will terminate as soon as
// possible and specifies an upper bound on the time it takes to receive the
// notification.
constexpr absl::Duration kTimeout = absl::Milliseconds(500);

TEST(ThreadUtilsTest, CreateThreadWithStopToken) {
  absl::Notification done;
  ASSERT_OK_AND_ASSIGN(Thread thread,
                       CreateThread(
                           ThreadOptions(),
                           [](StopToken stop_token, absl::Notification& done) {
                             while (!stop_token.stop_requested()) {
                               absl::SleepFor(absl::Milliseconds(10));
                             }
                             done.Notify();
                           },
                           std::ref(done)));
  EXPECT_TRUE(thread.request_stop());
  EXPECT_TRUE(done.WaitForNotificationWithTimeout(kTimeout));
}

TEST(ThreadUtilsTest, CreateThread) {
  absl::Notification done;
  ASSERT_OK_AND_ASSIGN(
      Thread thread,
      CreateThread(
          ThreadOptions(), [](absl::Notification& done) { done.Notify(); },
          std::ref(done)));
  EXPECT_TRUE(done.WaitForNotificationWithTimeout(kTimeout));
}

TEST(ThreadUtilsTest, CreateThreadWithMoveOnlyArgument) {
  absl::Notification done;
  auto ptr = std::make_unique<int>(1);
  int* expected_ptr = ptr.get();
  int* observed_ptr = nullptr;
  ASSERT_OK_AND_ASSIGN(
      Thread thread,
      CreateThread(
          ThreadOptions(),
          [&observed_ptr](std::unique_ptr<int> ptr, absl::Notification& done) {
            observed_ptr = ptr.get();
            done.Notify();
          },
          std::move(ptr), std::ref(done)));
  EXPECT_TRUE(done.WaitForNotificationWithTimeout(kTimeout));
  EXPECT_EQ(expected_ptr, observed_ptr);
}

TEST(ThreadUtilsTest, CreateThreadWithMoveOnlyArgumentAndStopToken) {
  absl::Notification done;
  auto ptr = std::make_unique<int>(1);
  int* expected_ptr = ptr.get();
  int* observed_ptr = nullptr;
  ASSERT_OK_AND_ASSIGN(
      Thread thread,
      CreateThread(
          ThreadOptions(),
          [&observed_ptr](StopToken stop_token, std::unique_ptr<int> ptr,
                          absl::Notification& done) {
            while (!stop_token.stop_requested()) {
              absl::SleepFor(absl::Milliseconds(10));
            }
            observed_ptr = ptr.get();
            done.Notify();
          },
          std::move(ptr), std::ref(done)));
  EXPECT_TRUE(thread.request_stop());
  EXPECT_TRUE(done.WaitForNotificationWithTimeout(kTimeout));
  EXPECT_EQ(expected_ptr, observed_ptr);
}

}  // namespace
}  // namespace intrinsic
