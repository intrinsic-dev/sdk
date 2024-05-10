// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_EIGEN_H_
#define INTRINSIC_UTIL_EIGEN_H_

#include <array>
#include <cfloat>
#include <cstddef>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "absl/log/check.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/repeated_field.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/math/pose3.h"

namespace intrinsic {

namespace eigen_details {
template <typename T>
void ToRepeatedDouble(const T& values,
                      google::protobuf::RepeatedField<double>* output) {
  output->Clear();
  output->Reserve(values.size());
  for (size_t i = 0; i < values.size(); ++i) {
    output->Add(values[i]);
  }
}

template <typename T>
T FromRepeatedDouble(const google::protobuf::RepeatedField<double>& values) {
  T result(values.size());
  for (size_t i = 0; i < values.size(); ++i) {
    result[i] = values[i];
  }

  return result;
}

template <typename S, typename T>
S ConvertVector(const T& values) {
  S result(values.size());
  for (size_t i = 0; i < values.size(); ++i) {
    result[i] = values[i];
  }

  return result;
}

}  // namespace eigen_details

// Convert a std::vector to a vectorNd
inline eigenmath::VectorNd VectorToVectorNd(const std::vector<double>& values) {
  return eigen_details::ConvertVector<eigenmath::VectorNd>(values);
}

// Convert a vectorNd to a std::vector
inline std::vector<double> VectorNdToVector(const eigenmath::VectorNd& values) {
  return eigen_details::ConvertVector<std::vector<double>>(values);
}

// Convert a vectorNd to a proto field of repeated doubles
inline void VectorNdToRepeatedDouble(
    const eigenmath::VectorNd& values,
    google::protobuf::RepeatedField<double>* output) {
  eigen_details::ToRepeatedDouble(values, output);
}

// Convert a std vector to vectorXd
inline eigenmath::VectorXd VectorToVectorXd(const std::vector<double>& values) {
  return eigen_details::ConvertVector<eigenmath::VectorXd>(values);
}

inline std::vector<double> VectorXdToVector(const eigenmath::VectorXd& values) {
  return eigen_details::ConvertVector<std::vector<double>>(values);
}

template <size_t T>
inline std::array<double, T> VectorXdToArray(
    const eigenmath::VectorXd& values) {
  CHECK_EQ(values.size(), T) << absl::StrFormat(
      "The size of the input VectorXd[%lu] should be equal to T[%lu]",
      values.size(), T);
  std::array<double, T> out_array;
  for (size_t i = 0; i < T; ++i) {
    out_array[i] = values[i];
  }
  return out_array;
}

template <size_t T>
inline eigenmath::VectorXd ArrayToVectorXd(std::array<double, T>& values) {
  return Eigen::Map<eigenmath::VectorXd>(values.data(), values.size());
}

// Convert a vectorXd to a proto repeated field double
inline void VectorXdToRepeatedDouble(
    const eigenmath::VectorXd& values,
    google::protobuf::RepeatedField<double>* output) {
  eigen_details::ToRepeatedDouble(values, output);
}

// Convert a proto double repeated field to a VectorXd
inline eigenmath::VectorXd RepeatedDoubleToVectorXd(
    const google::protobuf::RepeatedField<double>& values) {
  return eigen_details::FromRepeatedDouble<eigenmath::VectorXd>(values);
}

// Convert a repeated double to vector double
inline std::vector<double> RepeatedDoubleToVectorDouble(
    const google::protobuf::RepeatedField<double>& values) {
  return eigen_details::FromRepeatedDouble<std::vector<double>>(values);
}

// Convert a vector double to repeated double
inline void VectorDoubleToRepeatedDouble(
    const std::vector<double>& values,
    google::protobuf::RepeatedField<double>* output) {
  eigen_details::ToRepeatedDouble(values, output);
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_EIGEN_H_
