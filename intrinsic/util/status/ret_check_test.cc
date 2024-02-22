// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/ret_check.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <string>

#include "absl/base/log_severity.h"
#include "absl/log/scoped_mock_log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace not_intrinsic {

// Define a different namespace `absl` and  `absl::Status` just to make life
// harder and ensure that macros expand correctly.
namespace absl {
struct Status;  // NOLINT
}  // namespace absl

namespace {

using ::absl::LogSeverity;
using ::absl::ScopedMockLog;
using ::testing::_;
using ::testing::AllOf;
using ::testing::HasSubstr;
using ::testing::Not;

// Matcher to verify that an error message has all the parts we guarantee.
testing::Matcher<const std::string&> HasRCheckMessage(const char* func) {
  return AllOf(HasSubstr("INTR_RET_CHECK"), HasSubstr("TRIGGERED"),
               Not(HasSubstr("IGNORED")), HasSubstr(func));
}

TEST(StatusMacrosChecksTest, RCheckFailure) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_FAIL() << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage(""));
}

TEST(StatusMacrosChecksTest, Bool) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK(true) << "IGNORED";
    INTR_RET_CHECK(false) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("false"));
}

TEST(StatusMacrosChecksTest, Eq) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_EQ(2, 2) << "IGNORED";
    INTR_RET_CHECK_EQ(3, 4) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("3 == 4"));
}

TEST(StatusMacrosChecksTest, Ne) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_NE(3, 4) << "IGNORED";
    INTR_RET_CHECK_NE(2, 2) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("2 != 2"));
}

TEST(StatusMacrosChecksTest, Le) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_LE(2, 2) << "IGNORED";
    INTR_RET_CHECK_LE(4, 3) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("4 <= 3"));
}

TEST(StatusMacrosChecksTest, Lt) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_LT(2, 3) << "IGNORED";
    INTR_RET_CHECK_LT(4, 4) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("4 < 4"));
}

TEST(StatusMacrosChecksTest, Ge) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_GE(2, 2) << "IGNORED";
    INTR_RET_CHECK_GE(3, 4) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("3 >= 4"));
}

TEST(StatusMacrosChecksTest, Gt) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_GT(3, 2) << "IGNORED";
    INTR_RET_CHECK_GT(4, 4) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("4 > 4"));
}

TEST(StatusMacrosChecksTest, Ok) {
  auto func = []() -> ::absl::Status {
    INTR_RET_CHECK_OK(::absl::OkStatus()) << "IGNORED";
    INTR_RET_CHECK_OK(::absl::Status(::absl::StatusCode::kUnknown, "zomg"))
        << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("zomg"));
}

TEST(StatusMacrosChecksTest, StatusOrOk) {
  auto func = []() -> ::absl::Status {
    int val = 45;
    ::absl::StatusOr<int*> ok = &val;
    ::absl::StatusOr<int*> ok_null = nullptr;
    ::absl::StatusOr<int*> not_ok =
        ::absl::Status(::absl::StatusCode::kUnknown, "zomg");
    INTR_RET_CHECK_OK(ok) << "IGNORED";
    INTR_RET_CHECK_OK(ok_null) << "IGNORED";
    INTR_RET_CHECK_OK(not_ok) << "TRIGGERED";
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func().message()), HasRCheckMessage("zomg"));
}

TEST(StatusMacrosChecksTest, LocalVars) {
  auto func = [](bool condition, const char* msg) -> ::absl::Status {
    INTR_RET_CHECK(condition) << msg;
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_EQ(func(true, "IGNORED"), ::absl::OkStatus());
  EXPECT_THAT(std::string(func(false, "TRIGGERED").message()),
              HasRCheckMessage("condition"));
}

TEST(StatusMacrosChecksTest, NullStr) {
  auto func = [](const char* var, const char* msg) -> ::absl::Status {
    INTR_RET_CHECK_NE(var, nullptr) << msg;
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_EQ(func("", "IGNORED"), ::absl::OkStatus());
  EXPECT_THAT(std::string(func(nullptr, "TRIGGERED").message()),
              HasRCheckMessage("var != nullptr"));
}

TEST(StatusMacrosChecksTest, MutableNullStr) {
  auto func = [](char* var, const char* msg) -> ::absl::Status {
    INTR_RET_CHECK_NE(var, nullptr) << msg;
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_THAT(std::string(func(nullptr, "TRIGGERED").message()),
              HasRCheckMessage("var != nullptr"));
}

TEST(StatusMacrosChecksTest, LocalVarsOp) {
  auto func = [](int x, int y, const char* msg) -> ::absl::Status {
    INTR_RET_CHECK_EQ(x, y) << msg;
    return ::absl::OkStatus();
  };

  ScopedMockLog log;
  log.StartCapturingLogs();
  EXPECT_CALL(log, Log(LogSeverity::kError, _, HasRCheckMessage(__func__)))
      .Times(1);
  EXPECT_EQ(func(1, 1, "IGNORED"), ::absl::OkStatus());
  EXPECT_THAT(std::string(func(2, 3, "TRIGGERED").message()),
              HasRCheckMessage("x == y"));
}

}  // namespace
}  // namespace not_intrinsic
