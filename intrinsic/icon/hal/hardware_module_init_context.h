// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_INIT_CONTEXT_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_INIT_CONTEXT_H_

#include "absl/base/attributes.h"
#include "grpcpp/server_builder.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/module_config.h"

namespace intrinsic::icon {

// Provides configuration and functions needed during initialization of a
// Hardware Module such as
// - access to the module configuration
// - access to the interface registry
// - the ability to register a gRPC service
class HardwareModuleInitContext {
 public:
  HardwareModuleInitContext(HardwareInterfaceRegistry& interface_registry
                                ABSL_ATTRIBUTE_LIFETIME_BOUND,
                            grpc::ServerBuilder& server_builder
                                ABSL_ATTRIBUTE_LIFETIME_BOUND,
                            const ModuleConfig& config)
      : interface_registry_(interface_registry),
        server_builder_(server_builder),
        module_config_(config) {}
  ~HardwareModuleInitContext() = default;
  // Delete copy and move constructors since this class contains temporary
  // objects which are deleted after the hardware module is initialized.
  // Hardware modules should not be able to copy or move this class.
  HardwareModuleInitContext(const HardwareModuleInitContext&) = delete;
  HardwareModuleInitContext& operator=(const HardwareModuleInitContext&) =
      delete;
  HardwareModuleInitContext& operator=(HardwareModuleInitContext&&) = delete;

  // Returns the interface registry for this Hardware Module to register
  // interfaces.
  HardwareInterfaceRegistry& GetInterfaceRegistry() const {
    return interface_registry_;
  }

  // Returns the config for this Hardware Module.
  const ModuleConfig& GetModuleConfig() const { return module_config_; }

  // Registers a gRPC service with the hardware module runtime. The runtime
  // makes this service available to external components some time after the
  // hardware module's `Init()` function returns.
  //
  // Attention: `service` must live until the `Shutdown()` of the Hardware
  // Module is called!
  //
  // The gRPC service will still be served even if
  // HardwareModuleInterface::Init() returns an error.
  //
  // The gRPC service will run on a port that is reachable from external
  // components such as the frontend.
  void RegisterGrpcService(grpc::Service& service) {
    server_builder_.RegisterService(&service);
  }

 private:
  HardwareInterfaceRegistry& interface_registry_;
  grpc::ServerBuilder& server_builder_;
  const ModuleConfig module_config_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_INIT_CONTEXT_H_
