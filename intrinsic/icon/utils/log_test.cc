// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/log.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/log/log.h"
#include "absl/strings/str_cat.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/icon/utils/log_internal.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {
namespace {

using ::testing::AllOf;
using ::testing::ElementsAre;
using ::testing::HasSubstr;
using ::testing::IsEmpty;
using ::testing::StartsWith;
using ::testing::StrEq;

class FakeLogger : public LogSinkInterface {
 public:
  void Log(const LogEntry& entry) override {
    messages_.emplace_back(entry.msg);
    char buffer[kLogMessageMaxSize] = {0};
    LogEntryFormatToBuffer(buffer, sizeof(buffer), entry);
    text_.emplace_back(std::string(buffer));
  }
  std::vector<std::string> text_;
  std::vector<std::string> messages_;
};

TEST(IconUtilsLogTest, LogsSeverityLineFilename) {
  auto unique_logger = std::make_unique<FakeLogger>();
  auto* logger = unique_logger.get();
  GlobalLogContext::SetThreadLocalLogSink(std::move(unique_logger));
  EXPECT_THAT(logger->messages_, IsEmpty());
  double d = 0.5;
  INTRINSIC_RT_LOG(INFO) << "dof:" << 3 << " d:" << d;
  auto location = INTRINSIC_LOC;
  std::string expected_line_number = absl::StrCat(":", location.line() - 1);
  EXPECT_THAT(logger->messages_, ElementsAre(StrEq("dof:3 d:0.5")));
  EXPECT_THAT(
      logger->text_,
      ElementsAre(AllOf(StartsWith("I"), HasSubstr(expected_line_number),
                        HasSubstr("log_test.cc"), HasSubstr("dof:3 d:0.5"))));
}

TEST(IconUtilsLogTest, Throttles) {
  auto unique_logger = std::make_unique<FakeLogger>();
  auto* logger = unique_logger.get();
  GlobalLogContext::SetThreadLocalLogSink(std::move(unique_logger));
  EXPECT_THAT(logger->messages_, IsEmpty());
  INTRINSIC_RT_LOG_THROTTLED(WARNING) << "logged1";
  auto location = INTRINSIC_LOC;
  std::string expected_line_number = absl::StrCat(":", location.line() - 1);
  EXPECT_THAT(
      logger->text_,
      ElementsAre(AllOf(StartsWith("W"), HasSubstr(expected_line_number),
                        HasSubstr("log_test.cc"), HasSubstr("logged1"))));
  INTRINSIC_RT_LOG_THROTTLED(WARNING) << "logged2";
  for (int i = 0; i < 2000; ++i) {
    INTRINSIC_RT_LOG_THROTTLED(INFO) << "rarely logged i:" << i;
  }
  EXPECT_THAT(
      logger->messages_,
      ElementsAre(StrEq("logged1"), StrEq("logged2"),
                  StartsWith("rarely logged i:0"),
                  StartsWith("rarely logged i:1000 (repeated 1000 times in ")));
}

TEST(IconUtilsLogTest, DefaultLoggerDoesNotAllocate) {
  GlobalLogContext::SetThreadLocalLogSink(nullptr);
  double d = 0.5;
  std::string s = "text";
  INTRINSIC_RT_LOG(INFO) << "dof:" << 3 << " d:" << d;
  INTRINSIC_RT_LOG(ERROR) << "error: " << s;
  INTRINSIC_RT_LOG_THROTTLED(WARNING) << "logged1";
  for (int i = 0; i < 2000; ++i) {
    INTRINSIC_RT_LOG_THROTTLED(WARNING) << "rarely logged i:" << i;
  }
}

TEST(IconUtilsLogTest, DefaultLoggerIsThreadSafe) {
  GlobalLogContext::SetThreadLocalLogSink(nullptr);
  auto worker = []() {
    for (int i = 0; i < 10; ++i) {
      std::string s = "text";
      INTRINSIC_RT_LOG(INFO) << " i:" << i;
      INTRINSIC_RT_LOG(ERROR) << "error: " << s;
      INTRINSIC_RT_LOG_THROTTLED(WARNING) << "logged1";
      for (int j = 0; j < 2000; ++j) {
        INTRINSIC_RT_LOG_THROTTLED(WARNING) << "rarely logged j:" << j;
      }
    }
  };
  intrinsic::Thread worker1_thread{worker};
  intrinsic::Thread worker2_thread{worker};
  worker1_thread.Join();
  worker2_thread.Join();
}

}  // namespace
}  // namespace intrinsic::icon
