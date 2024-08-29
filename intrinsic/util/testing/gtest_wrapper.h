// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
#define INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_

#ifndef ASSERT_OK
#define ASSERT_OK(expr) ASSERT_THAT(expr, ::absl_testing::IsOk())
#endif

#ifndef EXPECT_OK
#define EXPECT_OK(expr) EXPECT_THAT(expr, ::absl_testing::IsOk())
#endif

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "absl/status/status_matchers.h"
#include "internal/testing.h"
#include "intrinsic/util/testing/status_payload_matchers.h"
#include "protobuf-matchers/protocol-buffer-matchers.h"

namespace intrinsic {
namespace testing {

using ::intrinsic::testing::StatusHasGenericPayload;
using ::intrinsic::testing::StatusHasProtoPayload;
using ::protobuf_matchers::EqualsProto;
using ::protobuf_matchers::EquivToProto;
using ::protobuf_matchers::internal::ProtoCompare;
using ::protobuf_matchers::internal::ProtoComparison;
using ::protobuf_matchers::proto::Approximately;
using ::protobuf_matchers::proto::IgnoringFieldPaths;
using ::protobuf_matchers::proto::IgnoringRepeatedFieldOrdering;
using ::protobuf_matchers::proto::Partially;
using ::protobuf_matchers::proto::WhenDeserialized;
using ::protobuf_matchers::proto::WhenDeserializedAs;

}  // namespace testing
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
