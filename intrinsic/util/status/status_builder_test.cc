// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_builder.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <optional>
#include <sstream>
#include <string>
#include <type_traits>
#include <utility>

#include "absl/base/log_severity.h"
#include "absl/log/log_entry.h"
#include "absl/log/log_sink.h"
#include "absl/log/scoped_mock_log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/cord.h"
#include "absl/strings/match.h"
#include "absl/strings/str_cat.h"
#include "absl/time/civil_time.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "google/protobuf/wrappers.pb.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/util/proto/type_url.h"
#include "intrinsic/util/status/extended_status.pb.h"
#include "intrinsic/util/testing/gtest_wrapper.h"
#include "intrinsic/util/testing/status_payload_matchers.h"

namespace intrinsic {
namespace {

using ::absl::LogSeverity;
using ::absl::ScopedMockLog;
using ::intrinsic::testing::EqualsProto;
using ::intrinsic::testing::StatusHasGenericPayload;
using ::intrinsic::testing::StatusHasProtoPayload;
using ::intrinsic::testing::StatusIs;
using ::testing::_;
using ::testing::AllOf;
using ::testing::AnyOf;
using ::testing::Eq;
using ::testing::HasSubstr;
using ::testing::Not;
using ::testing::Pointee;

// We use `#line` to produce some `source_location` values pointing at various
// different (fake) files to test, but we use it at the end of this
// file so as not to mess up the source location data for the whole file.
// Making them static data members lets us forward-declare them and define them
// at the end.
struct Locs {
  static const intrinsic::SourceLocation kSecret;
  static const intrinsic::SourceLocation kBar;
};

class StringSink : public absl::LogSink {
 public:
  StringSink() = default;

  void Send(const absl::LogEntry& entry) override {
    absl::StrAppend(&message_, entry.source_basename(), ":",
                    entry.source_line(), " - ", entry.text_message());
  }

  const std::string& ToString() { return message_; }

 private:
  std::string message_;
};

// Converts a StatusBuilder to a Status.
absl::Status ToStatus(const StatusBuilder& s) { return s; }

// Converts a StatusBuilder to a Status and then ignores it.
void ConvertToStatusAndIgnore(const StatusBuilder& s) {
  absl::Status status = s;
  (void)status;
}

// Converts a StatusBuilder to a StatusOr<T>.
template <typename T>
absl::StatusOr<T> ToStatusOr(const StatusBuilder& s) {
  return s;
}

TEST(StatusBuilderTest, Size) {
  EXPECT_LE(sizeof(StatusBuilder), 40)
      << "Relax this test with caution and thorough testing. If StatusBuilder "
         "is too large it can potentially blow stacks, especially in debug "
         "builds. See the comments for StatusBuilder::Rep.";
}

TEST(StatusBuilderTest, Ctors) {
  EXPECT_EQ(ToStatus(StatusBuilder(absl::StatusCode::kUnimplemented) << "nope"),
            absl::Status(absl::StatusCode::kUnimplemented, "nope"));
}

TEST(StatusBuilderTest, ExplicitSourceLocation) {
  const intrinsic::SourceLocation kLocation = INTRINSIC_LOC;

  {
    const StatusBuilder builder(absl::OkStatus(), kLocation);
    EXPECT_THAT(builder.source_location().file_name(),
                Eq(kLocation.file_name()));
    EXPECT_THAT(builder.source_location().line(), Eq(kLocation.line()));
  }
}

TEST(StatusBuilderTest, ImplicitSourceLocation) {
  const StatusBuilder builder(absl::OkStatus());
  auto loc = INTRINSIC_LOC;
  EXPECT_THAT(builder.source_location().file_name(),
              AnyOf(Eq(loc.file_name()), Eq("<source_location>")));
  EXPECT_THAT(builder.source_location().line(),
              AnyOf(Eq(1), Eq(loc.line() - 1)));
}

TEST(StatusBuilderTest, StatusCode) {
  // OK
  {
    const StatusBuilder builder(absl::StatusCode::kOk);
    EXPECT_TRUE(builder.ok());
    EXPECT_THAT(builder.code(), Eq(absl::StatusCode::kOk));
  }

  // Non-OK code
  {
    const StatusBuilder builder(absl::StatusCode::kInvalidArgument);
    EXPECT_FALSE(builder.ok());
    EXPECT_THAT(builder.code(), Eq(absl::StatusCode::kInvalidArgument));
  }
}

TEST(StatusBuilderTest, Streaming) {
  EXPECT_THAT(
      ToStatus(
          StatusBuilder(absl::CancelledError(), intrinsic::SourceLocation())
          << "booyah"),
      Eq(absl::CancelledError("booyah")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::AbortedError("hello"),
                                     intrinsic::SourceLocation())
                       << "world"),
              Eq(absl::AbortedError("hello; world")));
  EXPECT_THAT(
      ToStatus(StatusBuilder(
                   absl::Status(absl::StatusCode::kUnimplemented, "enosys"),
                   intrinsic::SourceLocation())
               << "punk!"),
      Eq(absl::Status(absl::StatusCode::kUnimplemented, "enosys; punk!")));
}

TEST(StatusBuilderTest, PrependLvalue) {
  {
    StatusBuilder builder(absl::CancelledError(), intrinsic::SourceLocation());
    EXPECT_THAT(ToStatus(builder.SetPrepend() << "booyah"),
                Eq(absl::CancelledError("booyah")));
  }
  {
    StatusBuilder builder(absl::AbortedError(" hello"),
                          intrinsic::SourceLocation());
    EXPECT_THAT(ToStatus(builder.SetPrepend() << "world"),
                Eq(absl::AbortedError("world hello")));
  }
}

TEST(StatusBuilderTest, PrependRvalue) {
  EXPECT_THAT(ToStatus(StatusBuilder(absl::CancelledError(),
                                     intrinsic::SourceLocation())
                           .SetPrepend()
                       << "booyah"),
              Eq(absl::CancelledError("booyah")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::AbortedError(" hello"),
                                     intrinsic::SourceLocation())
                           .SetPrepend()
                       << "world"),
              Eq(absl::AbortedError("world hello")));
}

