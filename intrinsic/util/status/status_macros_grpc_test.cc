// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_macros_grpc.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/util/status/status_builder.h"
#include "intrinsic/util/status/status_builder_grpc.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace {

using ::testing::AllOf;
using ::testing::Eq;
using ::testing::HasSubstr;

grpc::Status ReturnGrpcOk() { return grpc::Status::OK; }
absl::Status ReturnAbslOk() { return absl::OkStatus(); }

intrinsic::StatusBuilder ReturnOkBuilder() {
  return intrinsic::StatusBuilder(absl::OkStatus());
}

grpc::Status ReturnGrpcError(std::string_view msg) {
  return ToGrpcStatus(absl::UnknownError(msg));
}

absl::Status ReturnAbslError(std::string_view msg) {
  return absl::UnknownError(msg);
}

intrinsic::StatusBuilderGrpc ReturnErrorBuilder(std::string_view msg) {
  return intrinsic::StatusBuilderGrpc(
      intrinsic::StatusBuilder(absl::UnknownError(msg)));
}

absl::StatusOr<int> ReturnStatusOrValue(int v) { return v; }

absl::StatusOr<int> ReturnStatusOrError(std::string_view msg) {
  return absl::UnknownError(msg);
}

template <class... Args>
absl::StatusOr<std::tuple<Args...>> ReturnStatusOrTupleValue(Args&&... v) {
  return std::tuple<Args...>(std::forward<Args>(v)...);
}

template <class... Args>
absl::StatusOr<std::tuple<Args...>> ReturnStatusOrTupleError(
    std::string_view msg) {
  return absl::UnknownError(msg);
}

absl::StatusOr<std::unique_ptr<int>> ReturnStatusOrPtrValue(int v) {
  return std::make_unique<int>(v);
}

