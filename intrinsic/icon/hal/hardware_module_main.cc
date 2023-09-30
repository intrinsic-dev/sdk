// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include <signal.h>
#include <sys/mman.h>

#include <memory>
#include <optional>
#include <string>
#include <utility>

#include "absl/container/flat_hash_set.h"
#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_join.h"
#include "intrinsic/icon/control/realtime_clock_interface.h"
#include "intrinsic/icon/hal/hardware_module_registry.h"
#include "intrinsic/icon/hal/hardware_module_runtime.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/hal/realtime_clock.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/memory_lock.h"
#include "intrinsic/util/proto/any.h"
#include "intrinsic/util/proto/get_text_proto.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/util.h"

ABSL_FLAG(std::string, module_config_file, "",
          "Module prototext configuration file path.");
ABSL_FLAG(bool, realtime, false,
          "Indicating whether we run on a privileged RTPC.");

ABSL_FLAG(std::optional<int>, realtime_core, std::nullopt,
          "The CPU core for all realtime threads. Is read from /proc/cmdline "
          "if not defined.");

namespace {

constexpr const char* kUsageString = R"(
Usage: my_hardware_module --module_config_file=<path> [--realtime] [--realtime_core=5]

Starts the hardware module and runs its realtime update loop.

If --realtime is specified, the update loop runs in a thread with realtime
priority. Otherwise, it runs in a normal thread.
)";

// Loads in and updates the HardwareModuleConfig from disk.  This is expected to
// be in the resource's configuration, unless --module_config_file is specified,
// in which case we assume this is not running as a resource, but as an original
// hardware module.
absl::StatusOr<intrinsic_proto::icon::HardwareModuleConfig> LoadConfig() {
  const std::string module_config_file =
      absl::GetFlag(FLAGS_module_config_file);
  if (module_config_file.empty()) {
    LOG(ERROR) << "PUBLIC: Expected --module_config_file=<path>";
    return absl::InvalidArgumentError(
        "No config file specified. Please run the execution with "
        "--module_config_file=<path>/<to>/config.pbtxt");
  }
  LOG(INFO) << "Not running as a resource.  Loading textproto from "
            << module_config_file;
  intrinsic_proto::icon::HardwareModuleConfig module_config;
  INTRINSIC_RETURN_IF_ERROR(
      intrinsic::GetTextProto(module_config_file, module_config));
  return module_config;
}

absl::Status ModuleMain() {
  sigset_t sigset;
  sigemptyset(&sigset);
  sigaddset(&sigset, SIGINT);
  sigaddset(&sigset, SIGTERM);
  pthread_sigmask(SIG_BLOCK, &sigset, nullptr);

  INTRINSIC_ASSIGN_OR_RETURN(const auto module_config, LoadConfig());
  LOG(INFO) << "Starting hardware module with config:\n" << module_config;

  std::unique_ptr<intrinsic::icon::RealtimeClock> realtime_clock = nullptr;
  if (module_config.drives_realtime_clock()) {
    INTRINSIC_ASSIGN_OR_RETURN(
        realtime_clock,
        intrinsic::icon::RealtimeClock::Create(module_config.name()));
  }

  std::optional<int> realtime_core = absl::GetFlag(FLAGS_realtime_core);
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

  intrinsic::Thread::Options server_thread_options;
  if (absl::GetFlag(FLAGS_realtime)) {
    LOG(INFO) << "Configuring hardware module with RT options.";
    // A realtime config without affinity set is not valid.
    INTRINSIC_RETURN_IF_ERROR(affinity_set.status());
    LOG(INFO) << "Realtime cores are: " << absl::StrJoin(*affinity_set, ", ");
    server_thread_options =
        intrinsic::Thread::Options()
            .SetRealtimeHighPriorityAndScheduler()
            .SetAffinity({affinity_set->begin(), affinity_set->end()});
  }

  intrinsic::icon::RealtimeClockInterface* realtime_clock_ptr =
      realtime_clock.get();
  INTRINSIC_ASSIGN_OR_RETURN(
      auto runtime,
      intrinsic::icon::HardwareModuleRuntime::Create(
          intrinsic::icon::hardware_module_registry::CreateInstance(
              intrinsic::icon::ModuleConfig(module_config, realtime_clock_ptr,
                                            server_thread_options),
              std::move(realtime_clock))));

  LOG(INFO) << "PUBLIC: Starting hardware module " << module_config.name();

  // Both an empty affinity set and a populated one are valid for non-realtime.
  if (!affinity_set.status().ok()) {
    LOG(INFO) << "Using empty affinity set for runtime.";
    affinity_set = absl::flat_hash_set<int>{};
  }
  auto status = runtime.Run(absl::GetFlag(FLAGS_realtime),
                            {affinity_set->begin(), affinity_set->end()});
  if (!status.ok()) {
    LOG(ERROR) << "PUBLIC: Error running hardware module: " << status.message();
  }

  int signal = 0;
  sigwait(&sigset, &signal);
  LOG(INFO) << "Received signal " << signal;

  INTRINSIC_RETURN_IF_ERROR(runtime.Stop());
  LOG(INFO) << "PUBLIC: Stopping hardware module. Shutting down ...";

  return absl::OkStatus();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(kUsageString, argc, argv);
  constexpr int prefault_memory = 256 * 1024;
  QCHECK_OK((intrinsic::LockMemory<prefault_memory, prefault_memory>()));
  QCHECK_OK(ModuleMain());
  return 0;
}
