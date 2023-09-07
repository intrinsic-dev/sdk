// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HARDWARE_MODULES_LOOPBACK_LOOPBACK_HARDWARE_MODULE_H_
#define INTRINSIC_ICON_HARDWARE_MODULES_LOOPBACK_LOOPBACK_HARDWARE_MODULE_H_

#include <atomic>

#include "absl/status/status.h"
#include "intrinsic/icon/control/safety/safety_messages_generated.h"
#include "intrinsic/icon/control/safety/safety_messages_utils.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/hardware_module_interface.h"
#include "intrinsic/icon/hal/interfaces/joint_command_generated.h"
#include "intrinsic/icon/hal/interfaces/joint_limits_generated.h"
#include "intrinsic/icon/hal/interfaces/joint_state_generated.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace loopback_module {

// A simple hardware module that just reports back the commanded joint
// positions. Joint velocity and acceleration status are reported as 0.
class LoopbackHardwareModule final
    : public intrinsic::icon::HardwareModuleInterface {
 public:
  explicit LoopbackHardwareModule();

  absl::Status Init(
      intrinsic::icon::HardwareInterfaceRegistry& interface_registry,
      const intrinsic::icon::ModuleConfig& config) override;

  intrinsic::icon::RealtimeStatus Activate() override;

  intrinsic::icon::RealtimeStatus Deactivate() override;

  absl::Status EnableMotion() override;

  absl::Status DisableMotion() override;

  absl::Status ClearFaults() override;

  absl::Status Shutdown() override;

  intrinsic::icon::RealtimeStatus ReadStatus() override;

  intrinsic::icon::RealtimeStatus ApplyCommand() override;

 private:
  // Number of degrees of freedom for the module, dynamically set by the
  // config provided.
  int num_dofs_;

  enum class ModuleState : uint8_t {
    kShutdown = 0,
    kInactive = 1,
    kActive = 2,
    kMotionEnabled = 3,
  };

  void RuntimeLoop();

  intrinsic::icon::RealtimeClockInterface* realtime_clock_;
  intrinsic::Thread runtime_loop_thread_;

  // HAL interface handles.
  intrinsic::icon::MutableHardwareInterfaceHandle<
      intrinsic_fbs::JointPositionState>
      joint_position_state_;
  intrinsic::icon::MutableHardwareInterfaceHandle<
      intrinsic_fbs::JointVelocityState>
      joint_velocity_state_;
  intrinsic::icon::MutableHardwareInterfaceHandle<
      intrinsic_fbs::JointAccelerationState>
      joint_acceleration_state_;
  intrinsic::icon::HardwareInterfaceHandle<intrinsic_fbs::JointPositionCommand>
      joint_position_command_;
  intrinsic::icon::MutableHardwareInterfaceHandle<intrinsic_fbs::JointLimits>
      joint_limits_;
  intrinsic::icon::MutableHardwareInterfaceHandle<
      intrinsic::safety::messages::SafetyStatusMessage>
      safety_status_;

  std::atomic<ModuleState> module_state_;
  static_assert(decltype(module_state_)::is_always_lock_free);
};

}  // namespace loopback_module

// Register the additional interfaces we use.
namespace intrinsic::icon {
namespace hardware_interface_traits {
INTRINSIC_ADD_HARDWARE_INTERFACE(safety::messages::SafetyStatusMessage,
                                 safety::messages::BuildSafetyStatusMessage,
                                 "intrinsic_fbs.SafetyStatus")
}  // namespace hardware_interface_traits
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HARDWARE_MODULES_LOOPBACK_LOOPBACK_HARDWARE_MODULE_H_
