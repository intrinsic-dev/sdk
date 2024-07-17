// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/command_validator.h"

#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/icon_state_register.h"
#include "intrinsic/icon/hal/interfaces/icon_state_generated.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

namespace {

absl::StatusOr<HardwareInterfaceHandle<intrinsic_fbs::IconState>>
GetIconStateInterface(absl::string_view shared_memory_namespace,
                      absl::string_view module_name) {
  if (module_name.empty()) {
    return absl::InvalidArgumentError("module_name cannot be empty");
  }

  return GetInterfaceHandle<intrinsic_fbs::IconState>(
      /*memory_namespace=*/shared_memory_namespace,
      /*module_name=*/module_name, /*interface_name=*/kIconStateInterfaceName);
}

}  // namespace

// static
absl::StatusOr<Validator> Validator::Create(
    HardwareInterfaceRegistry& interface_registry) {
  INTR_ASSIGN_OR_RETURN(auto icon_state,
                        GetIconStateInterface(
                            /*shared_memory_namespace=*/interface_registry
                                .SharedMemoryNamespace(),
                            /*module_name=*/interface_registry.ModuleName()));
  return Validator(std::move(icon_state));
}

}  // namespace intrinsic::icon
