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
#include "intrinsic/icon/hal/interfaces/hardware_module_state.fbs.h"
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/icon/interprocess/remote_trigger/remote_trigger_server.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_server.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
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
  // HardwareModuleRuntime is move only.
  HardwareModuleRuntime() = delete;

  // The copy operations are implicitly deleted, explicitly deleting for
  // visibility.
  HardwareModuleRuntime(const HardwareModuleRuntime&) = delete;
  HardwareModuleRuntime& operator=(const HardwareModuleRuntime&) = delete;

  // Destructor.
  // Stops any ongoing threads and servers.
  ~HardwareModuleRuntime();

  // Move Constructor and Operator.
  HardwareModuleRuntime(HardwareModuleRuntime&& other);
  HardwareModuleRuntime& operator=(HardwareModuleRuntime&& other);

  // Creates a HardwareModuleRuntime taking ownership of the
  // `shared_memory_manager` and `hardware_module`.
  // Forwards errors from creating the DomainSocketServer for exposing the
  // shared memory segments across process boundaries.
  static absl::StatusOr<HardwareModuleRuntime> Create(
      std::unique_ptr<SharedMemoryManager> shared_memory_manager,
      HardwareModule hardware_module);

  // Starts the execution of the module.
  // The module services will be run asynchronously in their own thread, which
  // can be parametrized by `is_realtime` and `cpu_affinity`.
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
  // All parameters are move only.
  HardwareModuleRuntime(
      HardwareModule hardware_module,
      HardwareInterfaceRegistry interface_registry,
      std::unique_ptr<SharedMemoryManager> shared_memory_manager,
      std::unique_ptr<DomainSocketServer> domain_socket_server);

  // Before calling `Run`, we once have to connect the runtime instance to the
  // rest of the ICON IPC. We internally call this in the `Create` function
  // after we've initialized our object. That way we can connect our service
  // callbacks correctly to class member instances (i.e. `PartRegistry`).
  absl::Status Connect();
  HardwareInterfaceRegistry interface_registry_;
  // Closes the shared memory file descriptors that it owns on destruction, so
  // it must go before hardware_module_ and domain_socket_server_:
  std::unique_ptr<SharedMemoryManager> shared_memory_manager_;
  // Reads and writes from/to hardware interfaces that live in shared memory.
  HardwareModule hardware_module_;
  // Exposes shared memory segments to other processes. We can't stop those
  // processes from keeping references after shared_memory_manager_ closes the
  // file descriptors, but at least we can prevent new clients from accessing
  // the shared memory by destroying domain_socket_server_ before
  // shared_menory_manager_.
  std::unique_ptr<DomainSocketServer> domain_socket_server_;

  class CallbackHandler;
  std::unique_ptr<CallbackHandler> callback_handler_;
  std::unique_ptr<RemoteTriggerServer> activate_server_;
  std::unique_ptr<RemoteTriggerServer> deactivate_server_;
  std::unique_ptr<RemoteTriggerServer> prepare_server_;
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
