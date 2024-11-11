// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/server/grpc_envelope.h"

#include <signal.h>

#include <cstdlib>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/base/nullability.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpc/grpc.h"
#include "grpcpp/channel.h"
#include "grpcpp/security/server_credentials.h"
#include "grpcpp/server.h"
#include "grpcpp/server_builder.h"
#include "grpcpp/server_context.h"
#include "grpcpp/support/channel_arguments.h"
#include "grpcpp/support/server_interceptor.h"
#include "grpcpp/support/status.h"
#include "grpcpp/support/sync_stream.h"
#include "intrinsic/hardware/gpio/gpio_service.grpc.pb.h"
#include "intrinsic/hardware/gpio/gpio_service.pb.h"
#include "intrinsic/icon/proto/service.grpc.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/server/icon_api_service.h"
#include "intrinsic/icon/utils/exit_code.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/status/status_macros_grpc.h"
#include "intrinsic/util/thread/stop_token.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {

constexpr absl::Duration kServerRestartMutexTimeout = absl::Seconds(30);

class GrpcEnvelope::WrapperService : public intrinsic::icon::IconApiService {
 public:
  explicit WrapperService(GrpcEnvelope& envelope) : envelope_(envelope) {}

  ::grpc::Status GetActionSignatureByName(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetActionSignatureByNameRequest* request,
      intrinsic_proto::icon::GetActionSignatureByNameResponse* response)
      override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetActionSignatureByName(context, request, response);
  }

  ::grpc::Status GetConfig(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetConfigRequest* request,
      intrinsic_proto::icon::GetConfigResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetConfig(context, request, response);
  }

  ::grpc::Status GetStatus(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetStatusRequest* request,
      intrinsic_proto::icon::GetStatusResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetStatus(context, request, response);
  }

  ::grpc::Status IsActionCompatible(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::IsActionCompatibleRequest* request,
      intrinsic_proto::icon::IsActionCompatibleResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->IsActionCompatible(context, request, response);
  }

  ::grpc::Status ListActionSignatures(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::ListActionSignaturesRequest* request,
      intrinsic_proto::icon::ListActionSignaturesResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->ListActionSignatures(context, request, response);
  }

  ::grpc::Status ListCompatibleParts(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::ListCompatiblePartsRequest* request,
      intrinsic_proto::icon::ListCompatiblePartsResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->ListCompatibleParts(context, request, response);
  }

  ::grpc::Status ListParts(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::ListPartsRequest* request,
      intrinsic_proto::icon::ListPartsResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->ListParts(context, request, response);
  }

  ::grpc::Status OpenSession(
      ::grpc::ServerContext* context,
      ::grpc::ServerReaderWriter<intrinsic_proto::icon::OpenSessionResponse,
                                 intrinsic_proto::icon::OpenSessionRequest>*
          stream) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->OpenSession(context, stream);
  }

  ::grpc::Status WatchReactions(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::WatchReactionsRequest* request,
      ::grpc::ServerWriter<intrinsic_proto::icon::WatchReactionsResponse>*
          writer) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->WatchReactions(context, request, writer);
  }

  ::grpc::Status OpenWriteStream(
      ::grpc::ServerContext* context,
      ::grpc::ServerReaderWriter<intrinsic_proto::icon::OpenWriteStreamResponse,
                                 intrinsic_proto::icon::OpenWriteStreamRequest>*
          stream) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->OpenWriteStream(context, stream);
  }

  ::grpc::Status GetLatestStreamingOutput(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetLatestStreamingOutputRequest* request,
      intrinsic_proto::icon::GetLatestStreamingOutputResponse* response)
      override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetLatestStreamingOutput(context, request, response);
  }

  ::grpc::Status GetPlannedTrajectory(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetPlannedTrajectoryRequest* request,
      ::grpc::ServerWriter<intrinsic_proto::icon::GetPlannedTrajectoryResponse>*
          stream) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetPlannedTrajectory(context, request, stream);
  }

  ::grpc::Status Enable(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::EnableRequest* request,
      intrinsic_proto::icon::EnableResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->Enable(context, request, response);
  }

  ::grpc::Status Disable(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::DisableRequest* request,
      intrinsic_proto::icon::DisableResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->Disable(context, request, response);
  }

  ::grpc::Status ClearFaults(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::ClearFaultsRequest* request,
      intrinsic_proto::icon::ClearFaultsResponse* response) override {
    absl::Status error = absl::OkStatus();
    {
      absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
      error = envelope_.IconService().status();
    }
    // If we are latching an error, then attempt to restart the server.
    if (!error.ok()) {
      LOG(INFO) << "Got ClearFault call while in fatal fault, restarting...";
      return ToGrpcStatus(envelope_.RebuildIconImpl());
    }
    // Otherwise, clear ICON faults.
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->ClearFaults(context, request, response);
  }

  ::grpc::Status GetOperationalStatus(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetOperationalStatusRequest* request,
      intrinsic_proto::icon::GetOperationalStatusResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    absl::StatusOr<absl::Nonnull<IconApiService*>> icon_service =
        envelope_.IconService();
    if (!icon_service.ok()) {
      response->mutable_operational_status()->set_state(
          intrinsic_proto::icon::OperationalState::FAULTED);
      response->mutable_operational_status()->set_fault_reason(
          icon_service.status().ToString());
      return ToGrpcStatus(absl::OkStatus());
    }
    return icon_service.value()->GetOperationalStatus(context, request,
                                                      response);
  }

  ::grpc::Status RestartServer(::grpc::ServerContext* context,
                               const google::protobuf::Empty* request,
                               google::protobuf::Empty* response) override {
    LOG(WARNING) << "PUBLIC: Received restart request, will close connections "
                    "and quit when sessions have closed.";
    return ToGrpcStatus(envelope_.RebuildIconImpl());
  }

  ::grpc::Status SetSpeedOverride(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::SetSpeedOverrideRequest* request,
      intrinsic_proto::icon::SetSpeedOverrideResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->SetSpeedOverride(context, request, response);
  }

  ::grpc::Status GetSpeedOverride(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetSpeedOverrideRequest* request,
      intrinsic_proto::icon::GetSpeedOverrideResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetSpeedOverride(context, request, response);
  }

  ::grpc::Status SetLoggingMode(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::SetLoggingModeRequest* request,
      intrinsic_proto::icon::SetLoggingModeResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->SetLoggingMode(context, request, response);
  }

  ::grpc::Status GetLoggingMode(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetLoggingModeRequest* request,
      intrinsic_proto::icon::GetLoggingModeResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetLoggingMode(context, request, response);
  }

  ::grpc::Status GetPartProperties(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetPartPropertiesRequest* request,
      intrinsic_proto::icon::GetPartPropertiesResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetPartProperties(context, request, response);
  }

  ::grpc::Status SetPartProperties(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::SetPartPropertiesRequest* request,
      intrinsic_proto::icon::SetPartPropertiesResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->SetPartProperties(context, request, response);
  }

  ::grpc::Status SetPayload(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::SetPayloadRequest* request,
      intrinsic_proto::icon::SetPayloadResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->SetPayload(context, request, response);
  }

  ::grpc::Status GetPayload(
      ::grpc::ServerContext* context,
      const intrinsic_proto::icon::GetPayloadRequest* request,
      intrinsic_proto::icon::GetPayloadResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(IconApiService * icon_service,
                               envelope_.IconService());
    return icon_service->GetPayload(context, request, response);
  }

 private:
  GrpcEnvelope& envelope_;
};