TEST(StatusBuilderTest, AppendLvalue) {
  {
    StatusBuilder builder(absl::CancelledError(), intrinsic::SourceLocation());
    EXPECT_THAT(ToStatus(builder.SetAppend() << "booyah"),
                Eq(absl::CancelledError("booyah")));
  }
  {
    StatusBuilder builder(absl::AbortedError("hello"),
                          intrinsic::SourceLocation());
    EXPECT_THAT(ToStatus(builder.SetAppend() << " world"),
                Eq(absl::AbortedError("hello world")));
  }
}

TEST(StatusBuilderTest, AppendRvalue) {
  EXPECT_THAT(ToStatus(StatusBuilder(absl::CancelledError(),
                                     intrinsic::SourceLocation())
                           .SetAppend()
                       << "booyah"),
              Eq(absl::CancelledError("booyah")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::AbortedError("hello"),
                                     intrinsic::SourceLocation())
                           .SetAppend()
                       << " world"),
              Eq(absl::AbortedError("hello world")));
}

TEST(StatusBuilderTest, LogToMultipleErrorLevelsLvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(1);
  EXPECT_CALL(log, Log(absl::LogSeverity::kError, _, HasSubstr("yes!")))
      .Times(1);
  log.StartCapturingLogs();
  {
    StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
    ConvertToStatusAndIgnore(builder.Log(LogSeverity::kWarning) << "no!");
  }
  {
    StatusBuilder builder(absl::AbortedError(""), Locs::kSecret);

    ConvertToStatusAndIgnore(builder.Log(LogSeverity::kError) << "yes!");
  }
}

TEST(StatusBuilderTest, LogToMultipleErrorLevelsRvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(1);
  EXPECT_CALL(log, Log(absl::LogSeverity::kError, _, HasSubstr("yes!")))
      .Times(1);
  log.StartCapturingLogs();
  ConvertToStatusAndIgnore(StatusBuilder(absl::CancelledError(), Locs::kSecret)
                               .Log(LogSeverity::kWarning)
                           << "no!");
  ConvertToStatusAndIgnore(StatusBuilder(absl::AbortedError(""), Locs::kSecret)
                               .Log(LogSeverity::kError)
                           << "yes!");
}

TEST(StatusBuilderTest, LogEveryNFirstLogs) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(1);
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  // Only 1 of the 3 should log.
  for (int i = 0; i < 3; ++i) {
    ConvertToStatusAndIgnore(builder.LogEveryN(LogSeverity::kWarning, 3)
                             << "no!");
  }
}

TEST(StatusBuilderTest, LogEveryN2Lvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(3);
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  // Only 3 of the 6 should log.
  for (int i = 0; i < 6; ++i) {
    ConvertToStatusAndIgnore(builder.LogEveryN(LogSeverity::kWarning, 2)
                             << "no!");
  }
}

TEST(StatusBuilderTest, LogEveryN3Lvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(2);
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  // Only 2 of the 6 should log.
  for (int i = 0; i < 6; ++i) {
    ConvertToStatusAndIgnore(builder.LogEveryN(LogSeverity::kWarning, 3)
                             << "no!");
  }
}

