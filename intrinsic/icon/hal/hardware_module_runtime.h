// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_RUNTIME_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_RUNTIME_H_

#include <atomic>
#include <memory>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "grpcpp/server_builder.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/hardware_module_interface.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"
#include "intrinsic/icon/hal/interfaces/icon_state_generated.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_server.h"
#include "intrinsic/util/thread/thread.h"

namespace intrinsic::icon {

// Runtime environment for executing a hardware module as its own binary.
// It sets up all necessary infrastructure to connect the module to the ICON IPC
// services.
// HardwareModuleRuntime::CallbackHandler ensures
// * ReadStatus does not forward the call to the module if it is not activated.
// * ApplyCommand does not forward the call to the module if it is not enabled.
// * No illegal transitions are taken, see `HardwareModuleTransitionGuard()`.
// * Activate/Deactivate can be called regardless if there is an ongoing
//   transition. Ongoing transitions are aborted. Ongoing callbacks to the
//   HardwareModuleInterface inside of those cannot be aborted, though.
// * An error of ReadStatus or ApplyCommand overrides the final state of an
//   ongoing transition. Deactivate takes precedence over faults.
//
// Further considerations:
// * Activate/Deactivate must only be called when the ICON main loop is not
// running, i.e. before and after the lockstep thread is running and calling
// ReadStatus/ApplyCommand.
class HardwareModuleRuntime final {
 public:
  // Default constructor.
  HardwareModuleRuntime();

  // Destructor.
  // Stops any ongoing threads and servers.
  ~HardwareModuleRuntime();

  // Move Constructor and Operator.
  HardwareModuleRuntime(HardwareModuleRuntime&& other);
  HardwareModuleRuntime& operator=(HardwareModuleRuntime&& other);

  static absl::StatusOr<HardwareModuleRuntime> Create(
      HardwareModule hardware_module);

  // Starts the execution of the module.
  // The module services will be run asynchronously in their own thread, which
  // can be parametrized by the thread options.
  // `server_builder` gives the hardware module the possibility to register gRPC
  // services.
  absl::Status Run(grpc::ServerBuilder& server_builder,
                   bool is_realtime = false,
                   const std::vector<int>& cpu_affinity = {});

  // Stops the execution of the module.
  // A call to `Stop()` stops the services and the module functions are no
  // longer called.
  absl::Status Stop();

  // Indicates whether the current runtime instance is started by a call to
  // `Run`.
  bool IsStarted() const;

  // Returns a reference to the underlying hardware module instance.
  const HardwareModule& GetHardwareModule() const;

  // Sets the state of the hardware module. Make sure nothing is reading the
  // state at the same time.
  void SetStateTestOnly(intrinsic_fbs::StateCode state);

  absl::StatusOr<const intrinsic_fbs::HardwareModuleState>
  GetHardwareModuleState() const;

 private:
  HardwareModuleRuntime(HardwareModule hardware_module,
                        HardwareInterfaceRegistry interface_registry);

  // Before calling `Run`, we once have to connect the runtime instance to the
  // rest of the ICON IPC. We internally call this in the `Create` function
  // after we've initialized our object. That way we can connect our service
  // callbacks correctly to class member instances (i.e. `PartRegistry`).
  absl::Status Connect();

  HardwareInterfaceRegistry interface_registry_;
  HardwareModule hardware_module_;

  class CallbackHandler;
  std::unique_ptr<CallbackHandler> callback_handler_;
  std::unique_ptr<RemoteTriggerServer> activate_server_;
  std::unique_ptr<RemoteTriggerServer> deactivate_server_;
  std::unique_ptr<RemoteTriggerServer> enable_motion_server_;
  std::unique_ptr<RemoteTriggerServer> disable_motion_server_;
  std::unique_ptr<RemoteTriggerServer> clear_faults_server_;
  std::unique_ptr<RemoteTriggerServer> read_status_server_;
  std::unique_ptr<RemoteTriggerServer> apply_command_server_;
  MutableHardwareInterfaceHandle<intrinsic_fbs::HardwareModuleState>
      hardware_module_state_interface_;
  HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state_interface_;

  // Runs activate, deactivate, enable, disable and clear faults.
  std::unique_ptr<std::atomic<bool>> stop_requested_;
  intrinsic::Thread state_change_thread_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_RUNTIME_H_
