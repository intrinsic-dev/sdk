// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
#define INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "google/fhir/testutil/proto_matchers.h"
#include "internal/testing.h"

namespace intrinsic {
namespace testing {
using cel::internal::IsOk;
using cel::internal::IsOkAndHolds;
using cel::internal::StatusIs;
using google::fhir::testutil::EqualsProto;
using google::fhir::testutil::internal::ProtoCompare;
using google::fhir::testutil::internal::ProtoComparison;
}  // namespace testing

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_TESTING_GTEST_WRAPPER_H_
