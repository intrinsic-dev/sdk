// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/logging/structured_logging_client.h"

#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "grpcpp/channel.h"
#include "grpcpp/client_context.h"
#include "grpcpp/support/status.h"
#include "intrinsic/logging/proto/logger_service.grpc.pb.h"
#include "intrinsic/logging/proto/logger_service.pb.h"
#include "intrinsic/util/grpc/grpc.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

using intrinsic_proto::data_logger::LogOptions;

struct StructuredLoggingClient::StructuredLoggingClientImpl {
  explicit StructuredLoggingClientImpl(
      const std::shared_ptr<grpc::Channel>& channel)
      : stub(intrinsic_proto::data_logger::DataLogger::NewStub(channel)) {}

  explicit StructuredLoggingClientImpl(
      std::unique_ptr<StructuredLoggingClient::LoggerStub> stub)
      : stub(std::move(stub)) {}

  // Following the general documentation here:
  // https://g3doc.corp.google.com/net/grpc/g3doc/grpc_prod/cpp/client_side_operation.md#creating-channels-and-stubs
  // we do not need to protect the stub with a dedicated mutex since the "stub
  // is thread-safe and should be re-used for multiple (concurrent) RPCs".
  std::unique_ptr<intrinsic_proto::data_logger::DataLogger::StubInterface> stub;
};

absl::StatusOr<StructuredLoggingClient> StructuredLoggingClient::Create(
    absl::string_view address, absl::Time deadline) {
  INTR_ASSIGN_OR_RETURN(
      std::shared_ptr<grpc::Channel> channel,
      CreateClientChannel(address, deadline,
                          UnlimitedMessageSizeGrpcChannelArgs()));
  return StructuredLoggingClient(channel);
}

StructuredLoggingClient::StructuredLoggingClient(
    const std::shared_ptr<grpc::Channel>& channel)
    : impl_(std::make_unique<StructuredLoggingClientImpl>(channel)) {}

StructuredLoggingClient::StructuredLoggingClient(
    std::unique_ptr<StructuredLoggingClient::LoggerStub> stub)
    : impl_(std::make_unique<StructuredLoggingClientImpl>(std::move(stub))) {}

// Functions are defaulted here because of the pimpl idiom.
// StructuredLoggingClientImpl is an incomplete type when only inspecting the
// header file.

StructuredLoggingClient::StructuredLoggingClient(StructuredLoggingClient&&) =
    default;

StructuredLoggingClient& StructuredLoggingClient::operator=(
    StructuredLoggingClient&&) = default;

StructuredLoggingClient::~StructuredLoggingClient() = default;

// Dispatches one log item to the data logger.
absl::Status StructuredLoggingClient::Log(LogItem&& item) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::LogRequest request;
  *request.mutable_item() = std::move(item);
  google::protobuf::Empty response;
  return ToAbslStatus(impl_->stub->Log(&context, request, &response));
}

absl::Status StructuredLoggingClient::Log(const LogItem& item) const {
  LogItem log_item = item;
  return Log(std::move(log_item));
}

void StructuredLoggingClient::LogAsync(LogItem&& item) const {
  std::string event_source = item.metadata().event_source();
  return LogAsync(std::move(item),
                  [event_source = std::move(event_source)](absl::Status s) {
                    if (!s.ok()) {
                      LOG(WARNING) << "Failed to log item for event source '"
                                   << event_source << "' in async call.";
                    }
                  });
}

void StructuredLoggingClient::LogAsync(
    LogItem&& item, std::function<void(absl::Status)> callback) const {
  struct LogArgs {
    // Both, the context as well as the response need to persist until the
    // callback function is invoked regardless of whether the response is used
    // in the callback or not.
    grpc::ClientContext context;
    google::protobuf::Empty response;
    std::function<void(absl::Status)> callback;
  };

  intrinsic_proto::data_logger::LogRequest request;
  *request.mutable_item() = std::move(item);

  // We need a shared_ptr here because the lambda below must remain copyable and
  // this is not the case if we used a unique_ptr.
  auto args = std::make_shared<LogArgs>();
  args->callback = std::move(callback);
  impl_->stub->async()->Log(
      &args->context, &request, &args->response,
      [args](grpc::Status s) { args->callback(ToAbslStatus(s)); });
}

void StructuredLoggingClient::LogAsync(const LogItem& item) const {
  LogItem log_item = item;
  return LogAsync(std::move(log_item));
}

void StructuredLoggingClient::LogAsync(
    const LogItem& item, std::function<void(absl::Status)> callback) const {
  LogItem log_item = item;
  return LogAsync(std::move(log_item), std::move(callback));
}

// Returns a list of `event_source` that can be requested using GetLogItems.
absl::StatusOr<std::vector<std::string>>
StructuredLoggingClient::ListLogSources() const {
  grpc::ClientContext context;
  google::protobuf::Empty request;
  intrinsic_proto::data_logger::ListLogSourcesResponse response;
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(impl_->stub->ListLogSources(&context, request, &response)));
  std::vector<std::string> log_sources(response.event_sources().begin(),
                                       response.event_sources().end());
  return log_sources;
}

