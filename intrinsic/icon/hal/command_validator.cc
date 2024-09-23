// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/command_validator.h"

#include <utility>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/icon_state_register.h"
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

// static
absl::StatusOr<Validator> Validator::Create(
    HardwareInterfaceRegistry& interface_registry) {
  INTR_ASSIGN_OR_RETURN(
      auto icon_state,
      interface_registry.GetInterfaceHandle<intrinsic_fbs::IconState>(
          /*interface_name=*/kIconStateInterfaceName));

  return Validator(std::move(icon_state));
}

}  // namespace intrinsic::icon
