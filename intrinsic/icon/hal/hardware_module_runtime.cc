// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/hardware_module_runtime.h"

#include <atomic>
#include <functional>
#include <memory>
#include <utility>
#include <vector>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/hardware_module_interface.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_utils.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_server.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {

namespace hardware_interface_traits {
INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::HardwareModuleState,
                                 intrinsic_fbs::BuildHardwareModuleState,
                                 "intrinsic_fbs.HardwareModuleState")
}  // namespace hardware_interface_traits

static constexpr char kDelimiter[] = "__";

class HardwareModuleRuntime::CallbackHandler final {
 public:
  explicit CallbackHandler(
      HardwareModuleInterface* instance,
      intrinsic_fbs::HardwareModuleState* hardware_module_state) noexcept
      : instance_(instance), hardware_module_state_(hardware_module_state) {}

  // Server callback for trigger `Activate` on the hardware module.
  void OnActivate() {
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kActivating, "");
    if (auto ret = instance_->Activate(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'Activate' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
      return;
    }
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kActivated, "");
  }

  // Server callback for trigger `Deactivate` on the hardware module.
  void OnDeactivate() {
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kDeactivating, "");
    if (auto ret = instance_->Deactivate(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'Deactivate' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
      return;
    }
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kDeactivated, "");
  }

  // Server callback for trigger `EnableMotion` on the hardware module.
  void OnEnableMotion() {
    absl::MutexLock lock(&lock_);
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kMotionEnabling, "");
    if (auto ret = instance_->EnableMotion(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'EnableMotion' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
      return;
    }
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kMotionEnabled, "");
  }

  // Server callback for trigger `DisableMotion` on the hardware module.
  void OnDisableMotion() {
    absl::MutexLock lock(&lock_);
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kMotionDisabling, "");
    if (auto ret = instance_->DisableMotion(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'DisableMotion' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
      return;
    }
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kActivated, "");
  }

  // Server callback for trigger `ClearFaults` on the hardware module.
  void OnClearFaults() {
    absl::MutexLock lock(&lock_);
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kClearingFaults, "");
    if (auto ret = instance_->ClearFaults(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'ClearFaults' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
      return;
    }
    intrinsic_fbs::SetState(hardware_module_state_,
                            intrinsic_fbs::StateCode::kActivated, "");
  }

  // Server callback for trigger `Shutdown` on the hardware module.
  void OnShutdown() {
    if (auto ret = instance_->Shutdown(); !ret.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "PUBLIC: Call to 'Shutdown' failed: " << ret.message();
      intrinsic_fbs::SetState(hardware_module_state_,
                              intrinsic_fbs::StateCode::kFaulted,
                              ret.message());
    }
  }

  // Server callback for trigger `ReadStatus` on the hardware module.
  void OnReadStatus() {
    if (auto ret = instance_->ReadStatus(); !ret.ok()) {
      INTRINSIC_RT_LOG_THROTTLED(ERROR)
          << "PUBLIC: Call to 'ReadStatus' failed: " << ret.message();
      // Only update the state to faulted if there is no other ongoing request.
      if (lock_.TryLock()) {
        intrinsic_fbs::SetState(hardware_module_state_,
                                intrinsic_fbs::StateCode::kFaulted,
                                ret.message());
        lock_.Unlock();
      }
    }
  }

  // Server callback for trigger `ApplyCommand` on the hardware module.
  void OnApplyCommand() {
    if (auto ret = instance_->ApplyCommand(); !ret.ok()) {
      INTRINSIC_RT_LOG_THROTTLED(ERROR)
          << "PUBLIC: Call to 'ApplyCommand' failed: " << ret.message();
      // Only update the state to faulted if there is no other ongoing request.
      if (lock_.TryLock()) {
        intrinsic_fbs::SetState(hardware_module_state_,
                                intrinsic_fbs::StateCode::kFaulted,
                                ret.message());
        lock_.Unlock();
      }
    }
  }

 private:
  HardwareModuleInterface* instance_;
  intrinsic_fbs::HardwareModuleState* hardware_module_state_;
  absl::Mutex lock_;
};

absl::StatusOr<HardwareModuleRuntime> HardwareModuleRuntime::Create(
    HardwareModule hardware_module) {
  INTRINSIC_ASSIGN_OR_RETURN(
      auto interface_registry,
      HardwareInterfaceRegistry::Create(hardware_module.config));
  HardwareModuleRuntime runtime(std::move(hardware_module),
                                std::move(interface_registry));
  INTRINSIC_RETURN_IF_ERROR(runtime.Connect());
  return runtime;
}

HardwareModuleRuntime::HardwareModuleRuntime() = default;

