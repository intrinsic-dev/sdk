// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_builder.h"

#include <array>
#include <memory>
#include <ostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "absl/base/log_severity.h"
#include "absl/base/thread_annotations.h"
#include "absl/container/flat_hash_map.h"
#include "absl/debugging/stacktrace.h"
#include "absl/debugging/symbolize.h"
#include "absl/log/log.h"
#include "absl/log/log_entry.h"
#include "absl/log/log_sink.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic {

namespace {
std::string GetSymbolizedStackTraceAsString(int max_depth = 50,
                                            int skip_count = 0,
                                            bool demangle = true) {
  std::string result;
  int skip_count_including_self = skip_count + 1;
  std::vector<void*> stack_trace;
  stack_trace.resize(max_depth);
  stack_trace.resize(absl::GetStackTrace(stack_trace.data(), max_depth,
                                         skip_count_including_self));
  std::array<char, 256> symbol_name_buffer;
  for (void* pc : stack_trace) {
    if (absl::Symbolize(pc, symbol_name_buffer.data(),
                        symbol_name_buffer.size())) {
      result += absl::StrFormat("%08p: %s\n", pc, symbol_name_buffer.data());
    } else {
      result += absl::StrFormat("%08p: [unknown]\n", pc);
    }
  }
  return result;
}

}  // namespace

StatusBuilder::Rep::Rep(const Rep& r)
    : logging_mode(r.logging_mode),
      log_severity(r.log_severity),
      n(r.n),
      period(r.period),
      stream(r.stream.str()),
      should_log_stack_trace(r.should_log_stack_trace),
      message_join_style(r.message_join_style),
      sink(r.sink) {}

absl::Status StatusBuilder::JoinMessageToStatus(absl::Status s,
                                                std::string_view msg,
                                                MessageJoinStyle style) {
  if (msg.empty()) {
    return s;
  }
  if (style == MessageJoinStyle::kAnnotate) {
    return AnnotateStatus(s, msg);
  }
  std::string new_msg = style == MessageJoinStyle::kPrepend
                            ? absl::StrCat(msg, s.message())
                            : absl::StrCat(s.message(), msg);
  absl::Status result = WithMessage(s, new_msg);
  SetStatusCode(s.code(), &result);
  return result;
}

void StatusBuilder::ConditionallyLog(const absl::Status& status) const {
  if (rep_->logging_mode == Rep::LoggingMode::kDisabled) {
    return;
  }

  absl::LogSeverity severity = rep_->log_severity;
  switch (rep_->logging_mode) {
    case Rep::LoggingMode::kDisabled:
    case Rep::LoggingMode::kLog:
      break;
    case Rep::LoggingMode::kLogEveryN: {
      struct LogSites {
        absl::Mutex mutex;
        absl::flat_hash_map<std::pair<const void*, uint>, uint>
            counts_by_file_and_line ABSL_GUARDED_BY(mutex);
      };
      static auto* log_every_n_sites = new LogSites();

      log_every_n_sites->mutex.Lock();
      const uint count =
          log_every_n_sites
              ->counts_by_file_and_line[{loc_.file_name(), loc_.line()}]++;
      log_every_n_sites->mutex.Unlock();

      if (count % rep_->n != 0) {
        return;
      }
      break;
    }
    case Rep::LoggingMode::kLogEveryPeriod: {
      struct LogSites {
        absl::Mutex mutex;
        absl::flat_hash_map<std::pair<const void*, uint>, absl::Time>
            next_log_by_file_and_line ABSL_GUARDED_BY(mutex);
      };
      static auto* log_every_sites = new LogSites();

      const auto now = absl::Now();
      absl::MutexLock lock(&log_every_sites->mutex);
      absl::Time& next_log =
          log_every_sites
              ->next_log_by_file_and_line[{loc_.file_name(), loc_.line()}];
      if (now < next_log) {
        return;
      }
      next_log = now + rep_->period;
      break;
    }
  }

  absl::LogSink* const sink = rep_->sink;
  const std::string maybe_stack_trace =
      rep_->should_log_stack_trace
          ? absl::StrCat("\n", GetSymbolizedStackTraceAsString(
                                   /*max_depth=*/50, /*skip_count=*/1))
          : "";
  const int verbose_level = absl::LogEntry::kNoVerboseLevel;
  if (sink != nullptr) {
    LOG(LEVEL(severity))
            .AtLocation(loc_.file_name(), loc_.line())
            .ToSinkAlso(sink)
            .WithVerbosity(verbose_level)
        << status << maybe_stack_trace;
  } else {
    LOG(LEVEL(severity))
            .AtLocation(loc_.file_name(), loc_.line())
            .WithVerbosity(verbose_level)
        << status << maybe_stack_trace;
  }
}

