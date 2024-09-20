// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/flatbuffers/flatbuffer_utils.h"

#include <gtest/gtest.h>

#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"

namespace intrinsic_fbs {
namespace {

TEST(FlatbufferArrayNumElementsTest, ReturnsCorrectNumElements) {
  EXPECT_EQ(FlatbufferArrayNumElements(&intrinsic::icon::SegmentInfo::names),
            intrinsic::icon::SegmentInfo{}.names()->size());
}

}  // namespace
}  // namespace intrinsic_fbs
