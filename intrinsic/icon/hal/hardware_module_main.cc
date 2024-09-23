// Copyright 2023 Intrinsic Innovation LLC

#include <dirent.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

#include <csignal>
#include <future>  // NOLINT(build/c++11)
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/hal/hardware_module_main_util.h"
#include "intrinsic/icon/hal/hardware_module_registry.h"
#include "intrinsic/icon/hal/hardware_module_runtime.h"
#include "intrinsic/icon/hal/hardware_module_util.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/icon/utils/shutdown_signals.h"
#include "intrinsic/logging/data_logger_client.h"
#include "intrinsic/util/memory_lock.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, module_config_file, "",
          "Module prototext configuration file path.");
ABSL_FLAG(bool, realtime, false,
          "Indicating whether we run on a privileged RTPC.");
ABSL_FLAG(std::optional<int>, realtime_core, std::nullopt,
          "The CPU core for all realtime threads. Is read from /proc/cmdline "
          "if not defined.");
ABSL_FLAG(std::string, shared_memory_namespace_testonly, "",
          "Prefix for all shared memory connections. Passing unique namespace "
          "is needed to make integration tests hermetic.");
ABSL_FLAG(
    std::optional<int>, grpc_server_port, std::nullopt,
    "The port to use for the grpc server. Only used if not in resource mode.");

namespace intrinsic::icon {

constexpr const char* kUsageString = R"(
Usage: my_hardware_module --module_config_file=<path> [--realtime] [--realtime_core=5] [--grpc_server_port=<port>]

Starts the hardware module and runs its realtime update loop.

If --realtime is specified, the update loop runs in a thread with realtime
priority. Otherwise, it runs in a normal thread.
)";

constexpr char kLoggerAddress[] = "logger.app-intrinsic-base:8080";
static constexpr absl::Duration kLoggerConnectionTimeout = absl::Seconds(1);

absl::StatusOr<HardwareModuleExitCode> ModuleMain(int argc, char** argv) {
  // Handle SIGTERM, sent by Kubernetes to shut down.
  std::signal(SIGTERM, ShutdownSignalHandler);
  // Handle Ctrl+C to shut down.
  std::signal(SIGINT, ShutdownSignalHandler);

  if (absl::Status status =
          intrinsic::data_logger::StartUpIntrinsicLoggerViaGrpc(
              kLoggerAddress, kLoggerConnectionTimeout);
      !status.ok()) {
    LOG(WARNING) << "Failed to connect to data logger, robot metadata will not "
                    "be published. Error: "
                 << status;
  }
  std::string runtime_context_file;
  absl::StatusOr<HardwareModuleMainConfig> hwm_main_config =
      LoadConfig(absl::GetFlag(FLAGS_module_config_file), runtime_context_file,
                 absl::GetFlag(FLAGS_realtime));

  absl::StatusOr<intrinsic::icon::HardwareModuleRuntime> runtime =
      absl::FailedPreconditionError("Config not OK");
  std::promise<HardwareModuleExitCode> hwm_exit_code_promise;
  std::future<HardwareModuleExitCode> hwm_exit_code_future =
      hwm_exit_code_promise.get_future();
  std::vector<int> cpu_affinity;

  if (hwm_main_config.ok()) {
    std::string shared_memory_namespace =
        absl::GetFlag(FLAGS_shared_memory_namespace_testonly);
    LOG(INFO) << "Shared memory namespace: \'" << shared_memory_namespace
              << "\'";
    std::optional<int> realtime_core = absl::GetFlag(FLAGS_realtime_core);
    if (!hwm_main_config->module_config.has_disable_malloc_guard()) {
      hwm_main_config->module_config.set_disable_malloc_guard(false);
    }

    INTR_ASSIGN_OR_RETURN(
        auto shm_manager,
        SharedMemoryManager::Create(
            /*shared_memory_namespace=*/shared_memory_namespace,
            /*module_name=*/hwm_main_config->module_config.name()));

    INTR_ASSIGN_OR_RETURN(
        (auto [realtime_clock, server_thread_options, affinity_set]),
        intrinsic::icon::SetupRtScheduling(
            hwm_main_config->module_config, *shm_manager,
            /*use_realtime_scheduling=*/
            hwm_main_config->use_realtime_scheduling, realtime_core,
            /*disable_malloc_guard=*/
            hwm_main_config->module_config.disable_malloc_guard()));
    cpu_affinity = {affinity_set.begin(), affinity_set.end()};
    LOG(INFO) << "Creating hardware module with config:\n"
              << hwm_main_config->module_config;
    runtime = intrinsic::icon::HardwareModuleRuntime::Create(
        std::move(shm_manager),
        intrinsic::icon::hardware_module_registry::CreateInstance(
            intrinsic::icon::ModuleConfig(
                hwm_main_config->module_config, shared_memory_namespace,
                realtime_clock.get(), server_thread_options),
            std::move(realtime_clock)));
  } else {
    LOG(ERROR) << "Failed to load hardware module config: "
               << hwm_main_config.status();
  }

  std::optional<HardwareModuleExitCode> exit_code =
      RunRuntimeWithGrpcServerAndWaitForShutdown(
          hwm_main_config, runtime, absl::GetFlag(FLAGS_grpc_server_port),
          cpu_affinity);

  // Stop the runtime and shutdown fully.
  if (runtime.ok()) {
    LOG(INFO) << "PUBLIC: Stopping hardware module. Shutting down ...";
    auto status = runtime->Stop();
    if (!status.ok()) {
      // If there is no explicit exit code, we return the status. Otherwise, we
      // log the error and don't want to mess up the desired exit code.
      if (!exit_code.has_value()) {
        return status;
      } else {
        LOG(ERROR) << "PUBLIC: Failed to stop hardware module: " << status;
      }
    }
  }
  return exit_code.value_or(HardwareModuleExitCode::kNormalShutdown);
}

}  // namespace intrinsic::icon

int main(int argc, char** argv) {
  InitXfa(intrinsic::icon::kUsageString, argc, argv);
  constexpr int prefault_memory = 256 * 1024;
  QCHECK_OK((intrinsic::LockMemory<prefault_memory, prefault_memory>()));
  absl::StatusOr<intrinsic::icon::HardwareModuleExitCode> exit_code =
      (intrinsic::icon::ModuleMain(argc, argv));
  if (!exit_code.ok()) {
    LOG(ERROR) << "PUBLIC: Hardware module main failed: " << exit_code.status();
    return 1;
  }
  LOG(INFO) << "PUBLIC: Hardware module shutdown complete with code "
            << static_cast<int>(exit_code.value());
  return static_cast<int>(exit_code.value());
}
