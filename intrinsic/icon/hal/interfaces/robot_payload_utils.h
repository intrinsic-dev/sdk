// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_ROBOT_PAYLOAD_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_ROBOT_PAYLOAD_UTILS_H_

#include <optional>

#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/robot_payload.fbs.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/world/robot_payload/robot_payload.h"
#include "intrinsic/world/robot_payload/robot_payload_base.h"

namespace intrinsic_fbs {

// Reserves and sets up FlatBuffer builder memory with RobotPayload. Default to
// a zero payload.
flatbuffers::Offset<RobotPayload> AddRobotPayload(
    flatbuffers::FlatBufferBuilder& fbb);

// Reserves and sets up FlatBuffer builder memory with OptionalPayload.
// By default, the payload is not set.
flatbuffers::Offset<OptionalRobotPayload> AddOptionalRobotPayload(
    flatbuffers::FlatBufferBuilder& fbb);

flatbuffers::DetachedBuffer BuildRobotPayload();

flatbuffers::DetachedBuffer BuildOptionalRobotPayload();

// Copies the data from a Robotpayload to the flatbuffer payload.
intrinsic::icon::RealtimeStatus CopyTo(
    const intrinsic::RobotPayloadBase& payload, RobotPayload& fbs_payload);

// Copies the data from a Robotpayload to the flatbuffer payload.
intrinsic::icon::RealtimeStatus CopyTo(
    const std::optional<intrinsic::RobotPayloadBase>& payload,
    OptionalRobotPayload& fbs_payload);

}  // namespace intrinsic_fbs

namespace intrinsic::icon {

// Copies the data from a flatbuffer payload to a RobotPayload.
RealtimeStatus CopyTo(const intrinsic_fbs::RobotPayload& fbs_payload,
                      intrinsic::RobotPayloadBase& payload);

// Copies the data from a flatbuffer optional payload to a optional
// RobotPayload.
RealtimeStatus CopyTo(const intrinsic_fbs::OptionalRobotPayload& fbs_payload,
                      std::optional<intrinsic::RobotPayloadBase>& payload);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_INTERFACES_ROBOT_PAYLOAD_UTILS_H_
