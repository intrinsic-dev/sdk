// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/external_action_api/testing/icon_action_factory_context_fake.h"

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/c_api/c_action_factory_context.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_action_factory_context.h"
#include "intrinsic/icon/control/c_api/wrappers/string_wrapper.h"
#include "intrinsic/icon/control/streaming_io_types.h"

namespace intrinsic::icon {

IconActionFactoryContext
IconActionFactoryContextFake::MakeIconActionFactoryContext() {
  return IconActionFactoryContext(
      reinterpret_cast<XfaIconActionFactoryContext*>(this), GetCApiVtable());
}

XfaIconActionFactoryContextVtable
IconActionFactoryContextFake::GetCApiVtable() {
  // The lambdas defined in this method are implicitly friends of
  // IconActionFactoryContextFake, so they can access its private members.
  return {
      .destroy_string = &DestroyString,
      .server_config =
          [](const XfaIconActionFactoryContext* self) -> XfaIconString* {
        return Wrap(reinterpret_cast<const IconActionFactoryContextFake*>(self)
                        ->server_config_.SerializeAsString());
      },
      .get_slot_info =
          [](XfaIconActionFactoryContext* self, XfaIconStringView slot_name,
             XfaIconSlotInfo* slot_info_out) -> XfaIconRealtimeStatus {
        absl::string_view slot_name_view(slot_name.data, slot_name.size);
        auto* fake = reinterpret_cast<IconActionFactoryContextFake*>(self);
        auto slot_info = fake->slot_map_.GetSlotInfoForSlot(slot_name_view);
        if (!slot_info.ok()) {
          return FromAbslStatus(slot_info.status());
        }
        slot_info_out->realtime_slot_id = slot_info->slot_id.value();
        slot_info_out->part_config_buffer =
            Wrap(slot_info->config.SerializeAsString());
        return FromAbslStatus(absl::OkStatus());
      },
      .add_streaming_input_parser =
          [](XfaIconActionFactoryContext* self, XfaIconStringView input_name,
             XfaIconStringView input_proto_message_type_name,
             XfaIconStreamingInputParserFnInstance parser,
             uint64_t* streaming_input_id_out) -> XfaIconRealtimeStatus {
        auto* fake = reinterpret_cast<IconActionFactoryContextFake*>(self);
        absl::string_view input_name_view(input_name.data, input_name.size);
        absl::string_view input_proto_message_type_name_view(
            input_proto_message_type_name.data,
            input_proto_message_type_name.size);
        absl::StatusOr<StreamingInputId> input_id =
            fake->streaming_io_registry_.AddInputParser(
                input_name_view, input_proto_message_type_name_view, parser);
        if (!input_id.ok()) {
          return FromAbslStatus(input_id.status());
        }
        *streaming_input_id_out = input_id->value();
        return FromAbslStatus(absl::OkStatus());
      },
      .add_streaming_output_converter =
          [](XfaIconActionFactoryContext* self,
             XfaIconStringView output_proto_message_type_name,
             size_t realtime_type_size,
             XfaIconStreamingOutputConverterFnInstance converter)
          -> XfaIconRealtimeStatus {
        auto fake = reinterpret_cast<IconActionFactoryContextFake*>(self);
        return FromAbslStatus(fake->streaming_io_registry_.AddOutputConverter(
            absl::string_view(output_proto_message_type_name.data,
                              output_proto_message_type_name.size),
            converter));
      },
  };
}
}  // namespace intrinsic::icon
