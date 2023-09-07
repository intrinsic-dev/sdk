// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_server.h"

#include <atomic>
#include <functional>
#include <string>
#include <utility>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/remote_trigger/binary_futex.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_constants.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {

absl::StatusOr<RemoteTriggerServer> RemoteTriggerServer::Create(
    absl::string_view server_id, RemoteTriggerServerCallback&& callback) {
  if (server_id.empty()) {
    return absl::InvalidArgumentError("no server id specified");
  }

  auto request_id = absl::StrCat(server_id, kSemRequestSuffix);
  auto response_id = absl::StrCat(server_id, kSemResponseSuffix);
  intrinsic::icon::SharedMemoryManager shm_manager;
  INTRINSIC_RETURN_IF_ERROR(shm_manager.AddSegment(request_id, BinaryFutex()));
  INTRINSIC_RETURN_IF_ERROR(shm_manager.AddSegment(response_id, BinaryFutex()));
  INTRINSIC_ASSIGN_OR_RETURN(
      auto request_futex, ReadOnlyMemorySegment<BinaryFutex>::Get(request_id));
  INTRINSIC_ASSIGN_OR_RETURN(
      auto response_futex,
      ReadWriteMemorySegment<BinaryFutex>::Get(response_id));

  return RemoteTriggerServer(
      server_id, std::forward<RemoteTriggerServerCallback>(callback),
      std::move(shm_manager), std::move(request_futex),
      std::move(response_futex));
}

RemoteTriggerServer::RemoteTriggerServer(
    absl::string_view server_id, RemoteTriggerServerCallback&& callback,
    SharedMemoryManager&& shm_manager,
    ReadOnlyMemorySegment<BinaryFutex>&& request_futex,
    ReadWriteMemorySegment<BinaryFutex>&& response_futex)
    : server_id_(server_id),
      callback_(std::forward<RemoteTriggerServerCallback>(callback)),
      shm_manager_(std::forward<decltype(shm_manager)>(shm_manager)),
      request_futex_(std::forward<decltype(request_futex)>(request_futex)),
      response_futex_(std::forward<decltype(response_futex)>(response_futex)) {}

RemoteTriggerServer::RemoteTriggerServer(RemoteTriggerServer&& other) noexcept {
  // Make sure that moved server is no longer running.
  other.Stop();

  server_id_ = std::exchange(other.server_id_, "");
  callback_ = std::exchange(other.callback_, nullptr);
  is_running_.store(false);
  shm_manager_ = std::exchange(other.shm_manager_, SharedMemoryManager());
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

    server_id_ = std::exchange(other.server_id_, "");
    callback_ = std::exchange(other.callback_, nullptr);
    is_running_.store(false);
    shm_manager_ = std::exchange(other.shm_manager_, SharedMemoryManager());
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

std::string RemoteTriggerServer::ServerID() const { return server_id_; }

void RemoteTriggerServer::Start() {
  // System is already running.
  if (is_running_.load()) {
    return;
  }
  is_running_.store(true);

  Run();
}

absl::Status RemoteTriggerServer::StartAsync(
    const intrinsic::Thread::Options& thread_options) {
  // System is already running.
  if (bool expected = false;
      !is_running_.compare_exchange_strong(expected, true)) {
    return absl::OkStatus();
  }

  auto ret =
      async_thread_.Start(thread_options, &RemoteTriggerServer::Run, this);
  if (!ret.ok()) {
    Stop();
  }
  return ret;
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
    LOG(ERROR) << "unable to receive client request: " << wait_status.message();
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
    LOG(ERROR) << "unable to send response to client: "
               << post_status.message();
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
      LOG(ERROR) << "unable to receive client request: "
                 << wait_status.message();
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
      LOG(ERROR) << "unable to send response to client: "
                 << post_status.message();
      Stop();
      return;
    }
  }
}

}  // namespace intrinsic::icon
