// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/imu_utils.h"

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/icon/hal/interfaces/imu.fbs.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildImuStatus() {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  ImuStatusBuilder status_builder(builder);

  intrinsic_fbs::Point linear_acceleration;
  status_builder.add_linear_acceleration(&linear_acceleration);

  intrinsic_fbs::Point angular_velocity;
  status_builder.add_angular_velocity(&angular_velocity);

  intrinsic_fbs::Rotation orientation;
  orientation.mutate_qw(1.0);
  status_builder.add_orientation(&orientation);

  auto status = status_builder.Finish();
  builder.Finish(status);

  return builder.Release();
}

}  // namespace intrinsic_fbs
