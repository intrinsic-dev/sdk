// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_ACTIONS_ADIO_INFO_H_
#define INTRINSIC_ICON_ACTIONS_ADIO_INFO_H_

#include "intrinsic/icon/actions/adio.pb.h"

namespace intrinsic {
namespace icon {

// Contains information needed by clients to correctly describe a Analog/Digital
// Input/Output Action.
struct ADIOActionInfo {
  // ADIO action type name and description
  static constexpr char kActionTypeName[] = "xfa.adio";
  static constexpr char kActionDescription[] =
      "Allows to react to Analog/Digital Inputs and set Digital Outputs. "
      "'expectations' and 'outputs' can be provided using the same command "
      "message. "
      "It is an error to provide neither 'expectations', nor 'outputs'.";
  static constexpr char kAdioSlotName[] = "adio";
  static constexpr char kAdioSlotDescription[] =
      "The Action sets and reads this Part's inputs and outputs.";
  static constexpr char kAllInputsMatch[] = "xfa.all_inputs_match";
  static constexpr char kAllInputsMatchDescription[] =
      "True if the input values match the expected values. Always `false` if "
      "no input triggers are defined in the action parameters.";
  static constexpr char kAnyInputsMatch[] = "xfa.any_inputs_match";
  static constexpr char kAnyInputsMatchDescription[] =
      "True if any input value matches it's expected values. Always `false` if "
      "no input triggers are defined in the action parameters.";

  static constexpr char kOutputsSet[] = "xfa.outputs_set";
  static constexpr char kOutputsSetDescription[] =
      "True if the commanded output values have been set on the device. Always "
      "`false` if no outputs are provided in the action parameters.";

  using FixedParams = ::xfa::icon::actions::proto::ADIOFixedParams;
};

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_ACTIONS_ADIO_INFO_H_