TEST(StatusBuilderTest, LogEveryN7Lvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(3);
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  // Only 3 of the 21 should log.
  for (int i = 0; i < 21; ++i) {
    ConvertToStatusAndIgnore(builder.LogEveryN(LogSeverity::kWarning, 7)
                             << "no!");
  }
}

TEST(StatusBuilderTest, LogEveryNRvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(2);
  log.StartCapturingLogs();

  // Only 2 of the 4 should log.
  for (int i = 0; i < 4; ++i) {
    ConvertToStatusAndIgnore(
        StatusBuilder(absl::CancelledError(), Locs::kSecret)
            .LogEveryN(LogSeverity::kWarning, 2)
        << "no!");
  }
}

TEST(StatusBuilderTest, LogEveryFirstLogs) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(1);
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  ConvertToStatusAndIgnore(
      builder.LogEvery(LogSeverity::kWarning, absl::Seconds(2)) << "no!");
}

TEST(StatusBuilderTest, LogEveryLvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(::testing::AtMost(3));
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  for (int i = 0; i < 4; ++i) {
    ConvertToStatusAndIgnore(
        builder.LogEvery(LogSeverity::kWarning, absl::Seconds(2)) << "no!");
    absl::SleepFor(absl::Seconds(1));
  }
}

TEST(StatusBuilderTest, LogEveryRvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(::testing::AtMost(3));
  log.StartCapturingLogs();

  for (int i = 0; i < 4; ++i) {
    ConvertToStatusAndIgnore(
        StatusBuilder(absl::CancelledError(), Locs::kSecret)
            .LogEvery(LogSeverity::kWarning, absl::Seconds(2))
        << "no!");
    absl::SleepFor(absl::Seconds(1));
  }
}

TEST(StatusBuilderTest, LogEveryZeroDuration) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("no!")))
      .Times(::testing::Exactly(4));
  log.StartCapturingLogs();

  StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
  for (int i = 0; i < 4; ++i) {
    ConvertToStatusAndIgnore(
        builder.LogEvery(LogSeverity::kWarning, absl::ZeroDuration()) << "no!");
  }
}

TEST(StatusBuilderTest, LogIncludesFileAndLine) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning,
                       AnyOf(HasSubstr("/foo/secret.cc"),
                             HasSubstr("<source_location>")),
                       HasSubstr("maybe?")))
      .Times(1);
  log.StartCapturingLogs();
  ConvertToStatusAndIgnore(StatusBuilder(absl::AbortedError(""), Locs::kSecret)
                               .Log(LogSeverity::kWarning)
                           << "maybe?");
}

TEST(StatusBuilderTest, NoLoggingLvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(_, _, _)).Times(0);
  log.StartCapturingLogs();

  {
    StatusBuilder builder(absl::AbortedError(""), Locs::kSecret);
    EXPECT_THAT(ToStatus(builder << "nope"), Eq(absl::AbortedError("nope")));
  }
  {
    StatusBuilder builder(absl::AbortedError(""), Locs::kSecret);
    // Enable and then disable logging.
    EXPECT_THAT(ToStatus(builder.Log(LogSeverity::kWarning).SetNoLogging()
                         << "not at all"),
                Eq(absl::AbortedError("not at all")));
  }
}

TEST(StatusBuilderTest, NoLoggingRvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(_, _, _)).Times(0);
  log.StartCapturingLogs();
  EXPECT_THAT(
      ToStatus(StatusBuilder(absl::AbortedError(""), Locs::kSecret) << "nope"),
      Eq(absl::AbortedError("nope")));
  // Enable and then disable logging.
  EXPECT_THAT(ToStatus(StatusBuilder(absl::AbortedError(""), Locs::kSecret)
                           .Log(LogSeverity::kWarning)
                           .SetNoLogging()
                       << "not at all"),
              Eq(absl::AbortedError("not at all")));
}

TEST(StatusBuilderTest, EmitStackTracePlusSomethingLikelyUniqueLvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log,
              Log(absl::LogSeverity::kError, HasSubstr("/bar/baz.cc"),
                  // this method shows up in the stack trace
                  HasSubstr("EmitStackTracePlusSomethingLikelyUniqueLvalue")))
      .Times(1);
  log.StartCapturingLogs();
  StatusBuilder builder(absl::AbortedError(""), Locs::kBar);
  ConvertToStatusAndIgnore(builder.LogError().EmitStackTrace() << "maybe?");
}

