// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/periodic.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <algorithm>
#include <cstdint>
#include <random>

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace {

using ::testing::AllOf;
using ::testing::Ge;
using ::testing::Le;

TEST(PeriodicOperationTest, StartStop) {
  PeriodicOperation op(+[] {});
  EXPECT_OK(op.Start());
  EXPECT_OK(op.Stop());
}

TEST(PeriodicOperationTest, StartStopTwice) {
  PeriodicOperation op(+[] {});
  EXPECT_OK(op.Start());
  EXPECT_OK(op.Stop());
  EXPECT_OK(op.Start());
  EXPECT_OK(op.Stop());
}

TEST(PeriodicOperationTest, TwoStartsAndAStop) {
  PeriodicOperation op(+[] {});
  EXPECT_OK(op.Start());
  EXPECT_OK(op.Start());
  EXPECT_OK(op.Stop());
}

void StartsAndStops(int num_starts, int num_stops) {
  PeriodicOperation op(+[] {});

  std::vector<absl::AnyInvocable<absl::Status()>> starts_and_stops;
  for (int i = 0; i < num_starts; ++i) {
    starts_and_stops.push_back([&op] { return op.Start(); });
  }
  for (int i = 0; i < num_stops; ++i) {
    starts_and_stops.push_back([&op] { return op.Stop(); });
  }

  std::random_device rd;
  std::mt19937 g(rd());

  std::shuffle(starts_and_stops.begin(), starts_and_stops.end(), g);
  for (auto &&f : starts_and_stops) {
    EXPECT_OK(f());
  }

  // If we ever started, then we must stop to make sure.
  EXPECT_OK(op.Stop());
}
TEST(PeriodicOperationTest, TestStartsAndStops) { StartsAndStops(5, 5); }

void RunsOnAPeriod(absl::Duration period, absl::Duration test_time) {
  int count = 0;
  auto counter = [&count] { ++count; };

  PeriodicOperation op(counter, period);

  absl::Time op_start = absl::Now();
  ASSERT_OK(op.Start());
  absl::SleepFor(test_time);
  ASSERT_OK(op.Stop());
  absl::Time op_end = absl::Now();

  int64_t period_ns = absl::ToInt64Nanoseconds(period);
  int64_t test_time_ns = absl::ToInt64Nanoseconds(op_end - op_start);
  // Round up
  int expected_count = (test_time_ns + period_ns - 1) / period_ns;

  // Use an 80th percentile lower bound to account for thread scheduling
  // inconsistencies (passes with runs_per_test=1000)
  EXPECT_THAT(count, AllOf(Le(expected_count), Ge(expected_count * 4 / 5)));
}
TEST(PeriodicOperationTest, TestRunsOnAPeriod) {
  RunsOnAPeriod(absl::Milliseconds(50), absl::Milliseconds(1000));
}

}  // namespace
}  // namespace intrinsic
