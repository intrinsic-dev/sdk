// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_MAIN_UTIL_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_MAIN_UTIL_H_

#include <memory>
#include <optional>
#include <vector>

#include "absl/container/flat_hash_set.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/icon/hal/hardware_module_runtime.h"
#include "intrinsic/icon/hal/hardware_module_util.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/hal/realtime_clock.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic::icon {

// Helper struct containing configuration data the Hardware Module execution.
struct HardwareModuleMainConfig {
  // Either loaded from a proto file directly or from the runtime context.
  intrinsic_proto::icon::HardwareModuleConfig module_config;
  // Whether to use realtime scheduling for the mainloop threads and for custom
  // HWM realtime threads.
  bool use_realtime_scheduling;
};

// Loads in and updates the HardwareModuleConfig from disk.  This is expected to
// be in the resource's configuration, unless --module_config_file is specified,
// in which case we assume this is not running as a resource, but as an
// standalone hardware module.
absl::StatusOr<HardwareModuleMainConfig> LoadConfig(
    absl::string_view module_config_file,
    absl::string_view runtime_context_file, bool use_realtime_scheduling);

struct HardwareModuleRtSchedulingData {
  // Realtime clock to be used by this Hardware Module.
  std::unique_ptr<intrinsic::icon::RealtimeClock> realtime_clock;
  // Options for the realtime thread.
  intrinsic::ThreadOptions rt_thread_options;
  // CPU cores that will be used for realtime scheduling.
  absl::flat_hash_set<int> affinity_set;
};

absl::StatusOr<HardwareModuleRtSchedulingData> SetupRtScheduling(
    const intrinsic_proto::icon::HardwareModuleConfig& module_config,
    absl::string_view shared_memory_namespace, bool use_realtime_scheduling,
    std::optional<int> realtime_core, bool disable_malloc_guard);

// Runs HWM runtime and the gRPC server and waits for runtime to shutdown as
// signaled by system signals or the resource health service.
std::optional<HardwareModuleExitCode>
RunRuntimeWithGrpcServerAndWaitForShutdown(
    const absl::StatusOr<HardwareModuleMainConfig>& main_config,
    absl::StatusOr<intrinsic::icon::HardwareModuleRuntime>& runtime,
    std::optional<int> cli_grpc_server_port,
    const std::vector<int>& cpu_affinity);

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_MAIN_UTIL_H_