TEST(StatusBuilderTest, EmitStackTracePlusSomethingLikelyUniqueRvalue) {
  ScopedMockLog log;
  EXPECT_CALL(log,
              Log(absl::LogSeverity::kError, HasSubstr("/bar/baz.cc"),
                  // this method shows up in the stack trace
                  HasSubstr("EmitStackTracePlusSomethingLikelyUniqueRvalue")))
      .Times(1);
  log.StartCapturingLogs();
  ConvertToStatusAndIgnore(StatusBuilder(absl::AbortedError(""), Locs::kBar)
                               .LogError()
                               .EmitStackTrace()
                           << "maybe?");
}

TEST(StatusBuilderTest, AlsoOutputToSinkLvalue) {
  StringSink sink;
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kError, _, HasSubstr("yes!")))
      .Times(1);
  log.StartCapturingLogs();
  {
    // This should not output anything to sink because logging is not enabled.
    StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
    ConvertToStatusAndIgnore(builder.AlsoOutputToSink(&sink) << "no!");
    EXPECT_TRUE(sink.ToString().empty());
  }
  {
    StatusBuilder builder(absl::CancelledError(), Locs::kSecret);
    ConvertToStatusAndIgnore(
        builder.Log(LogSeverity::kError).AlsoOutputToSink(&sink) << "yes!");
    EXPECT_TRUE(absl::StrContains(sink.ToString(), "yes!"));
  }
}

TEST(StatusBuilderTest, AlsoOutputToSinkRvalue) {
  StringSink sink;
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kError, _, HasSubstr("yes!")))
      .Times(1);
  log.StartCapturingLogs();
  // This should not output anything to sink because logging is not enabled.
  ConvertToStatusAndIgnore(StatusBuilder(absl::CancelledError(), Locs::kSecret)
                               .AlsoOutputToSink(&sink)
                           << "no!");
  EXPECT_TRUE(sink.ToString().empty());
  ConvertToStatusAndIgnore(StatusBuilder(absl::CancelledError(), Locs::kSecret)
                               .Log(LogSeverity::kError)
                               .AlsoOutputToSink(&sink)
                           << "yes!");
  EXPECT_TRUE(absl::StrContains(sink.ToString(), "yes!"));
}

TEST(StatusBuilderTest, WithRvalueRef) {
  auto policy = [](StatusBuilder sb) { return sb << "policy"; };
  EXPECT_THAT(ToStatus(StatusBuilder(absl::AbortedError("hello"),
                                     intrinsic::SourceLocation())
                           .With(policy)),
              Eq(absl::AbortedError("hello; policy")));
}

TEST(StatusBuilderTest, WithRef) {
  auto policy = [](StatusBuilder sb) { return sb << "policy"; };
  StatusBuilder sb(absl::AbortedError("zomg"), intrinsic::SourceLocation());
  EXPECT_THAT(ToStatus(sb.With(policy)),
              Eq(absl::AbortedError("zomg; policy")));
}

TEST(StatusBuilderTest, WithTypeChange) {
  auto policy = [](StatusBuilder sb) -> std::string {
    return sb.ok() ? "true" : "false";
  };
  EXPECT_EQ(StatusBuilder(absl::CancelledError(), intrinsic::SourceLocation())
                .With(policy),
            "false");
  EXPECT_EQ(
      StatusBuilder(absl::OkStatus(), intrinsic::SourceLocation()).With(policy),
      "true");
}

TEST(StatusBuilderTest, WithVoidTypeAndSideEffects) {
  absl::StatusCode code = absl::StatusCode::kUnknown;
  auto policy = [&code](absl::Status status) { code = status.code(); };
  StatusBuilder(absl::CancelledError(), intrinsic::SourceLocation())
      .With(policy);
  EXPECT_EQ(absl::StatusCode::kCancelled, code);
  StatusBuilder(absl::OkStatus(), intrinsic::SourceLocation()).With(policy);
  EXPECT_EQ(absl::StatusCode::kOk, code);
}

struct MoveOnlyAdaptor {
  std::unique_ptr<int> value;
  std::unique_ptr<int> operator()(const absl::Status&) && {
    return std::move(value);
  }
};

TEST(StatusBuilderTest, WithMoveOnlyAdaptor) {
  StatusBuilder sb(absl::AbortedError("zomg"), intrinsic::SourceLocation());
  EXPECT_THAT(sb.With(MoveOnlyAdaptor{std::make_unique<int>(100)}),
              Pointee(100));
  EXPECT_THAT(
      StatusBuilder(absl::AbortedError("zomg"), intrinsic::SourceLocation())
          .With(MoveOnlyAdaptor{std::make_unique<int>(100)}),
      Pointee(100));
}

template <typename T>
std::string ToStringViaStream(const T& x) {
  std::ostringstream os;
  os << x;
  return os.str();
}

