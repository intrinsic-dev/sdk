// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/realtime_guard.h"

#include <gtest/gtest.h>

#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_stack_trace.h"

namespace intrinsic::icon {
namespace {

TEST(RealTimeGuardTest, DeathTest) {
  EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
  {
    InitRtStackTrace();
    RealTimeGuard guard;
    EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
    // Test nested RealTimeGuard.
    {
      RealTimeGuard guard;
      EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
    }
    // Test nested RealTimeGuard with LOGE reaction
    {
      RealTimeGuard guard(RealTimeGuard::Reaction::LOGE);
      INTRINSIC_RT_LOG(INFO) << "Ignore the following error, this is normal:";
      EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
    }
    // Test nested RealTimeGuard with IGNORE reaction
    {
      RealTimeGuard guard(RealTimeGuard::Reaction::IGNORE);
      EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
    }
    EXPECT_DEATH(INTRINSIC_ASSERT_NON_REALTIME(), "");
  }
  EXPECT_NO_THROW(INTRINSIC_ASSERT_NON_REALTIME());
}

}  // namespace
}  // namespace intrinsic::icon
