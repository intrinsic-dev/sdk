// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/proto/eigen_conversion.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <cstddef>

#include "absl/status/status.h"
#include "google/protobuf/repeated_field.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/matrix.pb.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic::icon {

namespace {

using ::intrinsic::testing::EqualsProto;
using ::intrinsic::testing::IsOkAndHolds;
using ::intrinsic::testing::StatusIs;
using ::testing::ElementsAreArray;
using ::testing::Eq;
using ::testing::HasSubstr;

TEST(IconEigenConversionTest, VectorNd) {
  eigenmath::VectorNd vector =
      (eigenmath::VectorNd(4) << -1, 0, 1, 2).finished();
  EXPECT_THAT(ToJointVecProto(vector), EqualsProto("joints: [-1, 0, 1, 2]"));
  EXPECT_THAT(FromProto(ToJointVecProto(vector)), IsOkAndHolds(Eq(vector)));
  eigenmath::VectorNd empty_vector(0);
  EXPECT_THAT(FromProto(ToJointVecProto(empty_vector)),
              IsOkAndHolds(Eq(empty_vector)));
}

TEST(IconEigenConversionTest, ToJointStatePVP) {
  eigenmath::VectorNd vector =
      (eigenmath::VectorNd(4) << -1, 0, 1, 2).finished();

  EXPECT_THAT(ToJointStatePVProtoWithZeroVel(vector),
              EqualsProto(R"pb(position: -1
                               position: 0
                               position: 1
                               position: 2
                               velocity: 0
                               velocity: 0
                               velocity: 0
                               velocity: 0)pb"));
}

TEST(IconEigenConversionTest, VectorNdLimit) {
  intrinsic_proto::icon::JointVec proto;
  for (int i = 0; i < eigenmath::MAX_EIGEN_VECTOR_SIZE + 1; ++i) {
    proto.add_joints(1);
  }
  EXPECT_THAT(FromProto(proto), StatusIs(absl::StatusCode::kInvalidArgument,
                                         HasSubstr("VectorNd")));
}

TEST(IconEigenConversionTest, VectorXdUtils) {
  eigenmath::VectorXd value(6);
  for (size_t i = 0; i < value.size(); ++i) {
    value[i] = i + 1;
  }

  google::protobuf::RepeatedField<double> rpt_field;
  VectorXdToRepeatedDouble(value, &rpt_field);

  eigenmath::VectorXd decoded_value = RepeatedDoubleToVectorXd(rpt_field);

  EXPECT_EQ(value, decoded_value);
}

TEST(IconEigenConversionTest, VectorNdConversionOk) {
  google::protobuf::RepeatedField<double> rpt_field;
  for (size_t i = 0; i < eigenmath::MAX_EIGEN_VECTOR_SIZE; ++i) {
    rpt_field.Add(i + 1);
  }

  ASSERT_OK_AND_ASSIGN(eigenmath::VectorNd decoded_value,
                       RepeatedDoubleToVectorNd(rpt_field));

  EXPECT_THAT(decoded_value, ElementsAreArray(rpt_field));
}

TEST(IconEigenConversionTest, VectorNdConversionTooLargeError) {
  google::protobuf::RepeatedField<double> rpt_field;
  for (size_t i = 0; i < eigenmath::MAX_EIGEN_VECTOR_SIZE + 1; ++i) {
    rpt_field.Add(i + 1);
  }

  EXPECT_THAT(RepeatedDoubleToVectorNd(rpt_field),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(IconEigenConversionTest, Matrix6dFromProtoFailsWrongSize) {
  intrinsic_proto::icon::Matrix6d proto;
  proto.mutable_data()->Resize(35, 0);
  EXPECT_THAT(FromProto(proto), StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(IconEigenConversionTest, MatrixToFromProtoSucceeds) {
  eigenmath::Matrix6d matrix;
  for (int i = 0; i < 6; ++i) {
    for (int j = 0; j < 6; ++j) {
      matrix(i, j) = (i + 1) * (j + 6);
    }
  }
  ASSERT_OK_AND_ASSIGN(eigenmath::Matrix6d result, FromProto(ToProto(matrix)));
  EXPECT_EQ(matrix, result);
}

TEST(IconEigenConversionTest, Vector6dToFromProtoSucceeds) {
  eigenmath::Vector6d vector;
  vector << 1, 2, 3, 4, 5, 6;
  EXPECT_EQ(vector, FromProto(ToProto(vector)));
}

}  // namespace

}  // namespace intrinsic::icon