TEST(StatusBuilderTest, StreamInsertionOperator) {
  absl::Status status = absl::AbortedError("zomg");
  StatusBuilder builder(status, intrinsic::SourceLocation());
  EXPECT_EQ(ToStringViaStream(status), ToStringViaStream(builder));
  EXPECT_EQ(
      ToStringViaStream(status),
      ToStringViaStream(StatusBuilder(status, intrinsic::SourceLocation())));
}

TEST(StatusBuilderTest, SetCode) {
  StatusBuilder builder(absl::StatusCode::kUnknown,
                        intrinsic::SourceLocation());
  builder.SetCode(absl::StatusCode::kResourceExhausted);
  absl::Status status = builder;
  EXPECT_EQ(status, absl::ResourceExhaustedError(""));
}

TEST(CanonicalErrorsTest, CreateAndClassify) {
  struct CanonicalErrorTest {
    absl::StatusCode code;
    StatusBuilder builder;
  };
  intrinsic::SourceLocation loc = intrinsic::SourceLocation::current();
  CanonicalErrorTest canonical_errors[] = {
      // implicit location
      {absl::StatusCode::kAborted, AbortedErrorBuilder()},
      {absl::StatusCode::kAlreadyExists, AlreadyExistsErrorBuilder()},
      {absl::StatusCode::kCancelled, CancelledErrorBuilder()},
      {absl::StatusCode::kDataLoss, DataLossErrorBuilder()},
      {absl::StatusCode::kDeadlineExceeded, DeadlineExceededErrorBuilder()},
      {absl::StatusCode::kFailedPrecondition, FailedPreconditionErrorBuilder()},
      {absl::StatusCode::kInternal, InternalErrorBuilder()},
      {absl::StatusCode::kInvalidArgument, InvalidArgumentErrorBuilder()},
      {absl::StatusCode::kNotFound, NotFoundErrorBuilder()},
      {absl::StatusCode::kOutOfRange, OutOfRangeErrorBuilder()},
      {absl::StatusCode::kPermissionDenied, PermissionDeniedErrorBuilder()},
      {absl::StatusCode::kUnauthenticated, UnauthenticatedErrorBuilder()},
      {absl::StatusCode::kResourceExhausted, ResourceExhaustedErrorBuilder()},
      {absl::StatusCode::kUnavailable, UnavailableErrorBuilder()},
      {absl::StatusCode::kUnimplemented, UnimplementedErrorBuilder()},
      {absl::StatusCode::kUnknown, UnknownErrorBuilder()},

      // explicit location
      {absl::StatusCode::kAborted, AbortedErrorBuilder(loc)},
      {absl::StatusCode::kAlreadyExists, AlreadyExistsErrorBuilder(loc)},
      {absl::StatusCode::kCancelled, CancelledErrorBuilder(loc)},
      {absl::StatusCode::kDataLoss, DataLossErrorBuilder(loc)},
      {absl::StatusCode::kDeadlineExceeded, DeadlineExceededErrorBuilder(loc)},
      {absl::StatusCode::kFailedPrecondition,
       FailedPreconditionErrorBuilder(loc)},
      {absl::StatusCode::kInternal, InternalErrorBuilder(loc)},
      {absl::StatusCode::kInvalidArgument, InvalidArgumentErrorBuilder(loc)},
      {absl::StatusCode::kNotFound, NotFoundErrorBuilder(loc)},
      {absl::StatusCode::kOutOfRange, OutOfRangeErrorBuilder(loc)},
      {absl::StatusCode::kPermissionDenied, PermissionDeniedErrorBuilder(loc)},
      {absl::StatusCode::kUnauthenticated, UnauthenticatedErrorBuilder(loc)},
      {absl::StatusCode::kResourceExhausted,
       ResourceExhaustedErrorBuilder(loc)},
      {absl::StatusCode::kUnavailable, UnavailableErrorBuilder(loc)},
      {absl::StatusCode::kUnimplemented, UnimplementedErrorBuilder(loc)},
      {absl::StatusCode::kUnknown, UnknownErrorBuilder(loc)},
  };

  for (const auto& test : canonical_errors) {
    SCOPED_TRACE(absl::StrCat("absl::StatusCode::",
                              absl::StatusCodeToString(test.code)));

    // Ensure that the creator does, in fact, create status objects in the
    // canonical space, with the expected error code and message.
    std::string message =
        absl::StrCat("error code ", test.code, " test message");
    absl::Status status = StatusBuilder(test.builder) << message;
    EXPECT_EQ(test.code, status.code());
    EXPECT_EQ(message, status.message());
  }
}

TEST(StatusBuilderTest, ExtraMessageRValue) {
  static_assert(
      std::is_same_v<ExtraMessage&&, decltype(ExtraMessage() << "hello")>);
}

