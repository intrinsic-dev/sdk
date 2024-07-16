// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/c_api/external_action_api/icon_action_factory_context.h"

#include <cstdint>
#include <memory>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/c_api/c_action_factory_context.h"
#include "intrinsic/icon/control/c_api/c_types.h"
#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"
#include "intrinsic/icon/control/c_api/wrappers/string_wrapper.h"
#include "intrinsic/icon/control/realtime_signal_types.h"
#include "intrinsic/icon/control/slot_types.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {
namespace {
struct DestroyIconString {
  void operator()(XfaIconString* ptr) { destroy(ptr); }
  XfaIconStringDestroy destroy;
};
}  // namespace

intrinsic_proto::icon::ServerConfig IconActionFactoryContext::ServerConfig()
    const {
  std::unique_ptr<XfaIconString, DestroyIconString> server_config_string(
      icon_action_factory_context_vtable_.server_config(
          icon_action_factory_context_),
      DestroyIconString{icon_action_factory_context_vtable_.destroy_string});
  intrinsic_proto::icon::ServerConfig config_proto;
  config_proto.ParseFromArray(server_config_string->data,
                              server_config_string->size);
  return config_proto;
}

absl::StatusOr<intrinsic::icon::SlotInfo> IconActionFactoryContext::GetSlotInfo(
    absl::string_view slot_name) const {
  XfaIconSlotInfo slot_info_c;
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(icon_action_factory_context_vtable_.get_slot_info(
          icon_action_factory_context_, WrapView(slot_name), &slot_info_c)));
  std::unique_ptr<XfaIconString, DestroyIconString> part_config_string(
      slot_info_c.part_config_buffer,
      DestroyIconString{icon_action_factory_context_vtable_.destroy_string});
  intrinsic::icon::SlotInfo slot_info;
  slot_info.slot_id = RealtimeSlotId(slot_info_c.realtime_slot_id);
  slot_info.config.ParseFromArray(part_config_string->data,
                                  part_config_string->size);
  return slot_info;
}

absl::StatusOr<RealtimeSignalId> IconActionFactoryContext::GetRealtimeSignalId(
    absl::string_view realtime_signal_name) {
  uint64_t signal_id_out;
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(icon_action_factory_context_vtable_.get_realtime_signal_id(
          icon_action_factory_context_, WrapView(realtime_signal_name),
          &signal_id_out)));
  return RealtimeSignalId(signal_id_out);
}

}  // namespace intrinsic::icon
