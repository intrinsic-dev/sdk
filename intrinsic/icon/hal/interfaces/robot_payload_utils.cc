// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/robot_payload_utils.h"

#include <optional>
#include <utility>

#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/parts/realtime_robot_payload.h"
#include "intrinsic/icon/flatbuffers/control_types_copy.h"
#include "intrinsic/icon/flatbuffers/matrix_types.fbs.h"
#include "intrinsic/icon/flatbuffers/matrix_types_utils.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/icon/hal/interfaces/robot_payload.fbs.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/world/robot_payload/robot_payload.h"
#include "intrinsic/world/robot_payload/robot_payload_base.h"

namespace intrinsic_fbs {

flatbuffers::Offset<RobotPayload> AddRobotPayload(
    flatbuffers::FlatBufferBuilder& fbb) {
  fbb.ForceDefaults(true);
  intrinsic::RobotPayloadBase payload;
  Transform tip_t_cog;
  CopyTo(&tip_t_cog, payload.tip_t_cog());

  Matrix3d inertia;
  CopyTo(payload.inertia(), inertia);

  RobotPayloadBuilder builder(fbb);
  builder.add_mass_kg(payload.mass());
  builder.add_tip_t_cog(&tip_t_cog);
  builder.add_inertia(&inertia);
  return builder.Finish();
}

flatbuffers::Offset<OptionalRobotPayload> AddOptionalRobotPayload(
    flatbuffers::FlatBufferBuilder& fbb) {
  fbb.ForceDefaults(true);

  flatbuffers::Offset<RobotPayload> payload = AddRobotPayload(fbb);

  OptionalRobotPayloadBuilder builder(fbb);
  builder.add_has_value(false);
  builder.add_value(payload);
  return builder.Finish();
}

flatbuffers::DetachedBuffer BuildRobotPayload() {
  flatbuffers::FlatBufferBuilder fbb;
  fbb.Finish(AddRobotPayload(fbb));
  return fbb.Release();
}

flatbuffers::DetachedBuffer BuildOptionalRobotPayload() {
  flatbuffers::FlatBufferBuilder fbb;
  fbb.Finish(AddOptionalRobotPayload(fbb));
  return fbb.Release();
}

intrinsic::icon::RealtimeStatus CopyTo(
    const intrinsic::RobotPayloadBase& payload,
    intrinsic_fbs::RobotPayload& fbs_payload) {
  if (!fbs_payload.mutate_mass_kg(payload.mass())) {
    return intrinsic::icon::FailedPreconditionError(
        "mass field does not exist.");
  }
  CopyTo(fbs_payload.mutable_tip_t_cog(), payload.tip_t_cog());
  CopyTo(payload.inertia(), *fbs_payload.mutable_inertia());
  return intrinsic::icon::OkStatus();
}

intrinsic::icon::RealtimeStatus CopyTo(
    const std::optional<intrinsic::RobotPayloadBase>& payload,
    OptionalRobotPayload& fbs_payload) {
  if (!fbs_payload.mutate_has_value(payload.has_value())) {
    return intrinsic::icon::FailedPreconditionError(
        "has_value field does not exist.");
  }
  INTRINSIC_RT_RETURN_IF_ERROR(
      CopyTo(payload.value_or(intrinsic::RobotPayloadBase{}),
             *fbs_payload.mutable_value()));
  return intrinsic::icon::OkStatus();
}

}  // namespace intrinsic_fbs

namespace intrinsic::icon {

RealtimeStatus CopyTo(const intrinsic_fbs::RobotPayload& fbs_payload,
                      intrinsic::RobotPayloadBase& payload) {
  Pose3d tip_t_cog;
  intrinsic_fbs::CopyTo(&tip_t_cog, *fbs_payload.tip_t_cog());

  INTRINSIC_RT_ASSIGN_OR_RETURN(
      payload,
      intrinsic::icon::RealtimeRobotPayload::Create(
          fbs_payload.mass_kg(), tip_t_cog,
          intrinsic_fbs::ViewAs<eigenmath::Matrix3d>(*fbs_payload.inertia())));
  return OkStatus();
}

RealtimeStatus CopyTo(const intrinsic_fbs::OptionalRobotPayload& fbs_payload,
                      std::optional<intrinsic::RobotPayloadBase>& payload) {
  if (!fbs_payload.has_value()) {
    payload.reset();
    return OkStatus();
  }
  RobotPayload new_payload;
  INTRINSIC_RT_RETURN_IF_ERROR(CopyTo(*fbs_payload.value(), new_payload));
  payload.emplace(std::move(new_payload));
  return OkStatus();
}

}  // namespace intrinsic::icon