absl::StatusOr<StructuredLoggingClient::GetResult>
StructuredLoggingClient::GetLogItems(absl::string_view event_source) const {
  return GetLogItems(event_source, std::numeric_limits<int>::max());
}

absl::StatusOr<StructuredLoggingClient::GetResult>
StructuredLoggingClient::GetLogItems(absl::string_view event_source,
                                     absl::Time start_time,
                                     absl::Time end_time) const {
  return GetLogItems(event_source, std::numeric_limits<int>::max(), "",
                     start_time, end_time);
}

absl::StatusOr<StructuredLoggingClient::GetResult>
StructuredLoggingClient::GetLogItems(absl::string_view event_source,
                                     int page_size,
                                     absl::string_view page_token,
                                     absl::Time start_time,
                                     absl::Time end_time) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::GetLogItemsRequest request;
  intrinsic_proto::data_logger::GetLogItemsResponse response;
  request.add_event_sources(std::string{event_source});
  INTR_ASSIGN_OR_RETURN(auto start_time_proto, ToProto(start_time));
  *request.mutable_start_time() = std::move(start_time_proto);
  INTR_ASSIGN_OR_RETURN(auto end_time_proto, ToProto(end_time));
  *request.mutable_end_time() = std::move(end_time_proto);
  request.set_max_num_items(page_size);
  if (!page_token.empty()) {
    request.set_cursor(std::string{page_token});
  }
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(impl_->stub->GetLogItems(&context, request, &response)));
  std::vector<intrinsic_proto::data_logger::LogItem> log_items(
      std::make_move_iterator(response.log_items().begin()),
      std::make_move_iterator(response.log_items().end()));
  return GetResult{.log_items = std::move(log_items),
                   .next_page_token = std::move(response.cursor())};
}

// Returns the most recent LogItem that has been logged for the given event
// source, from an in-memory cache. If no LogItem with a matching event_source
// has been logged since --file_ttl, then NOT_FOUND will be returned instead.
absl::StatusOr<intrinsic_proto::data_logger::LogItem>
StructuredLoggingClient::GetMostRecentItem(
    absl::string_view event_source) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::GetMostRecentItemRequest request;
  request.set_event_source(std::string{event_source});
  intrinsic_proto::data_logger::GetMostRecentItemResponse response;
  INTR_RETURN_IF_ERROR(ToAbslStatus(
      impl_->stub->GetMostRecentItem(&context, request, &response)));
  return std::move(response.item());
}

// Flushes all remaining LogItems
absl::StatusOr<std::vector<std::string>>
StructuredLoggingClient::SyncAndRotateLogs(
    const std::vector<std::string>& event_sources) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::SyncRequest request;
  *request.mutable_event_sources() = {event_sources.begin(),
                                      event_sources.end()};
  request.set_sync_all(false);
  intrinsic_proto::data_logger::SyncResponse response;
  INTR_RETURN_IF_ERROR(ToAbslStatus(
      impl_->stub->SyncAndRotateLogs(&context, request, &response)));
  std::vector<std::string> synced_event_sources{
      std::make_move_iterator(response.event_sources().begin()),
      std::make_move_iterator(response.event_sources().end())};
  return synced_event_sources;
}

absl::StatusOr<std::vector<std::string>>
StructuredLoggingClient::SyncAndRotateLogs() const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::SyncRequest request;
  request.set_sync_all(true);
  intrinsic_proto::data_logger::SyncResponse response;
  INTR_RETURN_IF_ERROR(ToAbslStatus(
      impl_->stub->SyncAndRotateLogs(&context, request, &response)));
  std::vector<std::string> synced_event_sources{
      std::make_move_iterator(response.event_sources().begin()),
      std::make_move_iterator(response.event_sources().end())};
  return synced_event_sources;
}

absl::Status StructuredLoggingClient::SetLogOptions(
    const std::map<std::string, intrinsic_proto::data_logger::LogOptions>&
        options) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::SetLogOptionsRequest request;
  for (const auto& [event_source, log_options] : options) {
    request.mutable_log_options()->insert({event_source, log_options});
  }
  intrinsic_proto::data_logger::SetLogOptionsResponse response;
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(impl_->stub->SetLogOptions(&context, request, &response)));
  return absl::OkStatus();
}

absl::StatusOr<LogOptions> StructuredLoggingClient::GetLogOptions(
    absl::string_view event_source) const {
  grpc::ClientContext context;
  intrinsic_proto::data_logger::GetLogOptionsRequest request;
  request.set_event_source(std::string{event_source});
  intrinsic_proto::data_logger::GetLogOptionsResponse response;
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(impl_->stub->GetLogOptions(&context, request, &response)));
  return response.log_options();
}

}  // namespace intrinsic
