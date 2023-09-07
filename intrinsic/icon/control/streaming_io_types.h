// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_STREAMING_IO_TYPES_H_
#define INTRINSIC_ICON_CONTROL_STREAMING_IO_TYPES_H_

#include <any>
#include <cstdint>
#include <functional>

#include "absl/status/statusor.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/util/int_id.h"

namespace intrinsic::icon {

// Realtime Actions use StreamingInputIds to access streaming inputs. An Action
// factory saves IDs for any inputs. The Action instance can then use those IDs
// to access streaming inputs via the StreamingIoRealtimeAccess object that we
// pass to its Sense() method.
INTRINSIC_DEFINE_INT_ID_TYPE(StreamingInputId, int64_t);

// These definitions are used for storing streaming input parsers / output
// converters. Users do not interact with these definitions directly, but rather
// use wrappers that automatically convert from concrete proto message types to
// google::protobuf::Any and from realtime types to absl::any (and vice versa).
using GenericStreamingInputParser = std::function<absl::StatusOr<std::any>(
    const google::protobuf::Any &streaming_input)>;
using GenericStreamingOutputConverter =
    std::function<absl::StatusOr<google::protobuf::Any>(
        const std::any &streaming_output_any)>;

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_STREAMING_IO_TYPES_H_
