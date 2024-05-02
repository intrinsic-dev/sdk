// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
#define INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "internal/testing.h"
#include "protobuf-matchers/protocol-buffer-matchers.h"

namespace intrinsic {
namespace testing {
using cel::internal::IsOk;
using cel::internal::IsOkAndHolds;
using cel::internal::StatusIs;
using ::protobuf_matchers::EqualsProto;
using ::protobuf_matchers::EquivToProto;
using ::protobuf_matchers::internal::ProtoCompare;
using ::protobuf_matchers::internal::ProtoComparison;
using ::protobuf_matchers::proto::Approximately;
using ::protobuf_matchers::proto::Partially;
using ::protobuf_matchers::proto::WhenDeserialized;
}  // namespace testing

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
