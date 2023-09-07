// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/external_action_api/testing/action_test_helper.h"

#include <string>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/c_api/external_action_api/testing/icon_streaming_io_registry_fake.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

ActionTestHelper::ActionTestHelper(
    double control_frequency_hz,
    const ::intrinsic_proto::icon::ActionSignature& signature,
    absl::string_view server_name)
    : streaming_io_registry_(signature) {
  server_config_.set_frequency_hz(control_frequency_hz);
  server_config_.set_name(std::string(server_name));
}

RealtimeStatus ActionTestHelper::EnterAction(IconActionInterface& action) {
  return action.OnEnter(slot_map_.MakeIconConstRealtimeSlotMap());
}

RealtimeStatus ActionTestHelper::SenseAndControlAction(
    IconActionInterface& action) {
  auto streaming_io_access = streaming_io_registry_.MakeIconStreamingIoAccess();
  if (RealtimeStatus s = action.Sense(slot_map_.MakeIconConstRealtimeSlotMap(),
                                      streaming_io_access);
      !s.ok()) {
    return s;
  }
  auto mutable_rt_slot_map = slot_map_.MakeIconRealtimeSlotMap();
  return action.Control(mutable_rt_slot_map);
}

}  // namespace intrinsic::icon