class GrpcEnvelope::GpioWrapperService
    : public intrinsic_proto::gpio::GPIOService::Service {
 public:
  explicit GpioWrapperService(GrpcEnvelope& envelope) : envelope_(envelope) {}

  ::grpc::Status GetSignalDescriptions(
      ::grpc::ServerContext* context,
      const intrinsic_proto::gpio::GetSignalDescriptionsRequest* request,
      intrinsic_proto::gpio::GetSignalDescriptionsResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(
        intrinsic_proto::gpio::GPIOService::Service * gpio_service,
        envelope_.GpioService());
    return gpio_service->GetSignalDescriptions(context, request, response);
  }

  ::grpc::Status ReadSignals(
      ::grpc::ServerContext* context,
      const intrinsic_proto::gpio::ReadSignalsRequest* request,
      intrinsic_proto::gpio::ReadSignalsResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(
        intrinsic_proto::gpio::GPIOService::Service * gpio_service,
        envelope_.GpioService());
    return gpio_service->ReadSignals(context, request, response);
  }

  ::grpc::Status WaitForValue(
      ::grpc::ServerContext* context,
      const intrinsic_proto::gpio::WaitForValueRequest* request,
      intrinsic_proto::gpio::WaitForValueResponse* response) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(
        intrinsic_proto::gpio::GPIOService::Service * gpio_service,
        envelope_.GpioService());
    return gpio_service->WaitForValue(context, request, response);
  }

  ::grpc::Status OpenWriteSession(
      ::grpc::ServerContext* context,
      ::grpc::ServerReaderWriter<
          intrinsic_proto::gpio::OpenWriteSessionResponse,
          intrinsic_proto::gpio::OpenWriteSessionRequest>* stream) override {
    absl::ReaderMutexLock l(&envelope_.icon_impl_mutex_);
    INTR_ASSIGN_OR_RETURN_GRPC(
        intrinsic_proto::gpio::GPIOService::Service * gpio_service,
        envelope_.GpioService());
    return gpio_service->OpenWriteSession(context, stream);
  }

 private:
  GrpcEnvelope& envelope_;
};

GrpcEnvelope::GrpcEnvelope(GrpcEnvelope::Config config)
    : config_(std::move(config)) {
  if (config_.icon_impl_factory) {
    absl::MutexLock l(&icon_impl_mutex_);
    icon_impl_ = config_.icon_impl_factory();
  }
  StartServer();
}

