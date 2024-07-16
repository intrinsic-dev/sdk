// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/c_api/external_action_api/icon_realtime_signal_access.h"

#include "intrinsic/icon/control/c_api/c_realtime_signal_access.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_types.h"
#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"
#include "intrinsic/icon/control/c_api/convert_c_types.h"
#include "intrinsic/icon/control/realtime_signal_types.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/icon/utils/realtime_status_or.h"

namespace intrinsic::icon {

RealtimeStatusOr<SignalValue> IconRealtimeSignalAccess::ReadSignal(
    RealtimeSignalId id) {
  XfaIconSignalValue signal_value;
  XfaIconRealtimeStatus read_signal_status =
      realtime_signal_access_vtable_.read_signal(realtime_signal_access_,
                                                 id.value(), &signal_value);
  INTRINSIC_RT_RETURN_IF_ERROR(ToRealtimeStatus(read_signal_status));
  return Convert(signal_value);
}

}  // namespace intrinsic::icon
