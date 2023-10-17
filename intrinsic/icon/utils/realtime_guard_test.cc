// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/realtime_guard.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/types/span.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/log_sink.h"

namespace intrinsic::icon {
namespace {

using ::testing::Contains;
using ::testing::ElementsAre;
using ::testing::HasSubstr;
using ::testing::IsEmpty;

TEST(RealTimeGuardTest, DeathTest) {
  EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
  {
    RealTimeGuard guard;
    EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
    // Test nested RealTimeGuard.
    {
      RealTimeGuard guard;
      EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
    }
    // Test nested RealTimeGuard with LOGE reaction
    {
      RealTimeGuard guard(RealTimeGuard::Reaction::LOGE);
      INTRINSIC_RT_LOG(INFO) << "Ignore the following error, this is normal:";
      EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
    }
    // Test nested RealTimeGuard with IGNORE reaction
    {
      RealTimeGuard guard(RealTimeGuard::Reaction::IGNORE);
      EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
    }
    EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
  }
  EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
}

namespace {
void foo() {
  INTRINSIC_RT_LOG(INFO) << "Hi from foo().";
  // Note: foo/bar/baz are not symbolized in the backtrace, as they are not in
  // a shared library.
  RealTimeGuard::LogErrorBacktrace();
}

void bar() {
  INTRINSIC_RT_LOG(INFO) << "Hi from bar().";
  foo();
}

void baz() {
  INTRINSIC_RT_LOG(INFO) << "Hi from baz().";
  bar();
}
}  // namespace

TEST(RealTimeGuardTest, LogErrorBacktrace) {
  // Construct a RealTimeGuard. This also initializes backtrace, so
  // subsequent calls below don't malloc.
  RealTimeGuard real_time_guard;

  baz();
}

class FakeLogger : public ::intrinsic::icon::LogSinkInterface {
 public:
  void Log(const LogEntry& entry) override {
    messages_.emplace_back(entry.msg);
  }
  std::vector<std::string> messages_;
};

TEST(RealTimeGuardTest, BacktraceContainsFunctionNames) {
  auto unique_logger = std::make_unique<FakeLogger>();
  auto* logger = unique_logger.get();
  icon::GlobalLogContext::SetThreadLocalLogSink(std::move(unique_logger));
  EXPECT_THAT(logger->messages_, IsEmpty());
  baz();
  ASSERT_GT(logger->messages_.size(), 4);
  EXPECT_THAT(absl::MakeSpan(logger->messages_).subspan(0, 4),
              ElementsAre("Hi from baz().", "Hi from bar().", "Hi from foo().",
                          "Backtrace:"));
}

}  // namespace
}  // namespace intrinsic::icon
