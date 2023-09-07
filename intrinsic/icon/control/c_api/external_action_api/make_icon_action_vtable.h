// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_MAKE_ICON_ACTION_VTABLE_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_MAKE_ICON_ACTION_VTABLE_H_

#include <memory>
#include <string>
#include <type_traits>
#include <variant>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_split.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/message.h"
#include "intrinsic/icon/control/c_api/c_plugin_api.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_rtcl_action.h"
#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_action_factory_context.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_action_interface.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_realtime_slot_map.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_streaming_io_access.h"
#include "intrinsic/icon/control/c_api/wrappers/string_wrapper.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Helper struct to wrap a C++ IconActionInterface instance for use with the
// ICON C API.
struct ActionAndServerVtable {
  std::unique_ptr<IconActionInterface> action;
  XfaIconServerFunctions server_functions;
};

// Visitor to write a variant<bool, double, int64> into an
// XfaIconStateVariableValue C struct.
struct StateVariableVisitor {
  void operator()(bool value) {
    state_variable_out->type = XfaIconStateVariableValue::kBool;
    state_variable_out->value.bool_value = value;
  }
  void operator()(double value) {
    state_variable_out->type = XfaIconStateVariableValue::kDouble;
    state_variable_out->value.double_value = value;
  }
  void operator()(int64_t value) {
    state_variable_out->type = XfaIconStateVariableValue::kInt64;
    state_variable_out->value.int64_value = value;
  }
  XfaIconStateVariableValue* state_variable_out;
};

// Builds a Vtable for `ActionT` that ICON's plugin API can use to build,
// destroy and operate instances of `ActionT` via the C plugin API.
template <typename ActionT,
          typename =
              std::enable_if_t<std::is_base_of_v<IconActionInterface, ActionT>>,
          typename = std::enable_if_t<std::is_base_of_v<
              google::protobuf::Message, typename ActionT::ParameterProto>>>