TEST(StatusBuilderTest, ExtraMessageAppends) {
  EXPECT_THAT(
      ToStatus(
          StatusBuilder(absl::UnknownError("Foo")).With(ExtraMessage("Bar"))),
      Eq(absl::UnknownError("Foo; Bar")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::UnknownError("Foo"))
                           .With(ExtraMessage() << "Bar")),
              Eq(absl::UnknownError("Foo; Bar")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::UnknownError("Foo"))
                           .With(ExtraMessage() << "Bar")
                           .With(ExtraMessage() << "tender")),
              Eq(absl::UnknownError("Foo; Bartender")));
  EXPECT_THAT(ToStatus(StatusBuilder(absl::UnknownError("Foo"))
                           .With(ExtraMessage() << "Bar")
                           .SetPrepend()),
              Eq(absl::UnknownError("BarFoo")));
}

TEST(StatusBuilderTest, ExtraMessageAppendsMove) {
  auto extra_message = ExtraMessage("Bar");
  EXPECT_THAT(ToStatus(StatusBuilder(absl::UnknownError("Foo"))
                           .With(std::move(extra_message))),
              Eq(absl::UnknownError("Foo; Bar")));
}

TEST(StatusBuilderTest, LogsExtraMessage) {
  ScopedMockLog log;
  EXPECT_CALL(log, Log(absl::LogSeverity::kError, _, HasSubstr("Foo; Bar")))
      .Times(1);
  EXPECT_CALL(log, Log(absl::LogSeverity::kWarning, _, HasSubstr("Foo; Bar")))
      .Times(1);
  log.StartCapturingLogs();

  ConvertToStatusAndIgnore(StatusBuilder(absl::UnknownError("Foo"))
                               .With(ExtraMessage("Bar"))
                               .LogError());
  ConvertToStatusAndIgnore(StatusBuilder(absl::UnknownError("Foo"))
                               .With(ExtraMessage() << "Bar")
                               .LogWarning());
}

TEST(StatusBuilderTest, SetPayloadAdds) {
  google::protobuf::Int64Value value_proto;
  value_proto.set_value(-123);
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetPayload(AddTypeUrlPrefix(value_proto.GetDescriptor()->full_name()),
                     value_proto.SerializeAsCord());
  absl::Status result = builder;
  EXPECT_THAT(result, AllOf(StatusIs(absl::StatusCode::kInvalidArgument),
                            StatusHasProtoPayload<google::protobuf::Int64Value>(
                                EqualsProto(value_proto))));
}

TEST(StatusBuilderTest, SetPayloadIgnoredOnOkStatus) {
  StatusBuilder builder(absl::StatusCode::kOk);
  ASSERT_TRUE(builder.ok());

  google::protobuf::Int64Value value_proto;
  value_proto.set_value(-123);
  builder.SetPayload(AddTypeUrlPrefix(value_proto.GetDescriptor()->full_name()),
                     value_proto.SerializeAsCord());
  absl::Status result = builder;
  EXPECT_THAT(result, Not(StatusHasGenericPayload(
                          AddTypeUrlPrefix<google::protobuf::Int64Value>())));
}

TEST(StatusBuilderTest, SetPayloadMultiplePayloads) {
  google::protobuf::Int64Value int_proto;
  int_proto.set_value(-123);

  google::protobuf::StringValue string_proto;
  string_proto.set_value("foo");

  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetPayload(AddTypeUrlPrefix(int_proto), int_proto.SerializeAsCord())
      .SetPayload(AddTypeUrlPrefix(string_proto.GetDescriptor()->full_name()),
                  string_proto.SerializeAsCord());

  absl::Status result = builder;
  EXPECT_THAT(result,
              AllOf(StatusHasProtoPayload<google::protobuf::Int64Value>(
                        EqualsProto(int_proto)),
                    StatusHasProtoPayload<google::protobuf::StringValue>(
                        EqualsProto(string_proto))));
}

TEST(StatusBuilderTest, SetExtendedStatus) {
  intrinsic_proto::status::ExtendedStatus extended_status;
  extended_status.mutable_status_code()->set_component("Comp");
  extended_status.mutable_status_code()->set_code(123);
  extended_status.set_title("Title");
  extended_status.mutable_external_report()->set_message("Ext Message");
  extended_status.mutable_internal_report()->set_message("Int Message");
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatus(extended_status);
  absl::Status result = builder;

  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(extended_status)));
}

