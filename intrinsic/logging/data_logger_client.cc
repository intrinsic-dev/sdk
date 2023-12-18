// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/logging/data_logger_client.h"

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string_view>
#include <utility>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/random/random.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpcpp/channel.h"
#include "intrinsic/logging/proto/log_item.pb.h"
#include "intrinsic/logging/proto/logger_service.pb.h"
#include "intrinsic/logging/structured_logging_client.h"
#include "intrinsic/util/grpc/grpc.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::data_logger {
namespace {

constexpr std::string_view kLoggerNotInitialized =
    "Attempting to log before logger initialized.";

class LoggingData {
 public:
  static LoggingData& Instance() {
    static auto* logging_data = new LoggingData();
    return *logging_data;
  }

  absl::Status Init(std::unique_ptr<StructuredLoggingClient::LoggerStub> stub) {
    logging_client_.emplace(std::move(stub));
    return absl::OkStatus();
  }

  absl::Status Log(const intrinsic_proto::data_logger::LogItem& item) {
    if (!logging_client_.has_value()) {
      return absl::FailedPreconditionError(kLoggerNotInitialized);
    }
    return logging_client_->Log(item);
  }

  absl::Status Log(intrinsic_proto::data_logger::LogItem&& item) {
    if (!logging_client_.has_value()) {
      return absl::FailedPreconditionError(kLoggerNotInitialized);
    }
    return logging_client_->Log(std::move(item));
  }

  void LogAsync(const intrinsic_proto::data_logger::LogItem& item) {
    if (!logging_client_.has_value()) {
      LOG_FIRST_N(WARNING, 1) << kLoggerNotInitialized << " Doing nothing.";
      return;
    }
    return logging_client_->LogAsync(item);
  }

  void LogAsync(const intrinsic_proto::data_logger::LogItem& item,
                std::function<void(absl::Status)> callback) {
    if (!logging_client_.has_value()) {
      LOG_FIRST_N(WARNING, 1) << kLoggerNotInitialized << " Doing nothing.";
      return;
    }
    return logging_client_->LogAsync(item, std::move(callback));
  }

  void LogAsync(intrinsic_proto::data_logger::LogItem&& item) {
    if (!logging_client_.has_value()) {
      LOG_FIRST_N(WARNING, 1) << kLoggerNotInitialized << " Doing nothing.";
      return;
    }
    return logging_client_->LogAsync(std::move(item));
  }

  void LogAsync(intrinsic_proto::data_logger::LogItem&& item,
                std::function<void(absl::Status)> callback) {
    if (!logging_client_.has_value()) {
      LOG_FIRST_N(WARNING, 1) << kLoggerNotInitialized << " Doing nothing.";
      return;
    }
    return logging_client_->LogAsync(std::move(item), std::move(callback));
  }

 private:
  LoggingData() = default;

  std::optional<StructuredLoggingClient> logging_client_;
};

}  // namespace

uint64_t GenerateUid() { return absl::Uniform<uint64_t>(absl::BitGen()); }

void LogAsync(const intrinsic_proto::data_logger::LogItem& item) {
  LoggingData::Instance().LogAsync(item);
}

void LogAsync(const intrinsic_proto::data_logger::LogItem& item,
              std::function<void(absl::Status)> callback) {
  LoggingData::Instance().LogAsync(item, std::move(callback));
}

void LogAsync(intrinsic_proto::data_logger::LogItem&& item) {
  LoggingData::Instance().LogAsync(std::move(item));
}

void LogAsync(intrinsic_proto::data_logger::LogItem&& item,
              std::function<void(absl::Status)> callback) {
  LoggingData::Instance().LogAsync(std::move(item), std::move(callback));
}

absl::Status LogAndAwaitResponse(
    const intrinsic_proto::data_logger::LogItem& item) {
  return LoggingData::Instance().Log(item);
}

absl::Status LogAndAwaitResponse(intrinsic_proto::data_logger::LogItem&& item) {
  return LoggingData::Instance().Log(std::move(item));
}

absl::Status StartUpIntrinsicLoggerViaGrpc(absl::string_view target_address,
                                           absl::Duration timeout) {
  INTR_ASSIGN_OR_RETURN(
      std::shared_ptr<grpc::Channel> channel,
      CreateClientChannel(target_address, absl::Now() + timeout,
                          UnlimitedMessageSizeGrpcChannelArgs()));
  return StartUpIntrinsicLoggerViaStub(
      intrinsic_proto::data_logger::DataLogger::NewStub(channel));
}

absl::Status StartUpIntrinsicLoggerViaStub(
    std::unique_ptr<intrinsic_proto::data_logger::DataLogger::StubInterface>
        stub) {
  LoggingData& logging_data = LoggingData::Instance();
  return logging_data.Init(std::move(stub));
}

}  // namespace intrinsic::data_logger
