// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_INTERFACE_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_INTERFACE_H_

#include <memory>

#include "absl/status/status.h"
#include "intrinsic/icon/control/realtime_clock_interface.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Interface definition for implementing an ICON hardware module.
// An implementation of this interface enables the integration of a custom
// hardware module into ICON.
//
// Both the hardware module and ICON are spawned in their respective processes
// and are synchronized via IPC calls to the functions defined in this
// interface. Data exchange happens via the exported hardware interfaces and are
// semantically classified into read-only state interfaces as well as mutable
// command interfaces.
//
// When a hardware module is started, a call to `Init()` is triggered. This
// function allows to set up various robot communication mechanisms and is
// responsible for advertising its state and command hardware interfaces.
// Once the hardware module is successfully initialized and ICON is ready to
// control it, ICON issues a call to `Activate()` and thus signals the hardware
// module that a real-time loop is beginning. A respective call to
// `Deactivate()` lets the hardware module know that ICON is no longer
// controlling the module.

// The real-time loop is composed of a cyclic call to `ReadStatus()` and
// optionally `ApplyCommand()`. A call to `EnableMotion()` allows the hardware
// module to receive command inputs and signals that ICON will trigger calls to
// `ApplyCommand()` in its real-time loop. As long as the hardware module is not
// motion-enabled, no calls to `ApplyCommand()` are received. If a call to
// `ReadStatus()`, `ApplyCommand()`, `Activate()`, `Deactivate()`
// `EnableMotion()` or `DisableMotion()` returns anything else than
// `StatusOk()`, the hardware module is considered faulted and thus
// motion-disabled.
class HardwareModuleInterface {
 public:
  virtual ~HardwareModuleInterface() = default;

  // Initializes the hardware module and registers its hardware interfaces.
  // The init phase is considered part of the non-realtime bringup phase.
  virtual absl::Status Init(HardwareInterfaceRegistry& interface_registry,
                            const ModuleConfig& config) = 0;

  // Activates the hardware module.
  // A call to `Activate()` signals the hardware module that ICON has
  // successfully connected to the hardware module and starts the realtime loop.
  // Prior to this, there's no call to `ReadStatus` happening.
  virtual RealtimeStatus Activate() = 0;

  // Deactivates the hardware module.
  // A call to `Deactivate()` signals the hardware module that ICON has been
  // disconnected and the hardware module is no longer controlled within a
  // realtime loop. No calls to `ReadStatus()` or `ApplyCommand()` are happening
  // after this.
  // The hardware module is supposed to be independent, yet alive. That is, a
  // call to `Deactivate()` is semantically different from `Shutdown()` in which
  // a subsequent call to `Activate()` is designed to succeed when the hardware
  // module is deactivated.
  virtual RealtimeStatus Deactivate() = 0;

  // Enables motion commands for the hardware modules.
  // Only after a successful call to `EnableMotion()` does the hardware module
  // receive calls to `ApplyCommand()` and thus puts the hardware module in a
  // state in which it accepts commands.
  // A call to `EnableMotion()` can happen asynchronously to `ReadStatus()` and
  // is considered non-realtime.
  virtual absl::Status EnableMotion() = 0;

  // Disables motion commands for the hardware modules.
  // After a call to `DisableMotion()` the hardware module no longer receives
  // calls to `ApplyCommand()`.
  // Similarly to `EnableMotion()` the call can occur asynchronously to
  // `ReadStatus()` and `ApplyCommands()` without realtime considerations. Only
  // after the call successfully returns will the hardware module considered to
  // be motion-disabled.
  virtual absl::Status DisableMotion() = 0;

  // Clear faults.
  virtual absl::Status ClearFaults() = 0;

  // Shutdown the hardware module.
  // The hardware module can be cleanly shutdown without any realtime
  // considerations.
  virtual absl::Status Shutdown() = 0;

  // Reads the current hardware status of all exported hardware interfaces.
  virtual RealtimeStatus ReadStatus() = 0;

  // Applies newly set commands of the hardware interfaces.
  virtual RealtimeStatus ApplyCommand() = 0;
};

struct HardwareModule {
  // Realtime clock, if this hardware module drives the clock. Otherwise,
  // nullptr. ModuleConfig takes a non-owning pointer to this, so this must
  // outlive config. `instance` of course ticks the clock, so this must also
  // outlive `instance`.
  std::unique_ptr<RealtimeClockInterface> realtime_clock;
  std::unique_ptr<HardwareModuleInterface> instance;
  ModuleConfig config;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_INTERFACE_H_