TEST(StatusBuilderTest, SetExtendedStatusCode) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusCode("component", 2345);
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "component" code: 2345 }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusCodeFromProto) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  intrinsic_proto::status::StatusCode status_code;
  status_code.set_component("component");
  status_code.set_code(3456);
  builder.SetExtendedStatusCode(status_code);
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "component" code: 3456 }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusTitle) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusTitle("My title");
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    title: "My title"
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusTimestamp) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  builder.SetExtendedStatusTimestamp(t);
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    timestamp { seconds: 1711453873 }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusInternalReportMessage) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusInternalReportMessage("internal message");
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    internal_report { message: "internal message" }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusExternalReportMessage) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusExternalReportMessage("external message");
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    external_report { message: "external message" }
                  )pb")));
}

TEST(StatusBuilderTest, EmitStackTraceToExtendedStatusInternalReport) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.EmitStackTraceToExtendedStatusInternalReport();
  absl::Status result = builder;
  std::optional<absl::Cord> result_payload = result.GetPayload(AddTypeUrlPrefix(
      intrinsic_proto::status::ExtendedStatus::descriptor()->full_name()));
  ASSERT_TRUE(result_payload.has_value());
  intrinsic_proto::status::ExtendedStatus result_proto;
  ASSERT_TRUE(result_proto.ParseFromCord(*result_payload));
  EXPECT_THAT(result_proto.internal_report().message(),
              HasSubstr("EmitStackTraceToExtendedStatusInternalReport"));
}

TEST(StatusBuilderTest, ChainExtendedStatusCalls) {
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusCode("component", 2345)
      .SetExtendedStatusTitle("My title")
      .SetExtendedStatusExternalReportMessage("Foo");
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "component" code: 2345 }
                    title: "My title"
                    external_report { message: "Foo" }
                  )pb")));
}

TEST(StatusBuilderTest, AddExtendedStatusContext) {
  intrinsic_proto::status::ExtendedStatus context_status;
  context_status.mutable_status_code()->set_component("Context");
  context_status.mutable_status_code()->set_code(123);
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusCode("component", 2345)
      .AddExtendedStatusContext(context_status);
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "component" code: 2345 }
                    context { status_code { component: "Context" code: 123 } }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusLogContext) {
  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);
  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatusLogContext(log_context);
  absl::Status result = builder;
  std::optional<absl::Cord> result_payload = result.GetPayload(AddTypeUrlPrefix(
      intrinsic_proto::status::ExtendedStatus::descriptor()->full_name()));
  ASSERT_TRUE(result_payload.has_value());
  intrinsic_proto::status::ExtendedStatus result_proto;
  ASSERT_TRUE(result_proto.ParseFromCord(*result_payload));
  EXPECT_EQ(result_proto.related_to().log_context().executive_plan_id(), 3354);
}

TEST(StatusBuilderTest, ExtendedStatusConstructor) {
  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  intrinsic_proto::status::ExtendedStatus context_status_1;
  context_status_1.mutable_status_code()->set_component("Context");
  context_status_1.mutable_status_code()->set_code(123);
  intrinsic_proto::status::ExtendedStatus context_status_2;
  context_status_2.mutable_status_code()->set_component("Context");
  context_status_2.mutable_status_code()->set_code(234);

  StatusBuilder builder("ai.intrinsic.test", 2345,
                        {.title = "Test title",
                         .timestamp = t,
                         .external_report_message = "Ext message",
                         .internal_report_message = "Int message",
                         .log_context = log_context,
                         .context = {context_status_1, context_status_2}});
  ASSERT_FALSE(builder.ok());
  absl::Status result = builder;
  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "ai.intrinsic.test" code: 2345 }
                    title: "Test title"
                    timestamp { seconds: 1711453873 }
                    related_to { log_context { executive_plan_id: 3354 } }
                    external_report { message: "Ext message" }
                    internal_report { message: "Int message" }
                    context { status_code { component: "Context" code: 123 } }
                    context { status_code { component: "Context" code: 234 } }
                  )pb")));
}