TEST(AssignOrReturnGrpc, Works) {
  auto func = []() -> grpc::Status {
    INTR_ASSIGN_OR_RETURN_GRPC(int value1, ReturnStatusOrValue(1));
    EXPECT_EQ(1, value1);
    INTR_ASSIGN_OR_RETURN_GRPC(const int value2, ReturnStatusOrValue(2));
    EXPECT_EQ(2, value2);
    INTR_ASSIGN_OR_RETURN_GRPC(const int& value3, ReturnStatusOrValue(3));
    EXPECT_EQ(3, value3);
    INTR_ASSIGN_OR_RETURN_GRPC([[maybe_unused]] int value4,
                               ReturnStatusOrError("EXPECTED"));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

// Note: GCC (as of 9.2.1) doesn't seem to support this trick.
#ifdef __clang__
TEST(AssignOrReturnGrpc, WorksWithCommasInType) {
  auto func = []() -> grpc::Status {
    INTR_ASSIGN_OR_RETURN_GRPC((std::tuple<int, int> t1),
                               ReturnStatusOrTupleValue(1, 1));
    EXPECT_EQ((std::tuple{1, 1}), t1);
    INTR_ASSIGN_OR_RETURN_GRPC(
        (const std::tuple<int, std::tuple<int, int>, int> t2),
        ReturnStatusOrTupleValue(1, std::tuple{1, 1}, 1));
    EXPECT_EQ((std::tuple{1, std::tuple{1, 1}, 1}), t2);
    INTR_ASSIGN_OR_RETURN_GRPC(
        ([[maybe_unused]] std::tuple<int, std::tuple<int, int>, int> t3),
        (ReturnStatusOrTupleError<int, std::tuple<int, int>, int>("EXPECTED")));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(AssignOrReturnGrpc, WorksWithStructureBindings) {
  auto func = []() -> grpc::Status {
    INTR_ASSIGN_OR_RETURN_GRPC(
        (const auto& [t1, t2, t3, t4, t5]),
        ReturnStatusOrTupleValue(std::tuple{1, 1}, 1, 2, 3, 4));
    EXPECT_EQ((std::tuple{1, 1}), t1);
    EXPECT_EQ(1, t2);
    EXPECT_EQ(2, t3);
    EXPECT_EQ(3, t4);
    EXPECT_EQ(4, t5);
    INTR_ASSIGN_OR_RETURN_GRPC([[maybe_unused]] int t6,
                               ReturnStatusOrError("EXPECTED"));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}
#endif

TEST(AssignOrReturnGrpc, WorksWithParenthesesAndDereference) {
  auto func = []() -> grpc::Status {
    int integer;
    int* pointer_to_integer = &integer;
    INTR_ASSIGN_OR_RETURN_GRPC((*pointer_to_integer), ReturnStatusOrValue(1));
    EXPECT_EQ(1, integer);
    INTR_ASSIGN_OR_RETURN_GRPC(*pointer_to_integer, ReturnStatusOrValue(2));
    EXPECT_EQ(2, integer);
    // Make the test where the order of dereference matters and treat the
    // parentheses.
    pointer_to_integer--;
    int** pointer_to_pointer_to_integer = &pointer_to_integer;
    INTR_ASSIGN_OR_RETURN_GRPC((*pointer_to_pointer_to_integer)[1],
                               ReturnStatusOrValue(3));
    EXPECT_EQ(3, integer);
    INTR_ASSIGN_OR_RETURN_GRPC([[maybe_unused]] int t1,
                               ReturnStatusOrError("EXPECTED"));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(AssignOrReturnGrpc, WorksWithAppend) {
  auto fail_test_if_called = []() -> std::string {
    ADD_FAILURE();
    return "FAILURE";
  };
  auto func = [&]() -> grpc::Status {
    [[maybe_unused]] int value;
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrValue(1),
                               _ << fail_test_if_called());
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrError("EXPECTED A"),
                               _ << "EXPECTED B");
    return ReturnGrpcOk();
  };

  EXPECT_THAT(func().error_message(),
              AllOf(HasSubstr("EXPECTED A"), HasSubstr("EXPECTED B")));
}

TEST(AssignOrReturnGrpc, WorksWithAdaptorFunc) {
  auto fail_test_if_called = [](intrinsic::StatusBuilderGrpc builder) {
    ADD_FAILURE();
    return builder;
  };
  auto adaptor = [](intrinsic::StatusBuilderGrpc builder) {
    return builder << "EXPECTED B";
  };
  auto func = [&]() -> grpc::Status {
    [[maybe_unused]] int value;
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrValue(1),
                               fail_test_if_called(_));
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrError("EXPECTED A"),
                               adaptor(_));
    return ReturnGrpcOk();
  };

  EXPECT_THAT(func().error_message(),
              AllOf(HasSubstr("EXPECTED A"), HasSubstr("EXPECTED B")));
}

// Note: GCC (as of 9.2.1) doesn't seem to support this trick.
#ifdef __clang__
TEST(AssignOrReturnGrpc, WorksWithThirdArgumentAndCommas) {
  auto fail_test_if_called = [](intrinsic::StatusBuilderGrpc builder) {
    ADD_FAILURE();
    return builder;
  };
  auto adaptor = [](intrinsic::StatusBuilderGrpc builder) {
    return builder << "EXPECTED B";
  };
  auto func = [&]() -> grpc::Status {
    INTR_ASSIGN_OR_RETURN_GRPC((const auto& [t1, t2, t3]),
                               ReturnStatusOrTupleValue(1, 2, 3),
                               fail_test_if_called(_));
    EXPECT_EQ(t1, 1);
    EXPECT_EQ(t2, 2);
    EXPECT_EQ(t3, 3);
    INTR_ASSIGN_OR_RETURN_GRPC(
        ([[maybe_unused]] const auto& [t4, t5, t6]),
        (ReturnStatusOrTupleError<int, int, int>("EXPECTED A")), adaptor(_));
    return ReturnGrpcOk();
  };

  EXPECT_THAT(func().error_message(),
              AllOf(HasSubstr("EXPECTED A"), HasSubstr("EXPECTED B")));
}
#endif

TEST(AssignOrReturnGrpc, WorksWithAppendIncludingLocals) {
  auto func = [&](const std::string& str) -> grpc::Status {
    int value;
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrError("EXPECTED A"),
                               _ << str);
    (void)value;
    return ReturnGrpcOk();
  };

  EXPECT_THAT(func("EXPECTED B").error_message(),
              AllOf(HasSubstr("EXPECTED A"), HasSubstr("EXPECTED B")));
}

TEST(AssignOrReturnGrpc, WorksForExistingVariable) {
  auto func = []() -> grpc::Status {
    int value = 1;
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrValue(2));
    EXPECT_EQ(2, value);
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrValue(3));
    EXPECT_EQ(3, value);
    INTR_ASSIGN_OR_RETURN_GRPC(value, ReturnStatusOrError("EXPECTED"));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(AssignOrReturnGrpc, UniquePtrWorks) {
  auto func = []() -> grpc::Status {
    INTR_ASSIGN_OR_RETURN_GRPC(std::unique_ptr<int> ptr,
                               ReturnStatusOrPtrValue(1));
    EXPECT_EQ(*ptr, 1);
    return ReturnGrpcError("EXPECTED");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(AssignOrReturnGrpc, UniquePtrWorksForExistingVariable) {
  auto func = []() -> grpc::Status {
    std::unique_ptr<int> ptr;
    INTR_ASSIGN_OR_RETURN_GRPC(ptr, ReturnStatusOrPtrValue(1));
    EXPECT_EQ(*ptr, 1);

    INTR_ASSIGN_OR_RETURN_GRPC(ptr, ReturnStatusOrPtrValue(2));
    EXPECT_EQ(*ptr, 2);
    return ReturnGrpcError("EXPECTED");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(ReturnIfErrorGrpc, Works) {
  auto func = []() -> grpc::Status {
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslOk());
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslOk());
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslError("EXPECTED"));
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(ReturnIfErrorGrpc, WorksWithBuilder) {
  auto func = []() -> grpc::Status {
    INTR_RETURN_IF_ERROR_GRPC(ReturnOkBuilder());
    INTR_RETURN_IF_ERROR_GRPC(ReturnOkBuilder());
    INTR_RETURN_IF_ERROR_GRPC(ReturnErrorBuilder("EXPECTED"));
    return ReturnErrorBuilder("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(ReturnIfErrorGrpc, WorksWithLambda) {
  auto func = []() -> grpc::Status {
    INTR_RETURN_IF_ERROR_GRPC([] { return ReturnAbslOk(); }());
    INTR_RETURN_IF_ERROR_GRPC([] { return ReturnAbslError("EXPECTED"); }());
    return ReturnGrpcError("ERROR");
  };

  EXPECT_THAT(func().error_message(), Eq("EXPECTED"));
}

TEST(ReturnIfErrorGrpc, WorksWithAppend) {
  auto fail_test_if_called = []() -> std::string {
    ADD_FAILURE();
    return "FAILURE";
  };
  auto func = [&]() -> grpc::Status {
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslOk()) << fail_test_if_called();
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslError("EXPECTED A")) << "EXPECTED B";
    return grpc::Status::OK;
  };

  EXPECT_THAT(func().error_message(),
              AllOf(HasSubstr("EXPECTED A"), HasSubstr("EXPECTED B")));
}

TEST(ReturnIfErrorGrpc, WorksWithVoidReturnAdaptor) {
  int code = 0;
  int phase = 0;
  auto adaptor = [&](grpc::Status status) -> void { code = phase; };
  auto func = [&]() -> void {
    phase = 1;
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslOk()).With(adaptor);
    phase = 2;
    INTR_RETURN_IF_ERROR_GRPC(ReturnAbslError("EXPECTED A")).With(adaptor);
    phase = 3;
  };

  func();
  EXPECT_EQ(phase, 2);
  EXPECT_EQ(code, 2);
}

}  // namespace
}  // namespace intrinsic
