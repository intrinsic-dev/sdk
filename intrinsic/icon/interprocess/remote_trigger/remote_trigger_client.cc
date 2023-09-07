// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_client.h"

#include <atomic>
#include <memory>
#include <string>
#include <utility>

#include "absl/cleanup/cleanup.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/remote_trigger/binary_futex.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_constants.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"

namespace intrinsic::icon {

RemoteTriggerClient::AsyncRequest::AsyncRequest(
    ReadOnlyMemorySegment<BinaryFutex>* response_futex,
    std::atomic<bool>* request_started)
    : response_futex_(response_futex), request_started_(request_started) {}

RemoteTriggerClient::AsyncRequest::AsyncRequest(AsyncRequest&& other) noexcept
    : response_futex_(other.response_futex_),
      request_started_(std::exchange(other.request_started_, nullptr)) {}

RemoteTriggerClient::AsyncRequest& RemoteTriggerClient::AsyncRequest::operator=(
    AsyncRequest&& other) noexcept {
  if (this != &other) {
    response_futex_ = std::move(other.response_futex_);
    request_started_ = std::exchange(other.request_started_, nullptr);
  }

  return *this;
}

RemoteTriggerClient::AsyncRequest::~AsyncRequest() noexcept {
  if (request_started_ != nullptr) {
    request_started_->store(false);
  }
}

bool RemoteTriggerClient::AsyncRequest::Valid() const {
  if (request_started_ == nullptr) {
    return false;
  }
  return request_started_->load();
}

bool RemoteTriggerClient::AsyncRequest::Ready() const {
  return response_futex_->GetValue().Value() > 0;
}

RealtimeStatus RemoteTriggerClient::AsyncRequest::WaitUntil(
    absl::Time deadline) {
  if (!Valid()) {
    return FailedPreconditionError("async request no longer valid");
  }

  auto response = response_futex_->GetValue().WaitUntil(deadline);
  request_started_->store(false);
  // We have to set the pointer to null, indicating in the destructor that we've
  // completed the async request and already cleared the `request_started_`
  // flag.
  request_started_ = nullptr;
  return response;
}

absl::StatusOr<RemoteTriggerClient> RemoteTriggerClient::Create(
    absl::string_view server_id, bool auto_connect) {
  if (server_id.empty()) {
    return absl::InvalidArgumentError("no server id specified");
  }

  if (auto_connect) {
    auto request_id = absl::StrCat(server_id, kSemRequestSuffix);
    auto response_id = absl::StrCat(server_id, kSemResponseSuffix);
    INTRINSIC_ASSIGN_OR_RETURN(
        auto request_futex,
        ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
    INTRINSIC_ASSIGN_OR_RETURN(
        auto response_futex,
        ReadOnlyMemorySegment<BinaryFutex>::Get(response_id));

    return RemoteTriggerClient(server_id, std::move(request_futex),
                               std::move(response_futex));
  }

  return RemoteTriggerClient(server_id);
}

RemoteTriggerClient::RemoteTriggerClient(absl::string_view server_id)
    : server_id_(server_id) {}

RemoteTriggerClient::RemoteTriggerClient(
    absl::string_view server_id,
    ReadWriteMemorySegment<BinaryFutex>&& request_futex,
    ReadOnlyMemorySegment<BinaryFutex>&& response_futex)
    : server_id_(server_id),
      request_futex_(std::forward<decltype(request_futex)>(request_futex)),
      response_futex_(std::forward<decltype(response_futex)>(response_futex)) {}

RemoteTriggerClient::RemoteTriggerClient(RemoteTriggerClient&& other) noexcept
    : server_id_(std::exchange(other.server_id_, "")),
      request_futex_(std::exchange(other.request_futex_,
                                   ReadWriteMemorySegment<BinaryFutex>())),
      response_futex_(std::exchange(other.response_futex_,
                                    ReadOnlyMemorySegment<BinaryFutex>())),
      request_started_(false) {}

RemoteTriggerClient& RemoteTriggerClient::operator=(
    RemoteTriggerClient&& other) noexcept {
  if (this != &other) {
    server_id_ = std::exchange(other.server_id_, "");
    request_futex_ = std::exchange(other.request_futex_,
                                   ReadWriteMemorySegment<BinaryFutex>());
    response_futex_ = std::exchange(other.response_futex_,
                                    ReadOnlyMemorySegment<BinaryFutex>());
    request_started_.store(false);
  }
  return *this;
}

std::string RemoteTriggerClient::ServerID() const { return server_id_; }

absl::Status RemoteTriggerClient::Connect() {
  if (IsConnected()) {
    return absl::OkStatus();
  }

  auto request_id = absl::StrCat(server_id_, kSemRequestSuffix);
  auto response_id = absl::StrCat(server_id_, kSemResponseSuffix);
  INTRINSIC_ASSIGN_OR_RETURN(
      request_futex_, ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
  INTRINSIC_ASSIGN_OR_RETURN(
      response_futex_, ReadOnlyMemorySegment<BinaryFutex>::Get(response_id));

  return absl::OkStatus();
}

bool RemoteTriggerClient::IsConnected() const {
  return request_futex_.IsValid() && response_futex_.IsValid();
}

RealtimeStatus RemoteTriggerClient::Trigger(absl::Time deadline) {
  if (!IsConnected()) {
    return InvalidArgumentError("client not connected");
  }
  if (absl::Now() > deadline) {
    return DeadlineExceededError("specified deadline is in the past");
  }
  if (bool expected = false;
      !request_started_.compare_exchange_strong(expected, true)) {
    return AlreadyExistsError("request already triggered");
  }

  // Clear the `request_started_` flag in any case when we leave the scope of
  // this function.
  absl::Cleanup clear_request_flag = [this] { request_started_.store(false); };

  // Signal the server to start the execution.
  INTRINSIC_RT_RETURN_IF_ERROR(request_futex_.GetValue().Post());
  // Wait for the response from the server.
  return response_futex_.GetValue().WaitUntil(deadline);
}

RealtimeStatusOr<RemoteTriggerClient::AsyncRequest>
RemoteTriggerClient::TriggerAsync() {
  if (!IsConnected()) {
    return InvalidArgumentError("client not connected");
  }

  if (bool expected = false;
      !request_started_.compare_exchange_strong(expected, true)) {
    return AlreadyExistsError("request already triggered");
  }

  INTRINSIC_RT_RETURN_IF_ERROR(request_futex_.GetValue().Post());
  return AsyncRequest(&response_futex_, &request_started_);
}

}  // namespace intrinsic::icon