void StatusBuilder::SetStatusCode(absl::StatusCode canonical_code,
                                  absl::Status* status) {
  if (status->code() == canonical_code) {
    return;
  }
  absl::Status new_status(canonical_code, status->message());
  CopyPayloads(*status, &new_status);
  using std::swap;
  swap(*status, new_status);
}

void StatusBuilder::CopyPayloads(const absl::Status& src, absl::Status* dst) {
  src.ForEachPayload([&](std::string_view type_url, absl::Cord payload) {
    dst->SetPayload(type_url, payload);
  });
}

absl::Status StatusBuilder::WithMessage(const absl::Status& status,
                                        std::string_view msg) {
  auto ret = absl::Status(status.code(), msg);
  CopyPayloads(status, &ret);
  return ret;
}

absl::Status StatusBuilder::AnnotateStatus(const absl::Status& s,
                                           std::string_view msg) {
  if (s.ok() || msg.empty()) {
    return s;
  }

  std::string_view new_msg = msg;
  std::string annotated;
  if (!s.message().empty()) {
    absl::StrAppend(&annotated, s.message(), "; ", msg);
    new_msg = annotated;
  }
  absl::Status result = WithMessage(s, new_msg);
  SetStatusCode(s.code(), &result);
  return result;
}

absl::Status StatusBuilder::CreateStatusAndConditionallyLog() && {
  absl::Status result = JoinMessageToStatus(
      std::move(status_), rep_->stream.str(), rep_->message_join_style);

  ConditionallyLog(result);

  // We consumed the status above, we set it to some error just to prevent
  // people relying on it become OK or something.
  status_ = absl::UnknownError("");
  rep_ = nullptr;
  return result;
}

std::ostream& operator<<(std::ostream& os, const StatusBuilder& builder) {
  return os << static_cast<absl::Status>(builder);
}

std::ostream& operator<<(std::ostream& os, StatusBuilder&& builder) {
  return os << static_cast<absl::Status>(std::move(builder));
}

StatusBuilder AbortedErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kAborted, location);
}

StatusBuilder AlreadyExistsErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kAlreadyExists, location);
}

StatusBuilder CancelledErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kCancelled, location);
}

StatusBuilder DataLossErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kDataLoss, location);
}

StatusBuilder DeadlineExceededErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kDeadlineExceeded, location);
}

StatusBuilder FailedPreconditionErrorBuilder(
    intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kFailedPrecondition, location);
}

StatusBuilder InternalErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kInternal, location);
}

StatusBuilder InvalidArgumentErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kInvalidArgument, location);
}

StatusBuilder NotFoundErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kNotFound, location);
}

StatusBuilder OutOfRangeErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kOutOfRange, location);
}

StatusBuilder PermissionDeniedErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kPermissionDenied, location);
}

StatusBuilder UnauthenticatedErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kUnauthenticated, location);
}

StatusBuilder ResourceExhaustedErrorBuilder(
    intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kResourceExhausted, location);
}

StatusBuilder UnavailableErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kUnavailable, location);
}

StatusBuilder UnimplementedErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kUnimplemented, location);
}

StatusBuilder UnknownErrorBuilder(intrinsic::SourceLocation location) {
  return StatusBuilder(absl::StatusCode::kUnknown, location);
}

}  // namespace intrinsic
