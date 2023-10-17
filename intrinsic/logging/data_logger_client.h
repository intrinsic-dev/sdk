// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_LOGGING_DATA_LOGGER_CLIENT_H_
#define INTRINSIC_LOGGING_DATA_LOGGER_CLIENT_H_

#include <cstdint>
#include <functional>
#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/logging/proto/log_item.pb.h"
#include "intrinsic/logging/proto/logger_service.grpc.pb.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic::data_logger {

// Initializes a connection to the DataLogger gRPC server. Call once during
// program startup.
absl::Status StartUpIntrinsicLoggerViaGrpc(
    absl::string_view target_address,
    absl::Duration timeout = intrinsic::kGrpcClientConnectDefaultTimeout);

// Initializes the DataLogger client from a stub. Call once during program
// startup. Intended for testing.
absl::Status StartUpIntrinsicLoggerViaStub(
    std::unique_ptr<intrinsic_proto::data_logger::DataLogger::StubInterface>
        stub);

// Generates a random integer with sufficient entropy to be considered globally
// unique.
uint64_t GenerateUid();

// Asynchronously logs a message.
void LogAsync(const intrinsic_proto::data_logger::LogItem& item);
void LogAsync(const intrinsic_proto::data_logger::LogItem& item,
              std::function<void(absl::Status)> callback);
void LogAsync(intrinsic_proto::data_logger::LogItem&& item);
void LogAsync(intrinsic_proto::data_logger::LogItem&& item,
              std::function<void(absl::Status)> callback);

// Sends a request to log `item` to the logging service, waits for a response
// and returns the Status. Use this instead of the async call when:
//   1) You don't mind blocking for a few ms.
//   2) You need to know whether the item was successfully logged to disk.
absl::Status LogAndAwaitResponse(
    const intrinsic_proto::data_logger::LogItem& item);
absl::Status LogAndAwaitResponse(intrinsic_proto::data_logger::LogItem&& item);

}  // namespace intrinsic::data_logger

#endif  // INTRINSIC_LOGGING_DATA_LOGGER_CLIENT_H_
