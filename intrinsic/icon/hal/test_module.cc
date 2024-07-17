// Copyright 2023 Intrinsic Innovation LLC

#include "absl/status/status.h"
#include "intrinsic/icon/hal/hardware_module_init_context.h"
#include "intrinsic/icon/hal/hardware_module_interface.h"
#include "intrinsic/icon/hal/hardware_module_registry.h"
#include "intrinsic/icon/utils/realtime_status.h"

// TestModule does nothing useful, but provides a target against which we can
// compile hardware_module_main.cc to ensure it builds.
class TestModule final : public ::intrinsic::icon::HardwareModuleInterface {
 public:
  explicit TestModule() = default;

  absl::Status Init(
      intrinsic::icon::HardwareModuleInitContext& init_context) override {
    return absl::OkStatus();
  }

  intrinsic::icon::RealtimeStatus Activate() override {
    return intrinsic::icon::OkStatus();
  }

  intrinsic::icon::RealtimeStatus Deactivate() override {
    return intrinsic::icon::OkStatus();
  }

  absl::Status EnableMotion() override { return absl::OkStatus(); }

  absl::Status DisableMotion() override { return absl::OkStatus(); }

  absl::Status ClearFaults() override { return absl::OkStatus(); }

  absl::Status Shutdown() override { return absl::OkStatus(); }

  intrinsic::icon::RealtimeStatus ReadStatus() override {
    return intrinsic::icon::OkStatus();
  }

  intrinsic::icon::RealtimeStatus ApplyCommand() override {
    return intrinsic::icon::OkStatus();
  }
};

REGISTER_HARDWARE_MODULE(TestModule);
