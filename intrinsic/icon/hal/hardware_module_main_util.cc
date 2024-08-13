// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/hardware_module_main_util.h"

#include <dirent.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

#include <future>  // NOLINT
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_set.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "grpc/grpc.h"
#include "grpcpp/security/server_credentials.h"
#include "grpcpp/server.h"
#include "grpcpp/server_builder.h"
#include "intrinsic/icon/hal/hardware_module_runtime.h"
#include "intrinsic/icon/hal/hardware_module_util.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/hal/realtime_clock.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/duration.h"
#include "intrinsic/icon/utils/shutdown_signals.h"
#include "intrinsic/util/proto/any.h"
#include "intrinsic/util/proto/get_text_proto.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread_options.h"
#include "intrinsic/util/thread/util.h"
namespace intrinsic::icon {

absl::StatusOr<HardwareModuleMainConfig> LoadConfig(
    absl::string_view module_config_file,
    absl::string_view runtime_context_file, bool use_realtime_scheduling) {
  if (module_config_file.empty()) {
    LOG(ERROR) << "PUBLIC: Expected --module_config_file=<path>";
    return absl::InvalidArgumentError(
        "No config file specified. Please run the execution with "
        "--module_config_file=<path>/<to>/config.pbtxt");
  }
  intrinsic_proto::icon::HardwareModuleConfig module_config;
  INTR_RETURN_IF_ERROR(
      intrinsic::GetTextProto(module_config_file, module_config));
  return HardwareModuleMainConfig{
      .module_config = module_config,
      .use_realtime_scheduling = use_realtime_scheduling};
}

absl::StatusOr<HardwareModuleRtSchedulingData> SetupRtScheduling(
    const intrinsic_proto::icon::HardwareModuleConfig& module_config,
    absl::string_view shared_memory_namespace, bool use_realtime_scheduling,
    std::optional<int> realtime_core) {
  std::unique_ptr<intrinsic::icon::RealtimeClock> realtime_clock = nullptr;
  if (module_config.drives_realtime_clock()) {
    INTR_ASSIGN_OR_RETURN(realtime_clock,
                          intrinsic::icon::RealtimeClock::Create(
                              shared_memory_namespace, module_config.name()));
  }

  absl::StatusOr<absl::flat_hash_set<int>> affinity_set =
      absl::FailedPreconditionError("Did not read Affinity set.");

  if (!module_config.realtime_cores().empty()) {
    LOG(INFO) << "Reading realtime core from proto config.";
    affinity_set =
        absl::flat_hash_set<int>{module_config.realtime_cores().begin(),
                                 module_config.realtime_cores().end()};
  } else if (realtime_core.has_value()) {
    LOG(INFO) << "Reading realtime core from flag.";
    affinity_set = absl::flat_hash_set<int>{*realtime_core};
  } else {
    LOG(INFO) << "Reading realtime core from /proc/cmdline";
    affinity_set = intrinsic::ReadCpuAffinitySetFromCommandLine();
  }

  intrinsic::ThreadOptions server_thread_options;
  if (use_realtime_scheduling) {
    LOG(INFO) << "Configuring hardware module with RT options.";
    // A realtime config without affinity set is not valid.
    INTR_RETURN_IF_ERROR(affinity_set.status());
    LOG(INFO) << "Realtime cores are: " << absl::StrJoin(*affinity_set, ", ");
    server_thread_options =
        intrinsic::ThreadOptions()
            .SetRealtimeHighPriorityAndScheduler()
            .SetAffinity({affinity_set->begin(), affinity_set->end()});
  }
  return HardwareModuleRtSchedulingData{
      std::move(realtime_clock), server_thread_options,
      affinity_set.value_or(absl::flat_hash_set<int>{})};
}

namespace {

// Simple convenience function to check if `exit_code_future` was set before
// reaching deadline.
// Returns true, if `exit_code_future` has a value set.
bool ExitCodeFutureHasValue(
    std::future<HardwareModuleExitCode>& exit_code_future,
    Clock::time_point deadline) {
  if (!exit_code_future.valid()) {
    return false;
  }
  return (exit_code_future.wait_until(deadline) == std::future_status::ready);
}

std::optional<HardwareModuleExitCode> GetExitCodeFromFuture(
    std::future<HardwareModuleExitCode>& exit_code_future,
    Clock::time_point deadline) {
  if (!ExitCodeFutureHasValue(exit_code_future, deadline)) {
    return std::nullopt;
  }
  return exit_code_future.get();
}

std::optional<HardwareModuleExitCode> GetExitCodeFromFuture(
    std::future<HardwareModuleExitCode>& exit_code_future,
    Duration timeout = Milliseconds(0)) {
  return GetExitCodeFromFuture(exit_code_future, Clock::Now() + timeout);
}

}  // namespace

std::optional<HardwareModuleExitCode>
RunRuntimeWithGrpcServerAndWaitForShutdown(
    const absl::StatusOr<HardwareModuleMainConfig>& main_config,
    absl::StatusOr<intrinsic::icon::HardwareModuleRuntime>& runtime,
    std::optional<int> cli_grpc_server_port,
    const std::vector<int>& cpu_affinity) {
  absl::Status hwm_run_error;
  grpc::ServerBuilder server_builder;
  server_builder.AddChannelArgument(GRPC_ARG_ALLOW_REUSEPORT, 0);
  server_builder.AddChannelArgument(GRPC_ARG_MAX_METADATA_SIZE,
                                    16 * 1024);  // Set to 16KB
  if (runtime.ok()) {
    QCHECK_OK(main_config.status())
        << "Runtime OK but config not OK - this is a bug";
    LOG(INFO) << "PUBLIC: Starting hardware module "
              << main_config->module_config.name();
    auto status = runtime->Run(
        server_builder, main_config->use_realtime_scheduling, cpu_affinity);
    if (!status.ok()) {
      LOG(ERROR) << "PUBLIC: Error running hardware module: "
                 << status.message();
      hwm_run_error = status;
    }
  }

  std::optional<HardwareModuleExitCode> exit_code;

  std::optional<int> grpc_server_port = std::nullopt;
  if (cli_grpc_server_port.has_value()) {
    grpc_server_port = cli_grpc_server_port;
    LOG(INFO) << "Using grpc port " << *grpc_server_port
              << " from command line";
  }

  // grpc server variable needs to live until shutdown, but must be destroyed
  // before calling HardwareModuleRuntime::Shutdown(). Create server after
  // setting init faults on HealthService, so that init faults are immediately
  // available.
  std::unique_ptr<::grpc::Server> grpc_server;
  if (grpc_server_port.has_value()) {
    std::string address = absl::StrCat("[::]:", *grpc_server_port);
    server_builder.AddListeningPort(
        address,
        ::grpc::InsecureServerCredentials()  // NOLINT (insecure)
    );

    grpc_server = server_builder.BuildAndStart();
    LOG(INFO) << "gRPC server started on port " << *grpc_server_port;
  } else {
    LOG(WARNING) << "No gRPC port provided. Will not start gRPC server.";
  }

  LOG(INFO) << "Running until receiving shutdown signal.";
  // The poll loop here is necessary because we can't call runtime->Stop()
  // from the signal handler and a future isn't signal-safe
  // either.
  const Duration kPollShutdownSignalEvery = intrinsic::Seconds(0.2);
  while (IsShutdownRequested() == ShutdownType::kNotRequested) {
    auto next_check_deadline = Clock::Now() + kPollShutdownSignalEvery;
  }
  LOG(INFO) << "Shutdown signal received";

  return exit_code;
}
}  // namespace intrinsic::icon
