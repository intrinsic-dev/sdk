// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/periodic.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <algorithm>
#include <cstdint>
#include <random>
#include <vector>

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/synchronization/mutex.h"
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

  std::shuffle(starts_and_stops.begin(), starts_and_stops.end(),
               std::mt19937());
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

TEST(PeriodicOperationTest, RunsOnDemand) {
  int count = 0;
  auto counter = [&count] { ++count; };

  // Use 24hrs as a period as a standin for a period longer than any reasonable
  // test timeout.
  PeriodicOperation op(counter, absl::Hours(24));

  ASSERT_OK(op.Start());

  op.RunNow();
  op.RunNow();
  op.RunNow();

  ASSERT_OK(op.Stop());

  // Once from initial `Start` call, thrice from `RunNow`.
  EXPECT_EQ(count, 4);
}

TEST(PeriodicOperationTest, RunsOnDemandWithoutBlocking) {
  int count = 0;
  auto counter = [&count] { ++count; };

  // Use 24hrs as a period as a standin for a period longer than any reasonable
  // test timeout.
  PeriodicOperation op(counter, absl::Hours(24));

  ASSERT_OK(op.Start());

  op.RunNowNonBlocking();
  op.RunNowNonBlocking();
  op.RunNowNonBlocking();

  ASSERT_OK(op.Stop());

  // We don't know when the execution thread will be scheduled between Start and
  // Stop, so we may drop some requests to run now. However, we know that it
  // will run at least once on `Start` and at least once for the requests, and
  // not more than four times.
  EXPECT_GE(count, 2);
  EXPECT_LE(count, 4);
}

void HandlesManyDemands(int num_blocking, int num_nonblocking) {
  int count = 0;
  auto counter = [&count] { ++count; };

  // Use 24hrs as a period as a standin for a period longer than any reasonable
  // test timeout.
  PeriodicOperation op(counter, absl::Hours(24));

  std::vector<absl::AnyInvocable<void()>> run_demands;
  for (int i = 0; i < num_blocking; ++i) {
    run_demands.push_back([&op] { return op.RunNow(); });
  }
  for (int i = 0; i < num_nonblocking; ++i) {
    run_demands.push_back([&op] { return op.RunNowNonBlocking(); });
  }

  std::shuffle(run_demands.begin(), run_demands.end(), std::mt19937());

  ASSERT_OK(op.Start());
  for (auto &&f : run_demands) {
    f();
  }
  ASSERT_OK(op.Stop());

  // We expect to have run the op once for `Start` and at least as many times as
  // we have blocking requests.
  EXPECT_GE(count, 1 + num_blocking);
}
TEST(PeriodicOperationTest, TestHandlesManyDemands) {
  HandlesManyDemands(50, 100);
}

TEST(PeriodicOperationTest, DoesntStarveOpOnDemand) {
  absl::Mutex count_mutex;
  int count = 0;
  auto counter = [&count, &count_mutex] {
    absl::MutexLock l(&count_mutex);
    ++count;
  };

  // Use 24hrs as a period as a standin for a period longer than any reasonable
  // test timeout.
  PeriodicOperation op(counter, absl::Hours(24));

  ASSERT_OK(op.Start());
  op.RunNowNonBlocking();

  absl::Condition saw_count(+[](int *c) { return *c >= 2; }, &count);
  {
    absl::MutexLock l(&count_mutex);
    count_mutex.Await(saw_count);
  }
  ASSERT_OK(op.Stop());
  EXPECT_EQ(count, 2);
}

}  // namespace
}  // namespace intrinsic
