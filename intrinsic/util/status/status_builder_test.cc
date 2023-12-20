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
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "google/protobuf/wrappers.pb.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic {
namespace {

using ::absl::LogSeverity;
using ::absl::ScopedMockLog;
using ::testing::_;
using ::testing::AnyOf;
using ::testing::Eq;
using ::testing::HasSubstr;
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
      .Times(testing::AtMost(3));
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
      .Times(testing::AtMost(3));
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
      .Times(testing::Exactly(4));
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
  builder.SetPayload(value_proto.GetDescriptor()->full_name(),
                     value_proto.SerializeAsCord());
  absl::Status result = builder;
  std::optional<absl::Cord> result_payload =
      result.GetPayload(value_proto.GetDescriptor()->full_name());
  EXPECT_TRUE(result_payload.has_value());
  google::protobuf::Int64Value result_proto;
  EXPECT_TRUE(result_proto.ParseFromCord(*result_payload));
  EXPECT_EQ(result_proto.value(), value_proto.value());
}

TEST(StatusBuilderTest, SetPayloadIgnoredOnOkStatus) {
  StatusBuilder builder(absl::StatusCode::kOk);
  ASSERT_TRUE(builder.ok());

  google::protobuf::Int64Value value_proto;
  value_proto.set_value(-123);
  builder.SetPayload(value_proto.GetDescriptor()->full_name(),
                     value_proto.SerializeAsCord());
  absl::Status result = builder;
  std::optional<absl::Cord> result_payload =
      result.GetPayload(value_proto.GetDescriptor()->full_name());
  EXPECT_FALSE(result_payload.has_value());
}

TEST(StatusBuilderTest, SetPayloadMultiplePayloads) {
  google::protobuf::Int64Value value1_proto;
  value1_proto.set_value(-123);

  google::protobuf::StringValue value2_proto;
  value2_proto.set_value("foo");

  StatusBuilder builder(absl::StatusCode::kInvalidArgument);
  ASSERT_FALSE(builder.ok());
  builder
      .SetPayload(value1_proto.GetDescriptor()->full_name(),
                  value1_proto.SerializeAsCord())
      .SetPayload(value2_proto.GetDescriptor()->full_name(),
                  value2_proto.SerializeAsCord());

  absl::Status result1 = builder;
  std::optional<absl::Cord> result1_payload =
      result1.GetPayload(value1_proto.GetDescriptor()->full_name());
  EXPECT_TRUE(result1_payload.has_value());

  absl::Status result2 = builder;
  std::optional<absl::Cord> result2_payload =
      result2.GetPayload(value2_proto.GetDescriptor()->full_name());
  EXPECT_TRUE(result2_payload.has_value());

  google::protobuf::Int64Value result1_proto;
  EXPECT_TRUE(result1_proto.ParseFromCord(*result1_payload));
  EXPECT_EQ(result1_proto.value(), value1_proto.value());

  google::protobuf::StringValue result2_proto;
  EXPECT_TRUE(result2_proto.ParseFromCord(*result2_payload));
  EXPECT_EQ(result2_proto.value(), value2_proto.value());
}

#line 1337 "/foo/secret.cc"
const intrinsic::SourceLocation Locs::kSecret = INTRINSIC_LOC;
#line 1337 "/bar/baz.cc"
const intrinsic::SourceLocation Locs::kBar = INTRINSIC_LOC;

}  // namespace
}  // namespace intrinsic
