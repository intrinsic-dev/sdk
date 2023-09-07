// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_PLUGIN_REGISTER_MACRO_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_PLUGIN_REGISTER_MACRO_H_

#include "intrinsic/icon/control/c_api/c_plugin_api.h"
#include "intrinsic/icon/control/c_api/external_action_api/make_icon_action_vtable.h"

// Implements the entrypoint for an ICON custom Action plugin for
// `ActionClassName`. Place this in a separate file (my_action_plugin.cc) and
// add a BUILD target with the following options to allow ICON to load your
// `ActionClassName` as a plugin:
//
// ```BUILD
// cc_binary(
//     name = "my_action_plugin.so",
//     srcs = ["my_action_plugin.cc"],
//     linkshared = 1,
//     linkstatic = 1,
//     deps = [
//         "//intrinsic/icon/control/c_api/external_action_api:icon_plugin_register_macro",
//         ":my_action",
//     ],
// )
// ```
//
// Before you do, make sure your Action not only implements the virtual
// functions from IconActionInterface, but also meets the additional
// requirements listed in icon_action_interface.h.
#define INTRINSIC_ICON_REGISTER_ICON_ACTION_PLUGIN(ActionClassName) \
  extern "C" {                                                      \
  __attribute__((__visibility__("default"))) XfaIconRealtimeStatus  \
  INTRINSIC_ICON_ACTION_PLUGIN_ENTRY_POINT(                         \
      XfaIconRegisterActionType register_action_type_fn) {          \
    return intrinsic::icon::RegisterIconAction<ActionClassName>(    \
        register_action_type_fn);                                   \
  }                                                                 \
  }

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_PLUGIN_REGISTER_MACRO_H_
