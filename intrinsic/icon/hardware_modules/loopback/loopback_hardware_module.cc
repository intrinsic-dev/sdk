// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hardware_modules/loopback/loopback_hardware_module.h"

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_format.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/control/safety/extern/safety_status.fbs.h"
#include "intrinsic/icon/control/safety/safety_messages.fbs.h"
#include "intrinsic/icon/hal/command_validator.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/hardware_module_init_context.h"
#include "intrinsic/icon/hal/hardware_module_registry.h"
#include "intrinsic/icon/hal/interfaces/joint_command.fbs.h"
#include "intrinsic/icon/hal/interfaces/joint_command_utils.h"
#include "intrinsic/icon/hal/interfaces/joint_state.fbs.h"
#include "intrinsic/icon/hal/interfaces/joint_state_utils.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/hardware_modules/loopback/loopback_config.pb.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/duration.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

namespace loopback_module {

using ::intrinsic::icon::OkStatus;
using ::intrinsic::icon::RealtimeStatus;
using ::intrinsic::icon::Validator;
using ::intrinsic::safety::messages::ButtonStatus;
using ::intrinsic::safety::messages::ModeOfSafeOperation;
using ::intrinsic::safety::messages::RequestedBehavior;
using ::intrinsic::safety::messages::SafetyStatusMessage;
using ::intrinsic_fbs::JointAccelerationState;
using ::intrinsic_fbs::JointPositionCommand;
using ::intrinsic_fbs::JointPositionState;
using ::intrinsic_fbs::JointVelocityState;

void LoopbackHardwareModule::RuntimeLoop() {
  static const intrinsic::Duration roundtrip = intrinsic::Milliseconds(1);
  LOG(ERROR) << "Entering runtime loop";
  while (module_state_ != ModuleState::kShutdown) {
    auto cycle_start_time = intrinsic::Clock::Now();
    if (module_state_ == ModuleState::kActive ||
        module_state_ == ModuleState::kMotionEnabled) {
      if (auto ret = realtime_clock_->TickBlockingWithTimeout(
              cycle_start_time, absl::InfiniteDuration());
          !ret.ok()) {
        LOG_EVERY_N_SEC(ERROR, 1)
            << "TickBlocking returned an error: " << ret.message();
        if (const auto reset_status =
                realtime_clock_->Reset(absl::InfiniteDuration());
            !reset_status.ok()) {
          LOG_EVERY_N_SEC(ERROR, 1)
              << "Failed to reset clock: " << reset_status.message();
        }
      }
    }

    intrinsic::Duration tick_duration =
        intrinsic::Clock::Now() - cycle_start_time;
    absl::SleepFor(absl::Nanoseconds(
        intrinsic::ToInt64Nanoseconds(roundtrip - tick_duration)));
  }
  LOG(ERROR) << "Finishing runtime loop.";
}

LoopbackHardwareModule::LoopbackHardwareModule() = default;

absl::Status LoopbackHardwareModule::Init(
    intrinsic::icon::HardwareModuleInitContext& init_context) {
  INTRINSIC_ASSERT_NON_REALTIME();
  intrinsic::icon::HardwareInterfaceRegistry& interface_registry =
      init_context.GetInterfaceRegistry();
  const intrinsic::icon::ModuleConfig& config = init_context.GetModuleConfig();
  INTR_ASSIGN_OR_RETURN(
      const auto loopback_config,
      config.GetConfig<::intrinsic_proto::icon::LoopbackConfig>());

  // Default to 6 dof if not specified otherwise.
  num_dofs_ = loopback_config.has_num_dof() ? loopback_config.num_dof() : 6;
  LOG(INFO) << "Configuring loopback module for " << num_dofs_ << " DOF";

  INTR_ASSIGN_OR_RETURN(
      joint_position_command_,
      interface_registry.AdvertiseInterface<JointPositionCommand>(
          "joint_position_command", num_dofs_));
  INTR_ASSIGN_OR_RETURN(
      joint_position_state_,
      interface_registry.AdvertiseMutableInterface<JointPositionState>(
          "joint_position_state", num_dofs_));
  INTR_ASSIGN_OR_RETURN(
      joint_velocity_state_,
      interface_registry.AdvertiseMutableInterface<JointVelocityState>(
          "joint_velocity_state", num_dofs_));
  INTR_ASSIGN_OR_RETURN(
      joint_acceleration_state_,
      interface_registry.AdvertiseMutableInterface<JointAccelerationState>(
          "joint_acceleration_state", num_dofs_));

  INTR_ASSIGN_OR_RETURN(
      safety_status_,
      interface_registry.AdvertiseMutableInterface<SafetyStatusMessage>(
          "safety_status",
          /*mode_of_safe_operation=*/ModeOfSafeOperation::AUTOMATIC,
          /*estop_button_status=*/ButtonStatus::UNKNOWN,
          /*enable_button_status=*/ButtonStatus::UNKNOWN,
          /*requested_behavior=*/RequestedBehavior::UNKNOWN));

  INTR_ASSIGN_OR_RETURN(command_validator_,
                        Validator::Create(interface_registry));

  module_state_ = ModuleState::kInactive;

  realtime_clock_ = config.GetRealtimeClock();
  if (realtime_clock_ == nullptr) {
    LOG(INFO) << "ICON is driving the loopback hardware module clock.";
  } else {
    LOG(INFO) << "The loopback hardware module is driving ICON's clock.";
    intrinsic::ThreadOptions thread_options = config.GetIconThreadOptions();
    thread_options.SetName("LoopbackHardwareModuleThread");

    absl::Notification runtime_loop_running;
    INTR_RETURN_IF_ERROR(runtime_loop_thread_.Start(
        thread_options, [this, &runtime_loop_running]() {
          runtime_loop_running.Notify();
          RuntimeLoop();
        }));
    // Wait until the thread is running.
    if (!runtime_loop_running.WaitForNotificationWithTimeout(
            absl::Seconds(1))) {
      return absl::DeadlineExceededError(absl::StrFormat(
          "Timeout after %s starting the Loopback communication thread.",
          absl::FormatDuration(absl::Seconds(1))));
    }
  }

  return absl::OkStatus();
}

RealtimeStatus LoopbackHardwareModule::Activate() {
  LOG(INFO) << "Activating loopback hardware module";
  module_state_ = ModuleState::kActive;
  return OkStatus();
}

RealtimeStatus LoopbackHardwareModule::Deactivate() {
  LOG(INFO) << "Deactivating loopback hardware module";
  module_state_ = ModuleState::kInactive;
  return OkStatus();
}

absl::Status LoopbackHardwareModule::EnableMotion() {
  LOG(INFO) << "Enabling motion on loopback hardware module";
  module_state_ = ModuleState::kMotionEnabled;
  return absl::OkStatus();
}

absl::Status LoopbackHardwareModule::DisableMotion() {
  LOG(INFO) << "Disabling motion on loopback hardware module";
  module_state_ = ModuleState::kActive;
  return absl::OkStatus();
}

absl::Status LoopbackHardwareModule::ClearFaults() {
  LOG(INFO) << "Clearing faults on loopback hardware module";
  module_state_ = ModuleState::kActive;
  return absl::OkStatus();
}

absl::Status LoopbackHardwareModule::Shutdown() {
  module_state_ = ModuleState::kShutdown;
  if (runtime_loop_thread_.Joinable()) {
    runtime_loop_thread_.Join();
  }
  return absl::OkStatus();
}

RealtimeStatus LoopbackHardwareModule::ApplyCommand() {
  INTRINSIC_RT_RETURN_IF_ERROR(
      command_validator_.WasUpdatedThisCycle(joint_position_command_));
  for (int i = 0; i < num_dofs_; ++i) {
    joint_position_state_->mutable_position()->Mutate(
        i, joint_position_command_->position()->Get(i));
    joint_velocity_state_->mutable_velocity()->Mutate(i, 0.0);
    joint_acceleration_state_->mutable_acceleration()->Mutate(i, 0.0);
  }
  return OkStatus();
}

RealtimeStatus LoopbackHardwareModule::ReadStatus() {
  // NO-OP, Status is updated already through `ApplyCommand`.
  return OkStatus();
}

}  // namespace loopback_module

