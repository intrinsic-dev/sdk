// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_server.h"

#include <atomic>
#include <functional>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/binary_futex.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_constants.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/rt_thread.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic::icon {

absl::StatusOr<RemoteTriggerServer> RemoteTriggerServer::Create(
    intrinsic::icon::SharedMemoryManager& shm_manager,
    absl::string_view server_memory_name,
    RemoteTriggerServerCallback&& callback) {
  std::string request_memory_name =
      absl::StrCat(server_memory_name, kSemRequestSuffix);
  std::string response_memory_name =
      absl::StrCat(server_memory_name, kSemResponseSuffix);

  INTR_RETURN_IF_ERROR(shm_manager.AddSegment(
      request_memory_name, /*must_be_used=*/false, BinaryFutex()));
  INTR_RETURN_IF_ERROR(shm_manager.AddSegment(
      response_memory_name, /*must_be_used=*/false, BinaryFutex()));

  INTR_ASSIGN_OR_RETURN(
      auto request_futex,
      shm_manager.Get<ReadOnlyMemorySegment<BinaryFutex>>(request_memory_name));

  INTR_ASSIGN_OR_RETURN(auto response_futex,
                        shm_manager.Get<ReadWriteMemorySegment<BinaryFutex>>(
                            response_memory_name));

  return RemoteTriggerServer(
      server_memory_name, std::forward<RemoteTriggerServerCallback>(callback),
      std::move(request_futex), std::move(response_futex));
}

RemoteTriggerServer::RemoteTriggerServer(
    absl::string_view server_memory_name,
    RemoteTriggerServerCallback&& callback,
    ReadOnlyMemorySegment<BinaryFutex>&& request_futex,
    ReadWriteMemorySegment<BinaryFutex>&& response_futex)
    : server_memory_name_(server_memory_name),
      callback_(std::forward<RemoteTriggerServerCallback>(callback)),
      request_futex_(std::forward<decltype(request_futex)>(request_futex)),
      response_futex_(std::forward<decltype(response_futex)>(response_futex)) {}

RemoteTriggerServer::RemoteTriggerServer(RemoteTriggerServer&& other) noexcept
    : server_memory_name_("") {
  // Make sure that moved server is no longer running.
  other.Stop();
  server_memory_name_ = std::exchange(other.server_memory_name_, "");
  callback_ = std::exchange(other.callback_, nullptr);
  is_running_.store(false);
  request_futex_ =
      std::exchange(other.request_futex_, ReadOnlyMemorySegment<BinaryFutex>());
  response_futex_ = std::exchange(other.response_futex_,
                                  ReadWriteMemorySegment<BinaryFutex>());
}

RemoteTriggerServer& RemoteTriggerServer::operator=(
    RemoteTriggerServer&& other) noexcept {
  if (this != &other) {
    // Make sure that moved server is no longer running.
    other.Stop();

    server_memory_name_ = std::exchange(other.server_memory_name_, "");
    callback_ = std::exchange(other.callback_, nullptr);
    is_running_.store(false);
    request_futex_ = std::exchange(other.request_futex_,
                                   ReadOnlyMemorySegment<BinaryFutex>());
    response_futex_ = std::exchange(other.response_futex_,
                                    ReadWriteMemorySegment<BinaryFutex>());
  }

  return *this;
}

RemoteTriggerServer::~RemoteTriggerServer() {
  Stop();

  if (async_thread_.Joinable()) {
    async_thread_.Join();
  }
}

void RemoteTriggerServer::Start() {
  // System is already running.
  if (is_running_.load()) {
    return;
  }
  is_running_.store(true);

  Run();
}

absl::Status RemoteTriggerServer::StartAsync(
    const intrinsic::ThreadOptions& thread_options) {
  // System is already running.
  if (bool expected = false;
      !is_running_.compare_exchange_strong(expected, true)) {
    return absl::OkStatus();
  }

  if (auto thread = CreateRealtimeCapableThread(
          thread_options, &RemoteTriggerServer::Run, this);
      thread.ok()) {
    async_thread_ = *std::move(thread);
    return absl::OkStatus();
  } else {
    Stop();
    return thread.status();
  }
}

bool RemoteTriggerServer::IsStarted() const { return is_running_.load(); }

void RemoteTriggerServer::Stop() {
  is_running_.store(false);

  if (async_thread_.Joinable()) {
    async_thread_.Join();
  }
}

bool RemoteTriggerServer::Query() {
  // The server was started, we don't allow single queries concurrently.
  if (is_running_.load()) {
    return false;
  }

  auto wait_status = request_futex_.GetValue().WaitFor(absl::Milliseconds(100));
  // If we woke up because of timeout, don't execute the callback.
  if (wait_status.code() == absl::StatusCode::kDeadlineExceeded) {
    return false;
  }
  // Some error occurred, we stop the server.
  if (!wait_status.ok()) {
    INTRINSIC_RT_LOG(ERROR)
        << "unable to receive client request: " << wait_status.message();
    return false;
  }

  // We woke up because we got a request.
  // If the object was moved or went out of scope, the callback_ might be
  // invalid.
  if (callback_ == nullptr) {
    return false;
  }
  // Call the passed in user callback.
  callback_();

  // Notify the caller.
  auto post_status = response_futex_.GetValue().Post();
  // If we're unable to send the response, that usually indicates a corrupt
  // system state in which the semaphores got destroyed. This further results
  // in a timeout on client side, which has potentially better means to react
  // to wrong behavior.
  if (!post_status.ok()) {
    INTRINSIC_RT_LOG(ERROR)
        << "unable to send response to client: " << post_status.message();
  }
  return true;
}

void RemoteTriggerServer::Run() {
  // Given its asynchronous nature, we have to make sure that the server
  // instance is valid at every point. That is, while the server is running, the
  // object may have been moved and destroyed.
  while (is_running_.load()) {
    auto wait_status =
        request_futex_.GetValue().WaitFor(absl::Milliseconds(100));
    // If we woke up because of timeout, don't execute the callback.
    if (wait_status.code() == absl::StatusCode::kDeadlineExceeded) {
      continue;
    }
    // Some error occurred, we stop the server.
    if (!wait_status.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "unable to receive client request: " << wait_status.message();
      Stop();
      return;
    }

    if (!is_running_.load()) {
      return;
    }

    // We woke up because we got a request.
    // If the object was moved or went out of scope, the callback_ might be
    // invalid.
    if (callback_ == nullptr) {
      Stop();
      return;
    }
    // Call the passed in user callback.
    callback_();

    // Notify the caller.
    auto post_status = response_futex_.GetValue().Post();
    // If we're unable to send the response, that usually indicates a corrupt
    // system state in which the semaphores got destroyed. This further results
    // in a timeout on client side, which has potentially better means to react
    // to wrong behavior.
    if (!post_status.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "unable to send response to client: " << post_status.message();
      Stop();
      return;
    }
  }
}

}  // namespace intrinsic::icon
