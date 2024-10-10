// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_SERVER_GRPC_ENVELOPE_H_
#define INTRINSIC_ICON_SERVER_GRPC_ENVELOPE_H_

#include <functional>
#include <memory>
#include <optional>
#include <string>

#include "absl/base/attributes.h"
#include "absl/base/nullability.h"
#include "absl/base/thread_annotations.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/synchronization/mutex.h"
#include "absl/types/optional.h"
#include "grpcpp/channel.h"
#include "grpcpp/server.h"
#include "grpcpp/support/channel_arguments.h"
#include "intrinsic/hardware/gpio/gpio_service.grpc.pb.h"
#include "intrinsic/icon/server/icon_api_service.h"

namespace intrinsic::icon {

// Interface that wraps implementations of the ICON and GPIO services.
//
// `GrpcEnvelope` relays requests to these two services, unless there is an
// error. If there *is* an error, `GrpcEnvelope` reports that error as a
// response to any and all gRPC requests. There are two exceptions to this
// behavior:
//
// * If a client calls `IconApiService::RestartServer()`, then `GrpcEnvelope`
//   discards the `IconImplInterface` and builds a new one, effectively
//   restarting ICON.
// * If a client calls `IconApiService::ClearFaults()`
//   *while `IconImplInterface::Status()` is not `absl::OkStatus()`*, then
//   `GrpcEnvelope` also discards the `IconImplInterface` and builds a new one.
//
// (Note that in both of these cases, the gRPC call blocks until the replacement
// `IconImplInterface` is ready.)
class IconImplInterface {
 public:
  virtual ~IconImplInterface() = default;
  // Returns a reference to an ICON gRPC service. This reference must be valid
  // for the lifetime of the IconImplInterface.
  //
  // Returns an error if the IconImplInterface is in an error state.
  virtual absl::StatusOr<absl::Nonnull<icon::IconApiService*>> IconService()
      ABSL_ATTRIBUTE_LIFETIME_BOUND = 0;
  // Returns a reference to a GPIOService. This reference must be valid for the
  // lifetime of the IconImplInterface.
  //
  // Returns an error if the IconImplInterface is in an error state.
  virtual absl::StatusOr<
      absl::Nonnull<intrinsic_proto::gpio::GPIOService::Service*>>
  GpioService() ABSL_ATTRIBUTE_LIFETIME_BOUND = 0;
};

// A wrapper for the ICON, GPIO grpc services and handler for the realtime
// tracing service. They either forwards calls to the wrapped services `service`
// and `gpio_service` or responds to all calls with a global error `status`.
// Each grpc server is started when the first setter function is called.
// The purpose of this is to expose error messages longer.
class GrpcEnvelope {
 public:
  struct Config {
    // Listening address of the gRPC services that GrpcEnvelope exposes:
    // * ICON Application Layer
    // * GPIO
    // * AutoGeneratedIconConfigService (if present in config)
    //
    // If unset, GrpcEnvelope still brings up the gRPC server, but the server is
    // only accessible via GrpcEnvelope::InProcChannel()
    const std::optional<std::string> grpc_address = std::nullopt;

    // Factory function for `IconImplInterface`. GrpcEnvelope builds and
    // replaces IconImplInterface as needed at runtime (see documentation on
    // IconImplInterface for more details).
    std::function<absl::StatusOr<std::unique_ptr<IconImplInterface>>()>
        icon_impl_factory;
  };

  explicit GrpcEnvelope(Config config);

  ~GrpcEnvelope();

  // Calls "TryCancel" on gRPC streams.
  // Usually results in all sessions closing later (after this call returns),
  // but this is not guaranteed (because of service methods not finishing for
  // other reasons or new grpc requests coming in).
  void TryCancelAllStreams();

  // 'nullptr' if ICON server has not started.
  std::shared_ptr<grpc::Channel> InProcChannel(
      const grpc::ChannelArguments& channel_args);

  // Blocks until shutdown.
  void Wait();

 private:
  class WrapperService;
  class GpioWrapperService;

  void StartServer();

  absl::StatusOr<absl::Nonnull<IconApiService*>> IconService()
      ABSL_SHARED_LOCKS_REQUIRED(icon_impl_mutex_);
  absl::StatusOr<absl::Nonnull<intrinsic_proto::gpio::GPIOService::Service*>>
  GpioService() ABSL_SHARED_LOCKS_REQUIRED(icon_impl_mutex_);
  // Tears down the current IconImplInterface and uses the factory in `config_`
  // to build a new one.
  //
  // Forwards any errors from the factory, and sets `icon_impl_`, regardless of
  // whether the factory succeeded or failed.
  absl::Status RebuildIconImpl() ABSL_LOCKS_EXCLUDED(icon_impl_mutex_);

  const Config config_;

  mutable absl::Mutex icon_impl_mutex_;
  absl::StatusOr<std::unique_ptr<IconImplInterface>> icon_impl_ ABSL_GUARDED_BY(
      icon_impl_mutex_) = absl::UnavailableError("Service is not set yet");

  std::unique_ptr<WrapperService> wrapper_service_;
  std::unique_ptr<GpioWrapperService> gpio_wrapper_service_;
  std::unique_ptr<::grpc::Server> server_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_SERVER_GRPC_ENVELOPE_H_
