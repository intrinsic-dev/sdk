// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/eigen.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <string>
#include <vector>

#include "google/protobuf/repeated_field.h"
#include "intrinsic/eigenmath/rotation_utils.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {

TEST(UtilEigen, VectorXdUtils) {
  eigenmath::VectorXd value(6);
  for (size_t i = 0; i < value.size(); ++i) {
    value[i] = i + 1;
  }

  google::protobuf::RepeatedField<double> rpt_field;
  VectorXdToRepeatedDouble(value, &rpt_field);

  eigenmath::VectorXd decoded_value = RepeatedDoubleToVectorXd(rpt_field);

  EXPECT_EQ(value, decoded_value);

  std::vector<double> vector_value = VectorXdToVector(value);
  EXPECT_EQ(vector_value.size(), value.size());
  EXPECT_EQ(value, VectorToVectorXd(vector_value));

  std::array<double, 6> array_value = VectorXdToArray<6>(value);
  EXPECT_EQ(array_value.size(), value.size());
  EXPECT_EQ(value, ArrayToVectorXd(array_value));
}

TEST(UtilEigen, VectorUtils) {
  std::vector<double> value(6);
  for (size_t i = 0; i < value.size(); ++i) {
    value[i] = i + 1;
  }

  google::protobuf::RepeatedField<double> rpt_field;
  VectorDoubleToRepeatedDouble(value, &rpt_field);

  std::vector<double> decoded_value = RepeatedDoubleToVectorDouble(rpt_field);

  EXPECT_EQ(value, decoded_value);
}

}  // namespace intrinsic