HardwareModuleRuntime::HardwareModuleRuntime(
    HardwareModule hardware_module,
    HardwareInterfaceRegistry interface_registry)
    : interface_registry_(std::move(interface_registry)),
      hardware_module_(std::move(hardware_module)),
      callback_handler_(nullptr),
      activate_server_(nullptr),
      deactivate_server_(nullptr),
      enable_motion_server_(nullptr),
      disable_motion_server_(nullptr),
      read_status_server_(nullptr),
      apply_command_server_(nullptr),
      stop_requested_(std::make_unique<std::atomic<bool>>(false)) {}

HardwareModuleRuntime::~HardwareModuleRuntime() {
  if (stop_requested_) {
    stop_requested_->store(true);
  }
  if (state_change_thread_.Joinable()) {
    state_change_thread_.Join();
  }
}

HardwareModuleRuntime::HardwareModuleRuntime(HardwareModuleRuntime&& other)
    : interface_registry_(std::exchange(other.interface_registry_,
                                        HardwareInterfaceRegistry())),
      hardware_module_(std::exchange(other.hardware_module_, HardwareModule())),
      callback_handler_(std::exchange(other.callback_handler_, nullptr)),
      activate_server_(std::exchange(other.activate_server_, nullptr)),
      deactivate_server_(std::exchange(other.deactivate_server_, nullptr)),
      enable_motion_server_(
          std::exchange(other.enable_motion_server_, nullptr)),
      disable_motion_server_(
          std::exchange(other.disable_motion_server_, nullptr)),
      clear_faults_server_(std::exchange(other.clear_faults_server_, nullptr)),
      read_status_server_(std::exchange(other.read_status_server_, nullptr)),
      apply_command_server_(
          std::exchange(other.apply_command_server_, nullptr)),
      hardware_module_state_interface_(
          std::move(other.hardware_module_state_interface_)),
      stop_requested_(std::exchange(other.stop_requested_, nullptr)),
      state_change_thread_(std::move(other.state_change_thread_)) {}

HardwareModuleRuntime& HardwareModuleRuntime::operator=(
    HardwareModuleRuntime&& other) {
  if (&other == this) {
    return *this;
  }
  interface_registry_ =
      std::exchange(other.interface_registry_, HardwareInterfaceRegistry());
  hardware_module_ = std::exchange(other.hardware_module_, HardwareModule());
  callback_handler_ = std::exchange(other.callback_handler_, nullptr);
  activate_server_ = std::exchange(other.activate_server_, nullptr);
  deactivate_server_ = std::exchange(other.deactivate_server_, nullptr);
  enable_motion_server_ = std::exchange(other.enable_motion_server_, nullptr);
  disable_motion_server_ = std::exchange(other.disable_motion_server_, nullptr);
  clear_faults_server_ = std::exchange(other.clear_faults_server_, nullptr);
  read_status_server_ = std::exchange(other.read_status_server_, nullptr);
  apply_command_server_ = std::exchange(other.apply_command_server_, nullptr);
  hardware_module_state_interface_ =
      std::move(other.hardware_module_state_interface_);
  stop_requested_ = std::exchange(other.stop_requested_, nullptr);
  state_change_thread_ = std::move(other.state_change_thread_);
  return *this;
}

absl::Status HardwareModuleRuntime::Connect() {
  // We add an "inbuilt" status segment for the hardware module state.
  INTRINSIC_ASSIGN_OR_RETURN(
      hardware_module_state_interface_,
      interface_registry_
          .AdvertiseMutableInterface<intrinsic_fbs::HardwareModuleState>(
              "hardware_module_state",
              intrinsic_fbs::BuildHardwareModuleState()));
  callback_handler_ = std::make_unique<CallbackHandler>(
      hardware_module_.instance.get(), *hardware_module_state_interface_);

  INTRINSIC_ASSIGN_OR_RETURN(
      auto activate_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "activate"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnActivate,
                    callback_handler_.get())));
  activate_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(activate_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto deactivate_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "deactivate"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnDeactivate,
                    callback_handler_.get())));
  deactivate_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(deactivate_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto enable_motion_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "enable_motion"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnEnableMotion,
                    callback_handler_.get())));
  enable_motion_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(enable_motion_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto disable_motion_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "disable_motion"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnDisableMotion,
                    callback_handler_.get())));
  disable_motion_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(disable_motion_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto clear_faults_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "clear_faults"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnClearFaults,
                    callback_handler_.get())));
  clear_faults_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(clear_faults_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto read_status_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "read_status"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnReadStatus,
                    callback_handler_.get())));
  read_status_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(read_status_server));

  INTRINSIC_ASSIGN_OR_RETURN(
      auto apply_command_server,
      RemoteTriggerServer::Create(
          absl::StrCat("/", hardware_module_.config.GetName(), kDelimiter,
                       "apply_command"),
          std::bind(&HardwareModuleRuntime::CallbackHandler::OnApplyCommand,
                    callback_handler_.get())));
  apply_command_server_ =
      std::make_unique<RemoteTriggerServer>(std::move(apply_command_server));

  return absl::OkStatus();
}

