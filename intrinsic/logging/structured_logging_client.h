// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_LOGGING_STRUCTURED_LOGGING_CLIENT_H_
#define INTRINSIC_LOGGING_STRUCTURED_LOGGING_CLIENT_H_

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "grpcpp/channel.h"
#include "intrinsic/logging/proto/log_item.pb.h"
#include "intrinsic/logging/proto/logger_service.grpc.pb.h"

namespace intrinsic {

// A client class to interact with the structured logging service.
// The class is thread-safe. If multiple gRPC services are available at the same
// address it is recommended to share a channel between them.
class StructuredLoggingClient {
 public:
  using LogItem = ::intrinsic_proto::data_logger::LogItem;
  using LogOptions = ::intrinsic_proto::data_logger::LogOptions;
  using LoggerStub = ::intrinsic_proto::data_logger::DataLogger::StubInterface;

  struct ListResult {
    std::vector<LogItem> log_items;
    std::string next_page_token;
  };

  using GetResult = ListResult;

  // Creates a structured logging client by connecting to the specified address.
  // If the connection cannot be established when the deadline is met, the
  // function returns an error.
  static absl::StatusOr<StructuredLoggingClient> Create(
      absl::string_view address, absl::Time deadline);

  // Constructs a client from an existing gRPC channel.
  explicit StructuredLoggingClient(
      const std::shared_ptr<grpc::Channel>& channel);

  // Direct stub injection, typically used to inject mocks for testing.
  explicit StructuredLoggingClient(std::unique_ptr<LoggerStub> stub);

  StructuredLoggingClient(const StructuredLoggingClient&) = delete;
  StructuredLoggingClient& operator=(const StructuredLoggingClient&) = delete;

  // Move construction and assignment.
  StructuredLoggingClient(StructuredLoggingClient&&);
  StructuredLoggingClient& operator=(StructuredLoggingClient&&);

  ~StructuredLoggingClient();

  // Logs an r-value item.
  absl::Status Log(LogItem&& item);

  // Logs an item. The item will be internally copied to the logging request.
  absl::Status Log(const LogItem& item);

  // Performs asynchronous logging of an r-value item. A default callback is
  // installed, which prints a warning message in case of a logging failure.
  void LogAsync(LogItem&& item);

  // Performs asynchronous logging of an r-value item and calls the user
  // specified callback when done.
  void LogAsync(LogItem&& item, std::function<void(absl::Status)> callback);

  // Performs asynchronous logging of an item. The item will be internally
  // copied to the logging request. A default callback is
  // installed, which prints a warning message in case of a logging failure.
  void LogAsync(const LogItem& item);

  // Performs asynchronous logging of an item and calls the user specified
  // callback when done. The item will be internally copied to the logging
  // request.
  void LogAsync(const LogItem& item,
                std::function<void(absl::Status)> callback);

  // Returns a list of `event_source` that can be requested using list requests.
  absl::StatusOr<std::vector<std::string>> ListLogSources();

  // Returns a list of log items for the specified event source. If no data is
  // available, an empty vector is returned and the function does not generate
  // an error.
  absl::StatusOr<GetResult> GetLogItems(absl::string_view event_source);

  // Returns a list of log items for the specified event source. If no data is
  // available, an empty vector is returned and the function does not generate
  // an error.
  // The function supports pagination. On each request 'page_size' items are
  // returned if that many are available. In addition a 'page_token' is returned
  // which can be used on the next request to request the next batch of items.
  // Filtering is supported in the same way as documented on the logging
  // service.
  absl::StatusOr<GetResult> GetLogItems(
      absl::string_view event_source, int page_size,
      absl::string_view page_token = "",
      absl::Time start_time = absl::UniversalEpoch(),
      absl::Time end_time = absl::Now());

  // Returns the most recent LogItem that has been logged for the given event
  // source. If no LogItem with a matching event_source has been logged since
  // --file_ttl, then NOT_FOUND will be returned instead.
  absl::StatusOr<LogItem> GetMostRecentItem(absl::string_view event_source);

  // Writes all log files of the specified 'event_sources' to GCS.
  absl::StatusOr<std::vector<std::string>> SyncAndRotateLogs(
      const std::vector<std::string>& event_sources);

  // Writes all log files to GCS.
  absl::StatusOr<std::vector<std::string>> SyncAndRotateLogs();

  // Set the logging configuration for an event_source
  absl::Status SetLogOptions(
      absl::string_view event_source,
      const intrinsic_proto::data_logger::LogOptions& options);

  // Get the logging configuration for an event_source
  absl::StatusOr<LogOptions> GetLogOptions(absl::string_view event_source);

 private:
  // Use of pimpl / firewall idiom to hide gRPC details.
  struct StructuredLoggingClientImpl;
  std::unique_ptr<StructuredLoggingClientImpl> impl_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_LOGGING_STRUCTURED_LOGGING_CLIENT_H_
