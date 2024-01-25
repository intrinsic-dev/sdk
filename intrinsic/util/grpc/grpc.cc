// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/grpc/grpc.h"

#include <atomic>
#include <chrono>  //NOLINT
#include <climits>
#include <csignal>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpcpp/grpcpp.h"
#include "intrinsic/icon/release/grpc_time_support.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/thread/thread.h"
#include "src/proto/grpc/health/v1/health.grpc.pb.h"

namespace intrinsic {

namespace {

using ::grpc::health::v1::HealthCheckRequest;
using ::grpc::health::v1::HealthCheckResponse;

// Returns OK if the server responds to a noop RPC. This ensures that the
// channel can be used for other RPCs.
absl::Status CheckChannelHealth(std::shared_ptr<::grpc::Channel> channel,
                                absl::Duration timeout) {
  // Try an arbitrary RPC (we use the Health service but could use anything that
  // responds quickly without side-effects). Use the async client because the
  // sync client doesn't seem to respect the deadline for certain channels.
  auto health_stub = grpc::health::v1::Health::NewStub(channel);

  grpc::CompletionQueue cq;
  absl::Time deadline = absl::Now() + timeout;
  grpc::ClientContext ctx;
  ctx.set_deadline(deadline);
  HealthCheckResponse resp;
  grpc::Status status;
  std::unique_ptr<grpc::ClientAsyncResponseReader<HealthCheckResponse>> rpc(
      health_stub->AsyncCheck(&ctx, HealthCheckRequest(), &cq));
  int tag = 1;
  rpc->Finish(&resp, &status, &tag);

  // Wait for the response. If it succeeds or returns "unimplemented", then we
  // know the channel is healthy.
  void* got_tag;
  bool ok = false;
  if (cq.AsyncNext(&got_tag, &ok, deadline) !=
          grpc::CompletionQueue::GOT_EVENT ||
      *static_cast<int*>(got_tag) != tag || !ok) {
    return absl::DeadlineExceededError(
        "deadline exceeded when checking channel health");
  }

  if (!status.ok() && status.error_code() != grpc::StatusCode::UNIMPLEMENTED) {
    return ToAbslStatus(status);
  }
  return absl::OkStatus();
}

}  // namespace

/**
 * Create a grpc server using the given address and the set of services provided
 */
absl::StatusOr<std::unique_ptr<::grpc::Server>> CreateServer(
    const absl::string_view address,
    const std::vector<::grpc::Service*>& services) {
  ::grpc::ServerBuilder builder;
  builder.AddListeningPort(
      std::string(address),
      ::grpc::                       // NOLINTNEXTLINE
      InsecureServerCredentials());  // NO_LINT(grpc_insecure_credential_linter)
  for (const auto& service : services) {
    builder.RegisterService(service);
  }

  std::unique_ptr<::grpc::Server> server(builder.BuildAndStart());
  if (server == nullptr) {
    return absl::InternalError("Could not start the server.");
  }

  return server;
}

absl::StatusOr<std::unique_ptr<::grpc::Server>> CreateServer(
    uint16_t listen_port, const std::vector<::grpc::Service*>& services) {
  std::string address = "0.0.0.0:" + std::to_string(listen_port);
  return CreateServer(address, services);
}

void ConfigureClientContext(::grpc::ClientContext* client_context) {
  // Disable fast failure in google3, since our code is written against the
  // (correct-in-blue) expectation that gRPC service calls will block/retry if
  // the other end isn't ready yet.
  client_context->set_fail_fast(false);
}

absl::Status WaitForChannelConnected(absl::string_view address,
                                     std::shared_ptr<::grpc::Channel> channel,
                                     absl::Time deadline) {
  if (channel->GetState(true) == GRPC_CHANNEL_READY) {
    return absl::OkStatus();
  } else {
    channel->WaitForConnected(absl::ToChronoTime(deadline));
    grpc_connectivity_state channel_state = channel->GetState(false);
    std::string channel_state_string;
    switch (channel_state) {
      case GRPC_CHANNEL_READY:
        return absl::OkStatus();
      case GRPC_CHANNEL_IDLE:
        channel_state_string = "GRPC_CHANNEL_IDLE";
        break;
      case GRPC_CHANNEL_CONNECTING:
        channel_state_string = "GRPC_CHANNEL_CONNECTING";
        break;
      case GRPC_CHANNEL_TRANSIENT_FAILURE:
        channel_state_string = "GRPC_CHANNEL_TRANSIENT_FAILURE";
        break;
      case GRPC_CHANNEL_SHUTDOWN:
        channel_state_string = "GRPC_CHANNEL_SHUTDOWN";
        break;
    }
    return absl::UnavailableError(absl::StrCat("gRPC channel to ", address,
                                               " is unavailable.  State is ",
                                               channel_state_string));
  }
}

::grpc::ChannelArguments DefaultGrpcChannelArgs() {
  ::grpc::ChannelArguments channel_args;
  channel_args.SetInt("grpc.testing.fixed_reconnect_backoff_ms", 1000);
  channel_args.SetInt(GRPC_ARG_MAX_RECONNECT_BACKOFF_MS, 1000);

  // Disable gRPC client-side keepalive. This is a temporary fix, as
  // //third_party/blue targets depend on //net/grpc but they do not call
  // InitGoogle(). These targets should either use //third_party/grpc instead,
  // or call InitGoogle().
  channel_args.SetInt(GRPC_ARG_KEEPALIVE_TIME_MS, INT_MAX);
  channel_args.SetInt(GRPC_ARG_KEEPALIVE_TIMEOUT_MS, 20000);
  channel_args.SetInt(GRPC_ARG_KEEPALIVE_PERMIT_WITHOUT_CALLS, 0);

  // Increase metadata size, this includes, for example, the size of the
  // information gathered from an absl::Status on error. Default is 8KB.
  channel_args.SetInt(GRPC_ARG_MAX_METADATA_SIZE, 16 * 1024);

  // Disable DNS resolution for service config. These calls can impact
  // performance negatively on some DNS servers (i.e. Vodafone LTE on-site in
  // Europe).
  channel_args.SetInt(GRPC_ARG_SERVICE_CONFIG_DISABLE_RESOLUTION, 1);
  return channel_args;
}

::grpc::ChannelArguments UnlimitedMessageSizeGrpcChannelArgs() {
  ::grpc::ChannelArguments channel_args = DefaultGrpcChannelArgs();
  channel_args.SetMaxReceiveMessageSize(-1);
  channel_args.SetMaxSendMessageSize(-1);
  return channel_args;
}

absl::StatusOr<std::shared_ptr<::grpc::Channel>> CreateClientChannel(
    const absl::string_view address, absl::Time deadline,
    const ::grpc::ChannelArguments& channel_args,
    bool use_default_application_credentials) {
  LOG(INFO) << "Connecting to " << address;
  absl::Status status =
      absl::DeadlineExceededError("Deadline in past in CreateClientChannel");
  while (absl::Now() < deadline) {
    std::shared_ptr<::grpc::Channel> channel;
    if (use_default_application_credentials) {
      channel = ::grpc::CreateCustomChannel(
          std::string(address), grpc::GoogleDefaultCredentials(), channel_args);
    } else {
      channel = ::grpc::CreateCustomChannel(
          std::string(address),
          ::grpc::                       // NOLINTNEXTLINE
          InsecureChannelCredentials(),  // NO_LINT(grpc_insecure_credential_linter)
          channel_args);
    }

    status = WaitForChannelConnected(address, channel, deadline);
    if (!status.ok()) continue;

    // CheckChannelHealth does not work when using application default
    // credentials. It returns "UNKNOWN: Received http2 header with status:
    // 302".
    if (!use_default_application_credentials) {
      // For some reason, WaitForChannelConnected can return "ok" even when the
      // server is not yet running. When checking for this case,
      // use a short timeout to allow time to retry after.
      status = CheckChannelHealth(channel, /*timeout=*/absl::Seconds(1));
      if (!status.ok()) {
        LOG(ERROR) << "Unhealthy channel: " << status;
        continue;
      }
    }

    LOG(INFO) << "Successfully connected to " << address;
    return channel;
  }

  return status;
}

ShutdownParams ShutdownParams::Aggressive() {
  return {.health_grace_duration = absl::ZeroDuration(),
          .shutdown_timeout = absl::Milliseconds(250)};
}

absl::Status RegisterSignalHandlerAndWait(
    grpc::Server* server, const ShutdownParams& params,
    absl::Notification& handlers_registered) {
  // User-provided signal handler needs to satisfy some constraints.
  // Effectively:
  // - access to atomics should be lock-free (std::atomic_flag is guaranteed to
  //   be lock-free by the standard).
  // - objects referred should have the lifetime of the process (hence, the use
  //   of `static`).
  //
  // See cpp reference for more details:
  // https://en.cppreference.com/w/cpp/utility/program/signal
  static std::atomic_flag shutdown_requested = ATOMIC_FLAG_INIT;

  auto prev_signal_handler = std::signal(SIGTERM, [](int) {
    // async-signal-safe implementation
    // for details, see here:
    // https://man7.org/linux/man-pages/man7/signal-safety.7.html
    // Note: To prevent undefined behavior, do not do any logging (unless using
    //   async-safe write) or else here without making sure that the function is
    //   async-signal-safe.

    // Ignores the returned value of `test_and_set` method.
    (void)shutdown_requested.test_and_set();
    shutdown_requested.notify_all();
  });
  if (prev_signal_handler == SIG_ERR) {
    return absl::InternalError("SIGTERM handler registration failed.");
  } else if (prev_signal_handler != nullptr) {
    LOG(WARNING) << absl::StrFormat(
        "Previously registered SIGTERM handler with address %p was "
        "overwritten.",
        prev_signal_handler);
  }

  handlers_registered.Notify();

  bool stop_shutdown_thread = false;
  intrinsic::Thread shutdown([&]() {
    constexpr bool kOldValue = false;
    shutdown_requested.wait(kOldValue);

    if (stop_shutdown_thread) {
      return;
    }

    if (server->GetHealthCheckService()) {
      server->GetHealthCheckService()->SetServingStatus(false);
      absl::SleepFor(params.health_grace_duration);
    }
    server->Shutdown(absl::Now() + params.shutdown_timeout);
  });

  server->Wait();

  // Makes the shutdown thread exit if the grpc server shut down due to
  // something other than SIGTERM.
  if (!shutdown_requested.test()) {
    stop_shutdown_thread = true;
    // Sets the flag to wake up the shutdown thread.
    (void)shutdown_requested.test_and_set();
    shutdown_requested.notify_all();
  }

  shutdown.Join();
  return absl::OkStatus();
}

}  // namespace intrinsic
