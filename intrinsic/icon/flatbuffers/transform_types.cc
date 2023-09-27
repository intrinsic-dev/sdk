// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.


#include "intrinsic/icon/flatbuffers/transform_types.h"

#include <cstddef>
#include <cstring>
#include <vector>

#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/transform_types_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer CreateVectorNdBuffer(
    const std::vector<double>& data) {
  flatbuffers::FlatBufferBuilder builder;
  builder.Finish(CreateVectorNdDirect(builder, &data));
  return builder.Release();
}

flatbuffers::DetachedBuffer CreateVectorNdBuffer(size_t length) {
  std::vector<double> vector(length, 0);
  flatbuffers::FlatBufferBuilder builder;
  builder.Finish(CreateVectorNdDirect(builder, &vector));
  return builder.Release();
}

intrinsic_fbs::VectorNd* CopyToVectorNdBuffer(const std::vector<double>& data,
                                              void* buffer, size_t size) {
  if (!buffer) {
    return nullptr;
  }

  flatbuffers::FlatBufferBuilder builder;
  builder.Finish(CreateVectorNdDirect(builder, &data));

  if (size < builder.GetSize()) {
    return nullptr;
  }

  memcpy(buffer, builder.GetBufferPointer(), builder.GetSize());
  return flatbuffers::GetMutableRoot<VectorNd>(buffer);
}

flatbuffers::DetachedBuffer CreateWrenchBuffer() {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);
  builder.Finish(builder.CreateStruct(Wrench()));
  return builder.Release();
}

}  // namespace intrinsic_fbs