GrpcEnvelope::~GrpcEnvelope() {
  if (server_) {
    server_->Shutdown();
  }
  // `icon_impl_` gets destroyed implicitly after this destructor
  // returns.
  // Note: It's important for the order to be correct here:
  // 1. Shut down the gRPC server to prevent any new requests from coming in and
  //    wrap up in-flight ones.
  // 2. Now that there's no more gRPC requests using it, destroy `icon_impl_`.
}

absl::StatusOr<absl::Nonnull<IconApiService*>> GrpcEnvelope::IconService() {
  INTR_RETURN_IF_ERROR(icon_impl_.status());
  return icon_impl_.value()->IconService();
}

absl::StatusOr<absl::Nonnull<intrinsic_proto::gpio::GPIOService::Service*>>
GrpcEnvelope::GpioService() {
  INTR_RETURN_IF_ERROR(icon_impl_.status());
  return icon_impl_.value()->GpioService();
}

absl::Status GrpcEnvelope::RebuildIconImpl() {
  TryCancelAllStreams();
  // There is no method to wait with a timeout on a locked Mutex, only on a
  // condition *protected by* a Mutex.
  // So, we bring out the big guns: This thread is a "time bomb" that kills the
  // entire process if we don't disarm it (by calling `RequestStop()`) before
  // the deadline.
  intrinsic::Thread kill_if_mutex_is_blocked_thread{
      [](const intrinsic::StopToken& stop_token,
         absl::Time mutex_block_deadline) {
        while (absl::Now() < mutex_block_deadline) {
          if (stop_token.stop_requested()) {
            return;
          }
          absl::SleepFor(absl::Milliseconds(100));
        }
        // If this thread wasn't "disarmed" by requesting a stop, then the
        // MutexLock below is blocking execution. Assume the worst and kill the
        // ICON process.
        std::exit(static_cast<int>(ExitCode::kFatalFaultDuringExec));
      },
      absl::Now() + kServerRestartMutexTimeout};

  // This should block until all current requests have released their locks.
  // Because we called TryCancelAllStreams(), that should happen eventually. If
  // it doesn't, then `kill_if_mutex_is_blocked_thread` stops the server
  // process.
  absl::MutexLock l(&icon_impl_mutex_);
  // Got the mutex, time to disarm our time bomb.
  kill_if_mutex_is_blocked_thread.RequestStop();
  kill_if_mutex_is_blocked_thread.Join();
  // First destroy the old ICON implementation (to make sure old and new don't
  // overlap).
  icon_impl_ = absl::UnavailableError("Restarting ICON service...");
  // Then use the factory to create a new ICON implementation.
  if (!config_.icon_impl_factory) {
    return absl::InternalError(
        "Missing ICON factory, please report this as a bug");
  }
  icon_impl_ = config_.icon_impl_factory();
  // If the factory returned an error, we want to forward that.
  return icon_impl_.status();
}

void GrpcEnvelope::TryCancelAllStreams() {
  absl::ReaderMutexLock l(&icon_impl_mutex_);
  auto icon_service = IconService();
  if (icon_service.ok()) {
    icon_service.value()->TryCancel();
  }
}

void GrpcEnvelope::StartServer() {
  INTRINSIC_ASSERT_NON_REALTIME();
  wrapper_service_ = std::make_unique<WrapperService>(*this);
  gpio_wrapper_service_ = std::make_unique<GpioWrapperService>(*this);
  grpc::ServerBuilder builder;
  if (config_.grpc_address.has_value()) {
    builder.AddListeningPort(
        config_.grpc_address.value(),
        ::grpc::InsecureServerCredentials()  // NOLINT (insecure)
    );
  }
  // Set the max message receive size to 512MB to allow longer trajectories.
  // Please check with the motion team before changing the value (see
  // b/275280379).
  builder.SetMaxReceiveMessageSize((512 * 1024 * 1024));
  builder.AddChannelArgument(GRPC_ARG_ALLOW_REUSEPORT, 0);
  // Set to 16KB
  builder.AddChannelArgument(GRPC_ARG_MAX_METADATA_SIZE, 16 * 1024);
  builder.RegisterService(wrapper_service_.get());
  builder.RegisterService(gpio_wrapper_service_.get());
  std::string server_description = "In-Process ICON Server";
  if (config_.grpc_address) {
    server_description =
        absl::StrCat("ICON Server listening on ", *config_.grpc_address);
  }
  server_ = builder.BuildAndStart();
  if (!server_) {
    LOG(FATAL) << "Failed to start " << server_description;
  }
  LOG(INFO) << "Started " << server_description;
}

std::shared_ptr<grpc::Channel> GrpcEnvelope::InProcChannel(
    const grpc::ChannelArguments& channel_args) {
  if (!server_) {
    return nullptr;
  }
  return server_->InProcessChannel(channel_args);
}

void GrpcEnvelope::Wait() {
  if (server_ == nullptr) {
    return;
  }
  server_->Wait();
}

}  // namespace intrinsic::icon