absl::Status HardwareModuleRuntime::Run(bool is_realtime,
                                        const std::vector<int>& cpu_affinity) {
  if (activate_server_ == nullptr) {
    return absl::InternalError(
        "PUBLIC: Hardware module does not seem to be connected. Did you call "
        "`Connect()`?");
  }

  // Helper lambda to set the state to kInitFailed if any of the initialization
  // steps below fail.
  auto set_init_failed_on_error = [this](absl::Status status) -> absl::Status {
    if (!status.ok()) {
      intrinsic_fbs::SetState(*hardware_module_state_interface_,
                              intrinsic_fbs::StateCode::kInitFailed,
                              status.message());
    }
    return status;
  };

  const auto init_status =
      set_init_failed_on_error(hardware_module_.instance->Init(
          interface_registry_, hardware_module_.config));
  if (!init_status.ok()) {
    LOG(ERROR) << "Initializing the module failed with: " << init_status;
  }
  // AdvertiseHardwareInfo is required so that ICON can connect to the module
  // and read the init failure.
  INTRINSIC_RETURN_IF_ERROR(
      set_init_failed_on_error(interface_registry_.AdvertiseHardwareInfo()));
  // Ensures that no methods on the uninitialized module can be called.
  INTRINSIC_RETURN_IF_ERROR(init_status);

  intrinsic::Thread::Options state_change_thread_options;
  state_change_thread_options.SetName("StateChange");

  intrinsic::Thread::Options activate_thread_options;
  activate_thread_options.SetName("Activate");

  intrinsic::Thread::Options read_status_thread_options;
  read_status_thread_options.SetName("ReadStatus");

  intrinsic::Thread::Options apply_command_thread_options;
  apply_command_thread_options.SetName("ApplyCommand");

  if (is_realtime) {
    state_change_thread_options.SetRealtimeLowPriorityAndScheduler();
    state_change_thread_options.SetAffinity(cpu_affinity);
    activate_thread_options.SetRealtimeLowPriorityAndScheduler();
    activate_thread_options.SetAffinity(cpu_affinity);
    read_status_thread_options.SetRealtimeHighPriorityAndScheduler();
    read_status_thread_options.SetAffinity(cpu_affinity);
    apply_command_thread_options.SetRealtimeHighPriorityAndScheduler();
    apply_command_thread_options.SetAffinity(cpu_affinity);
  }

  auto state_change_query = [](std::atomic<bool>* stop_requested,
                               RemoteTriggerServer* deactivate_server,
                               RemoteTriggerServer* enable_motion_server,
                               RemoteTriggerServer* disable_motion_server,
                               RemoteTriggerServer* clear_faults_server) {
    while (!stop_requested->load()) {
      deactivate_server->Query();
      enable_motion_server->Query();
      disable_motion_server->Query();
      clear_faults_server->Query();
    }
  };

  INTRINSIC_RETURN_IF_ERROR(set_init_failed_on_error(state_change_thread_.Start(
      state_change_thread_options, state_change_query, stop_requested_.get(),
      deactivate_server_.get(), enable_motion_server_.get(),
      disable_motion_server_.get(), clear_faults_server_.get())));
  INTRINSIC_RETURN_IF_ERROR(set_init_failed_on_error(
      activate_server_->StartAsync(activate_thread_options)));
  INTRINSIC_RETURN_IF_ERROR(set_init_failed_on_error(
      read_status_server_->StartAsync(read_status_thread_options)));
  INTRINSIC_RETURN_IF_ERROR(set_init_failed_on_error(
      apply_command_server_->StartAsync(apply_command_thread_options)));

  return absl::OkStatus();
}

absl::Status HardwareModuleRuntime::Stop() {
  apply_command_server_->Stop();
  read_status_server_->Stop();
  stop_requested_->store(true);
  if (state_change_thread_.Joinable()) {
    state_change_thread_.Join();
  }
  return hardware_module_.instance->Shutdown();
}

bool HardwareModuleRuntime::IsStarted() const {
  bool started = state_change_thread_.Joinable();
  started &= read_status_server_->IsStarted();
  started &= apply_command_server_->IsStarted();

  return started;
}

const HardwareModule& HardwareModuleRuntime::GetHardwareModule() const {
  return hardware_module_;
}

}  // namespace intrinsic::icon