// Register the interfaces we use.
namespace intrinsic::icon {
namespace hardware_interface_traits {
INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointPositionCommand,
                                 intrinsic_fbs::BuildJointPositionCommand,
                                 "intrinsic_fbs.JointPositionCommand")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointVelocityCommand,
                                 intrinsic_fbs::BuildJointVelocityCommand,
                                 "intrinsic_fbs.JointVelocityCommand")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointTorqueCommand,
                                 intrinsic_fbs::BuildJointTorqueCommand,
                                 "intrinsic_fbs.JointTorqueCommand")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointPositionState,
                                 intrinsic_fbs::BuildJointPositionState,
                                 "intrinsic_fbs.JointPositionState")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointVelocityState,
                                 intrinsic_fbs::BuildJointVelocityState,
                                 "intrinsic_fbs.JointVelocityState")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointAccelerationState,
                                 intrinsic_fbs::BuildJointAccelerationState,
                                 "intrinsic_fbs.JointAccelerationState")

INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::JointTorqueState,
                                 intrinsic_fbs::BuildJointTorqueState,
                                 "intrinsic_fbs.JointTorqueState")

}  // namespace hardware_interface_traits
}  // namespace intrinsic::icon

REGISTER_HARDWARE_MODULE(loopback_module::LoopbackHardwareModule)