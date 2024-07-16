// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SIGNAL_ACCESS_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SIGNAL_ACCESS_H_

#include <utility>

#include "intrinsic/icon/control/c_api/c_realtime_signal_access.h"
#include "intrinsic/icon/control/realtime_signal_types.h"
#include "intrinsic/icon/utils/realtime_status_or.h"

namespace intrinsic::icon {

class IconRealtimeSignalAccess {
 public:
  IconRealtimeSignalAccess(
      XfaIconRealtimeSignalAccess* realtime_signal_access,
      XfaIconRealtimeSignalAccessVtable realtime_signal_access_vtable)
      : realtime_signal_access_(realtime_signal_access),
        realtime_signal_access_vtable_(
            std::move(realtime_signal_access_vtable)) {}

  RealtimeStatusOr<SignalValue> ReadSignal(RealtimeSignalId id);

 private:
  XfaIconRealtimeSignalAccess* realtime_signal_access_ = nullptr;
  XfaIconRealtimeSignalAccessVtable realtime_signal_access_vtable_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_REALTIME_SIGNAL_ACCESS_H_