XfaIconRtclActionVtable MakeIconActionVtable() {
  return {
      .create =
          [](XfaIconServerFunctions server_functions,
             XfaIconStringView params_any_proto,
             XfaIconActionFactoryContext* action_factory_context,
             XfaIconRtclAction** action_ptr_out) -> XfaIconRealtimeStatus {
        google::protobuf::Any params_any;
        if (!params_any.ParseFromArray(params_any_proto.data,
                                       params_any_proto.size)) {
          return FromAbslStatus(absl::InvalidArgumentError(
              "Failed to parse parameter Any proto from string."));
        }
        typename ActionT::ParameterProto params;
        if (!params_any.UnpackTo(&params)) {
          // Work around a quirk of StrSplit, where it sometimes returns an
          // empty list instead of a list containing the empty string.
          std::string type_name = "";
          if (!params_any.type_url().empty()) {
            std::vector<std::string> url_components =
                absl::StrSplit(params_any.type_url(), '/');
            type_name = url_components.back();
          }
          return FromAbslStatus(absl::InvalidArgumentError(absl::StrCat(
              "Failed to unpack parameter Any proto. Expected '",
              ActionT::ParameterProto::GetDescriptor()->full_name(), "', got '",
              type_name, "'")));
        }
        IconActionFactoryContext context(
            action_factory_context, server_functions.action_factory_context);
        absl::StatusOr<std::unique_ptr<ActionT>> action =
            ActionT::Create(params, context);
        if (!action.ok()) return FromAbslStatus(action.status());
        *action_ptr_out = reinterpret_cast<XfaIconRtclAction*>(
            new ActionAndServerVtable{.action = std::move(action.value()),
                                      .server_functions = server_functions});
        return FromAbslStatus(OkStatus());
      },
      .destroy =
          [](XfaIconRtclAction* action) {
            // This calls the destructor for the unique_ptr in
            // ActionAndServerVtable and correctly cleans up the Action
            // instance.
            delete reinterpret_cast<ActionAndServerVtable*>(action);
          },
      .on_enter =
          [](XfaIconRtclAction* action,
             const XfaIconRealtimeSlotMap* slot_map) -> XfaIconRealtimeStatus {
        auto* action_and_server_vtable =
            reinterpret_cast<ActionAndServerVtable*>(action);
        return FromRealtimeStatus(
            action_and_server_vtable->action->OnEnter(IconConstRealtimeSlotMap(
                slot_map,
                action_and_server_vtable->server_functions.realtime_slot_map,
                action_and_server_vtable->server_functions
                    .feature_interfaces)));
      },
      .sense = [](XfaIconRtclAction* self,
                  const XfaIconRealtimeSlotMap* slot_map,
                  XfaIconStreamingIoRealtimeAccess* streaming_io_access)
          -> XfaIconRealtimeStatus {
        auto* action_and_server_vtable =
            reinterpret_cast<ActionAndServerVtable*>(self);
        IconStreamingIoAccess streaming_io_access_wrapped(
            streaming_io_access,
            action_and_server_vtable->server_functions.streaming_io_access);
        return FromRealtimeStatus(action_and_server_vtable->action->Sense(
            IconConstRealtimeSlotMap(
                slot_map,
                action_and_server_vtable->server_functions.realtime_slot_map,
                action_and_server_vtable->server_functions.feature_interfaces),
            streaming_io_access_wrapped));
      },
      .control = [](XfaIconRtclAction* self,
                    XfaIconRealtimeSlotMap* slot_map) -> XfaIconRealtimeStatus {
        auto* action_and_server_vtable =
            reinterpret_cast<ActionAndServerVtable*>(self);
        IconRealtimeSlotMap realtime_slot_map(
            slot_map,
            action_and_server_vtable->server_functions.realtime_slot_map,
            action_and_server_vtable->server_functions.feature_interfaces);
        return FromRealtimeStatus(
            action_and_server_vtable->action->Control(realtime_slot_map));
      },
      .get_state_variable = [](const XfaIconRtclAction* self, const char* name,
                               size_t name_size,
                               XfaIconStateVariableValue* state_variable_out)
          -> XfaIconRealtimeStatus {
        const auto* action_and_server_vtable =
            reinterpret_cast<const ActionAndServerVtable*>(self);

        auto state_variable =
            action_and_server_vtable->action->GetStateVariable(
                absl::string_view(name, name_size));
        if (!state_variable.ok()) {
          return FromRealtimeStatus(state_variable.status());
        }
        std::visit(
            StateVariableVisitor{.state_variable_out = state_variable_out},
            state_variable.value());
        return FromRealtimeStatus(OkStatus());
      },
  };
}

// Implements the entrypoint for an ICON custom Action plugin containing a
// single `ActionT`. Place this in a library and name it
// INTRINSIC_ICON_ACTION_PLUGIN_ENTRY_POINT (see
// icon/control/c_api/c_plugin_api.h) to allow ICON to load your `ActionT` as a
// plugin.
//
// Before you do, make sure your Action not only implements the virtual
// functions from IconActionInterface, but also meets the additional
// requirements listed in icon_action_interface.h.
template <typename ActionT,
          typename =
              std::enable_if_t<std::is_base_of_v<IconActionInterface, ActionT>>>
XfaIconRealtimeStatus RegisterIconAction(
    XfaIconRegisterActionType register_action_type_fn) {
  intrinsic_proto::icon::ActionSignature signature = ActionT::GetSignature();
  const std::string signature_string = signature.SerializeAsString();
  const std::string action_type_name(ActionT::kName);

  return register_action_type_fn(
      /*icon_api_version=*/0,
      /*action_type_name=*/WrapView(action_type_name),
      /*action_signature_proto=*/WrapView(signature_string),
      MakeIconActionVtable<ActionT>());
}

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_MAKE_ICON_ACTION_VTABLE_H_
