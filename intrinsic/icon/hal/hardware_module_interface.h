// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_INTERFACE_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_INTERFACE_H_

#include <memory>

#include "absl/status/status.h"
#include "intrinsic/icon/control/realtime_clock_interface.h"
#include "intrinsic/icon/hal/hardware_module_init_context.h"
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
// control it, ICON issues a call to `Prepare()` to give the hardware module
// time to prepare for realtime operation. Afterwards, ICON signals the hardware
// module using `Activate()` that the real-time loop is beginning. A respective
// call to `Deactivate()` lets the hardware module know that ICON is no longer
// controlling the module.
//
// The real-time loop is composed of a cyclic call to `ReadStatus()` and
// optionally `ApplyCommand()`. A call to `EnableMotion()` allows the hardware
// module to receive command inputs and signals that ICON will trigger calls to
// `ApplyCommand()` in its real-time loop. As long as the hardware module is not
// motion-enabled, no calls to `ApplyCommand()` are received.
// In the first enabled cycle, ICON calls `Enabled()` on the hardware module. In
// the last enabled cycle, ICON calls `Disabled()` on the hardware module.
//
// If a call to `ReadStatus()`, `ApplyCommand()`, `Prepare()`, `Activate()`,
// `Deactivate()` `EnableMotion()`, `DisableMotion()`, `Enabled()` or
// `Disabled()` returns anything else than `StatusOk()`, the hardware module is
// considered faulted and thus motion-disabled.
//
// The statemachine can be split into two parts for a simpler view. The
// non-motion part is shown here:
//
//                            +---------------+
//                            | kDeactivated  | <+
//                            +---------------+  |
//                              |                |
//                              |                |
//                              v                |
//    +-----------------+     +---------------+  |
// +> | kFatallyFaulted | <-- |  kPreparing   |  |
// |  +-----------------+     +---------------+  |
// |    ^                       |                |
// |    |                       |                |
// |    |                       v                |
// |    |                     +---------------+  |
// |    |                     |   kPrepared   |  |
// |    |                     +---------------+  |
// |    |                       |                |
// |    |                       |                |
// |    |                       v                |
// |    |                     +---------------+  |
// |    +-------------------- |  kActivating  |  |
// |                          +---------------+  |
// |                            |                |
// |                            |                |
// |                            v                |
// |                          +---------------+  |
// |                          |  kActivated   |  |
// |                          +---------------+  |
// |                            |                |
// |                            |                |
// |                            v                |
// |                          +---------------+  |
// +------------------------- | kDeactivating | -+
//                            +---------------+
//
// While the actual statemachine implementation is one big statemachine, the
// states kActivated, kMotionEnabling, kMotionEnabled, kMotionDisabling,
// kFaulted and kClearingFaults can be considered sub-states of the kActivated
// state:
//
// +--------------+
// |              v
// |            +----------------------+
// |    +-----> | kActivated(Disabled) | -+
// |    |       +----------------------+  |
// |    |         |                       |
// |    |         |                       |
// |    |         v                       |
// |    |       +----------------------+  |
// |    |    +- |   kMotionEnabling    |  |
// |    |    |  +----------------------+  |
// |    |    |    |                       |
// |    |    |    |                       |
// |    |    |    v                       |
// |    |    |  +----------------------+  |
// |    |    |  |    kMotionEnabled    | -+----+
// |    |    |  +----------------------+  |    |
// |    |    |    |                       |    |
// |    |    |    |                       |    |
// |    |    |    v                       |    |
// |    |    |  +----------------------+  |    |
// |    +----+- |   kMotionDisabling   |  |    |
// |         |  +----------------------+  |    |
// |         |    |                       |    |
// |         |    |                       |    |
// |         |    v                       v    v
// |         |  +--------------------------------+
// |         |  |                                | ---+
// |         |  |            kFaulted            |    |
// |         +> |                                | <--+
// |            +--------------------------------+
// |              |                       ^
// |              |                       |
// |              v                       |
// |            +----------------------+  |
// +----------- |   kClearingFaults    | -+
//              +----------------------+
class HardwareModuleInterface {
 public:
  virtual ~HardwareModuleInterface() = default;

  // Initializes the hardware module and registers its hardware interfaces.
  // The init phase is considered part of the non-realtime bringup phase.
  // `init_context` provides the Hardware Module configuration and other
  // utilities.
  virtual absl::Status Init(HardwareModuleInitContext& init_context) = 0;