TEST(StatusBuilderTest, SetExtendedStatusFromOptions) {
  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  intrinsic_proto::status::ExtendedStatus context_status_1;
  context_status_1.mutable_status_code()->set_component("Context");
  context_status_1.mutable_status_code()->set_code(123);
  intrinsic_proto::status::ExtendedStatus context_status_2;
  context_status_2.mutable_status_code()->set_component("Context");
  context_status_2.mutable_status_code()->set_code(234);

  StatusBuilder builder(absl::InvalidArgumentError("Foo"));
  ASSERT_FALSE(builder.ok());
  builder.SetExtendedStatus("ai.intrinsic.test", 2345,
                            {.title = "Test title",
                             .timestamp = t,
                             .external_report_message = "Ext message",
                             .internal_report_message = "Int message",
                             .log_context = log_context,
                             .context = {context_status_1, context_status_2}});
  ASSERT_FALSE(builder.ok());
  absl::Status result = builder;
  EXPECT_THAT(
      result,
      AllOf(StatusIs(absl::StatusCode::kInvalidArgument),
            StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                EqualsProto(R"pb(
                  status_code { component: "ai.intrinsic.test" code: 2345 }
                  title: "Test title"
                  timestamp { seconds: 1711453873 }
                  related_to { log_context { executive_plan_id: 3354 } }
                  context { status_code { component: "Context" code: 123 } }
                  context { status_code { component: "Context" code: 234 } }
                  external_report { message: "Ext message" }
                  internal_report { message: "Int message" }
                )pb"))));
}

TEST(StatusBuilderTest, WrapExtendedStatus) {
  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  intrinsic_proto::status::ExtendedStatus context_status_1;
  context_status_1.mutable_status_code()->set_component("Context");
  context_status_1.mutable_status_code()->set_code(123);
  intrinsic_proto::status::ExtendedStatus context_status_2;
  context_status_2.mutable_status_code()->set_component("Context");
  context_status_2.mutable_status_code()->set_code(234);

  absl::Status s =
      StatusBuilder(absl::InvalidArgumentError("Foo"))
          .SetExtendedStatus("ai.intrinsic.test", 2345,
                             {.title = "Test title",
                              .external_report_message = "Ext message",
                              .internal_report_message = "Int message",
                              .log_context = log_context});
  StatusBuilder builder(s);
  ASSERT_FALSE(builder.ok());
  absl::Status result = builder.WrapExtendedStatus(
      "ai.intrinsic.outer", 3456,
      {.title = "Outer title",
       .timestamp = t,
       .external_report_message = "Outer Ext message",
       .internal_report_message = "Outer Int message",
       .log_context = log_context,
       .context = {context_status_1, context_status_2}});

  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "ai.intrinsic.outer" code: 3456 }
                    timestamp { seconds: 1711453873 }
                    title: "Outer title"
                    external_report { message: "Outer Ext message" }
                    internal_report { message: "Outer Int message" }
                    related_to { log_context { executive_plan_id: 3354 } }
                    context { status_code { component: "Context" code: 123 } }
                    context { status_code { component: "Context" code: 234 } }
                    context {
                      status_code { component: "ai.intrinsic.test" code: 2345 }
                      title: "Test title"
                      related_to { log_context { executive_plan_id: 3354 } }
                      external_report { message: "Ext message" }
                      internal_report { message: "Int message" }
                    }
                  )pb")));
}

TEST(StatusBuilderTest, WrapExtendedStatusFromPlainStatus) {
  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  intrinsic_proto::status::ExtendedStatus context_status_1;
  context_status_1.mutable_status_code()->set_component("Context");
  context_status_1.mutable_status_code()->set_code(123);
  intrinsic_proto::status::ExtendedStatus context_status_2;
  context_status_2.mutable_status_code()->set_component("Context");
  context_status_2.mutable_status_code()->set_code(234);

  StatusBuilder builder(absl::InvalidArgumentError("Plain message"),
                        Locs::kBar);
  ASSERT_FALSE(builder.ok());
  absl::Status result = builder.WrapExtendedStatus(
      "ai.intrinsic.outer", 3456,
      {.title = "Outer title",
       .timestamp = t,
       .external_report_message = "Outer Ext message",
       .internal_report_message = "Outer Int message",
       .log_context = log_context,
       .context = {context_status_1, context_status_2}});

  EXPECT_THAT(result,
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(

                  EqualsProto(R"pb(
                    status_code { component: "ai.intrinsic.outer" code: 3456 }
                    timestamp { seconds: 1711453873 }
                    title: "Outer title"
                    external_report { message: "Outer Ext message" }
                    internal_report { message: "Outer Int message" }
                    related_to { log_context { executive_plan_id: 3354 } }
                    context { status_code { component: "Context" code: 123 } }
                    context { status_code { component: "Context" code: 234 } }
                    context {
                      status_code { component: "" code: 3 }
                      title: "Generic failure (code INVALID_ARGUMENT)"
                      external_report { message: "Plain message" }
                      internal_report {
                        message: "Error source location: /bar/baz.cc:1337"
                      }
                    }
                  )pb")));
}

#line 1337 "/foo/secret.cc"
const intrinsic::SourceLocation Locs::kSecret = INTRINSIC_LOC;
#line 1337 "/bar/baz.cc"
const intrinsic::SourceLocation Locs::kBar = INTRINSIC_LOC;

}  // namespace
}  // namespace intrinsic
