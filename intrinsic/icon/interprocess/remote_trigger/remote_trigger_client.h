// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_INTERPROCESS_REMOTE_TRIGGER_REMOTE_TRIGGER_CLIENT_H_
#define INTRINSIC_ICON_INTERPROCESS_REMOTE_TRIGGER_REMOTE_TRIGGER_CLIENT_H_

#include <atomic>
#include <memory>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/remote_trigger/binary_futex.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_or.h"

namespace intrinsic::icon {

// A RemoteTriggerClient signals a RemoteTriggerServer to execute the server's
// callback function. This callback function is specified when the server is
// created. The client solely triggers the execution on the server side.
// Remote denotes support for inter-process communication, yet still
// requires the connection to be machine-local, meaning the two processes for
// the client and server have to be executed on the same computer. The
// connection between a server and client is based on a named semaphore. The
// `server_id` passed into the server and client thus have to match in order to
// establish a connection.
// There is a recommended 1:1 relationship between a server and a client;
// the server can't distinguish a request when being triggered by various
// clients. While we can make sure that one client can only trigger one request
// at the time, we can't easily prevent multiple clients (each in their own
// process) to trigger a request at the same time.
class RemoteTriggerClient {
 public:
  // The AsyncRequest holds information about an asynchronous request call.
  // Once a asynchronous trigger is issued, the AsyncRequest object can later be
  // queried for the response of that trigger request.
  // That way, a call to `Trigger` is not forced to wait on the server response.
  // Note, despite being asynchronous, given that there's no direct link between
  // a request and a response, only one AsyncRequest per client can be executed
  // at a time. The request is considered complete through a successful call to
  // `WaitUntil` or when the instance goes out of scope. As long as neither of
  // these conditions are fulfilled, no second request can be issued by the
  // client.
  class AsyncRequest {
   public:
    // The constructor takes the semaphore from the `RemoteTriggerClient` to
    // later on wait for the response. The atomic bool is used to signal the
    // server once the request is fulfilled.
    explicit AsyncRequest(ReadOnlyMemorySegment<BinaryFutex>* response_futex,
                          std::atomic<bool>* request_started);

    AsyncRequest() = default;

    // This class is move-only.
    AsyncRequest(const AsyncRequest& other) = delete;
    AsyncRequest& operator=(const AsyncRequest& other) = delete;
    AsyncRequest(AsyncRequest&& other) noexcept;
    AsyncRequest& operator=(AsyncRequest&& other) noexcept;
    ~AsyncRequest() noexcept;

    // Indicates whether the request is still valid.
    bool Valid() const;

    // Indicates whether the server has signaled a response to the request.
    bool Ready() const;

    // Waits for the server to respond.
    // Similar to a call to `Trigger()`, a call to `WaitUntil()` waits for the
    // server to respond to the initial request. The `deadline` argument
    // indicates how long we should wait for this response before timing out. By
    // default, we wait forever.
    // Returns a `DeadlineExceeded` error code when timed out.
    // Returns `FailedPrecondition` error if request is invalid.
    // Returns `OkStatus` otherwise.
    RealtimeStatus WaitUntil(absl::Time deadline = absl::InfiniteFuture());

   private:
    ReadOnlyMemorySegment<BinaryFutex>* response_futex_ = nullptr;
    std::atomic<bool>* request_started_ = nullptr;
  };

  // Creates a new client instance on a specified server id.
  // By default, the client tries to automatically connect to an existing server
  // instance and fails if it can't connect. We can set the `auto_connect`
  // argument to false to create an unconnected client instance.
  // In order to trigger an execution on the server, we have to explicitly call
  // `Connect()` before in order to establish a working connection.
  static absl::StatusOr<RemoteTriggerClient> Create(absl::string_view server_id,
                                                    bool auto_connect = true);

  // This class is move-only.
  RemoteTriggerClient(RemoteTriggerClient& other) = delete;
  RemoteTriggerClient& operator=(RemoteTriggerClient& other) = delete;
  RemoteTriggerClient(RemoteTriggerClient&& other) noexcept;
  RemoteTriggerClient& operator=(RemoteTriggerClient&& other) noexcept;

  // Returns the current server id.
  std::string ServerID() const;

  // Manually connects to the server specified during construction.
  // One must call `Connect()` explicitly if the client instance was created
  // with the `auto_connect` flag set to `false`. If the client is already
  // connected, this function returns immediately and the connection remains
  // untouched. Returns an error state if it can't connect to the server.
  absl::Status Connect();

  // Indicates whether a connection to the server_id was successfully
  // established.
  bool IsConnected() const;

  // Triggers a request on the server to execute the server's callback and
  // waits for the server to respond.
  // The `deadline` argument indicates how long we should wait for the
  // server to respond before timing out. By default, it waits forever.
  // Returns a `DeadlineExceeded` error code when timed out.
  // Returns `OkStatus` otherwise.
  RealtimeStatus Trigger(absl::Time deadline = absl::InfiniteFuture());

  // Triggers a request to execute the specified callback on the server without
  // waiting for the server's response.
  // Unlike a call to `Trigger()`, this function returns immediately. It returns
  // an `AsyncRequest` object which can later be queried about the status of the
  // request. This function is mainly used for triggering calls from multiple
  // clients without them waiting on each other.
  RealtimeStatusOr<AsyncRequest> TriggerAsync();

 private:
  explicit RemoteTriggerClient(absl::string_view server_id);

  RemoteTriggerClient(absl::string_view server_id,
                      ReadWriteMemorySegment<BinaryFutex>&& request_futex,
                      ReadOnlyMemorySegment<BinaryFutex>&& response_futex);

  std::string server_id_;
  // The interprocess signaling is done via two semaphores shared between a
  // server and its clients.
  ReadWriteMemorySegment<BinaryFutex> request_futex_;
  ReadOnlyMemorySegment<BinaryFutex> response_futex_;

  // We have to bookmark whether a request is currently active. A call to
  // `Trigger()` as well as `TriggerAsync()` starts a request. The former
  // resets the atomic before returning. `TriggerAsync` resets it on a
  // successful call to `AsyncRequest::WaitUntil` or when the `AsyncRequest`
  // object goes out of scope.
  std::atomic<bool> request_started_{false};
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_REMOTE_TRIGGER_REMOTE_TRIGGER_CLIENT_H_