  // Gives the hardware module a chance to prepare itself for activation. This
  // function can block. As soon as it returns, the hardware module is
  // considered ready for realtime operation and the hardware module must remain
  // ready since other hardware modules might take longer to prepare.
  //
  // Attention: The hardware module must be ready to receive a call to
  // `Prepare()` at any time (after `Init()` and before `Shutdown()`), but can
  // take its time to return from this function.
  //
  // A viable strategy for this function is to shutdown the internal bus
  // and the rt thread and restart it. If the hardware module drives the clock,
  // it should reset the clock here. It should make sure that no other thread is
  // currently waiting in `RealtimeClock::TickBlockingWith*()` (e.g. by
  // restarting the rt thread) before returning from this function since
  // `RealtimeClock::Reset()` *must not* be called in parallel to
  // `RealtimeClock::TickBlockingWith*()`.
  //
  // ICON calls `Activate()` after a successful call to `Prepare()` on all
  // hardware modules.
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual absl::Status Prepare() { return absl::OkStatus(); }

  // Activates the hardware module.
  // A call to `Activate()` signals the hardware module that ICON has
  // successfully connected to the hardware module and starts the realtime loop.
  // Prior to this, there's no call to `ReadStatus` happening.
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
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
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual RealtimeStatus Deactivate() = 0;

  // Enables motion commands for the hardware modules.
  // Only after a successful call to `EnableMotion()` will ICON call
  // `Enabled()`, which indicates that ICON will call `ApplyCommand()` in
  // the same cycle. However, the time gap between `EnableMotion()` and
  // `Enabled()` can be arbitrary. The hardware module must remain ready to
  // receive the call to `Enabled()`, while multiple calls to `ReadStatus()` may
  // happen in between.
  //
  // A call to `EnableMotion()` can happen asynchronously to
  // `ReadStatus()` and is considered non-realtime.
  //
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual absl::Status EnableMotion() = 0;

  // Signals that the hardware module will now receive commands from ICON via
  // `ApplyCommand()`. Must return without blocking. Only after a successful
  // call to `EnableMotion()` and `Enabled()` does the hardware module receive
  // calls to `ApplyCommand()` and thus puts the hardware module in a state in
  // which it accepts commands. The call to `Enabled()` happens in the first
  // cycle in which `ApplyCommand()` will be called as well. Is called just
  // before `ReadStatus()` in that cycle.
  virtual RealtimeStatus Enabled() { return OkStatus(); }

  // Signals that the hardware module will not receive commands anymore. Must
  // return without blocking.
  //
  // The hardware module should take over control over the hardware.
  // ICON calls `Disabled()` just before `DisableMotion`. However, since
  // `DisableMotion()` is called asynchronously, the time gap between
  // `Disabled()` and `DisableMotion()` can be arbitrary. The call to
  // `Disabled()` happens in the first cycle in which `ApplyCommand()` will not
  // be called. `Disabled()` is called just before `ReadStatus()` in that cycle.
  virtual RealtimeStatus Disabled() { return OkStatus(); }

  // Disables motion commands for the hardware modules.
  // After a call to `DisableMotion()` the hardware module no longer receives
  // calls to `ApplyCommand()`.
  // Similarly to `EnableMotion()` the call can occur asynchronously to
  // `ReadStatus()` and `ApplyCommands()` without realtime considerations. Only
  // after the call successfully returns will the hardware module considered to
  // be motion-disabled.
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual absl::Status DisableMotion() = 0;

  // Clear faults. This function can block and should only return with OkStatus
  // when the faults are cleared. Otherwise, it should return an error.
  //
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual absl::Status ClearFaults() = 0;

  // Shutdown the hardware module.
  // The hardware module can be cleanly shutdown without any realtime
  // considerations.
  // If the hardware module has any blocking functions (other than waiting for
  // `realtime_clock`), such as
  // Enable/Disable/Activate/Deactivate/ClearFaults/ReadStatus/ApplyCommand
  // without timeout, `Shutdown` must cancel or unblock those functions.
  virtual absl::Status Shutdown() = 0;

  // Reads the current hardware status of all exported hardware interfaces.
  // During `EnableMotion()` `ReadStatus()` is expected to return OK and to
  // update the sensor values as well.
  //
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
  virtual RealtimeStatus ReadStatus() = 0;

  // Applies newly set commands of the hardware interfaces.
  // Returns kAborted to indicate a fatal fault, which requires a restart of the
  // process. The Hardware Module runtime will perform the process restart on
  // the next clear faults call via the ResourceHealth interface.
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
