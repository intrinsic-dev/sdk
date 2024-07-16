// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_TESTING_ICON_REALTIME_SIGNAL_ACCESS_AND_MAP_FAKE_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_TESTING_ICON_REALTIME_SIGNAL_ACCESS_AND_MAP_FAKE_H_

#include <memory>
#include <string>

#include "absl/container/fixed_array.h"
#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/c_api/c_realtime_signal_access.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_realtime_signal_access.h"
#include "intrinsic/icon/control/realtime_signal_types.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/utils/realtime_status_or.h"

namespace intrinsic::icon {

class IconRealtimeSignalAccessAndMapFake {
 public:
  explicit IconRealtimeSignalAccessAndMapFake(
      const ::intrinsic_proto::icon::ActionSignature& signature);

  RealtimeStatusOr<SignalValue> ReadSignal(RealtimeSignalId id);

  absl::StatusOr<RealtimeSignalId> GetRealtimeSignalId(
      absl::string_view realtime_signal_name);

  // Creates an IconRealtimeSignalAccess that is backed by this
  // IconRealtimeSignalAccessAndMapFake. You can then pass that object to the
  // Sense() method of an Action under test.
  IconRealtimeSignalAccess MakeIconRealtimeSignalAccess();

 private:
  static XfaIconRealtimeSignalAccessVtable GetCApiVtable();

  const ::intrinsic_proto::icon::ActionSignature signature_;
  std::unique_ptr<absl::FixedArray<SignalValue>> signal_ids_;
  absl::flat_hash_map<std::string, RealtimeSignalId> signal_id_map_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_TESTING_ICON_REALTIME_SIGNAL_ACCESS_AND_MAP_FAKE_H_
