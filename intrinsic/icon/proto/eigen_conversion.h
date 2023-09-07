// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_PROTO_EIGEN_CONVERSION_H_
#define INTRINSIC_ICON_PROTO_EIGEN_CONVERSION_H_

#include <cstddef>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "google/protobuf/repeated_field.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/icon/proto/joint_space.pb.h"
#include "intrinsic/icon/proto/matrix.pb.h"

namespace intrinsic::icon {

// Converts a VectorNd to a JointVec proto.
intrinsic_proto::icon::JointVec ToJointVecProto(const eigenmath::VectorNd& v);

// Converts a VectorNd to a JointStatePV proto with zero velocities.
intrinsic_proto::icon::JointStatePV ToJointStatePVProtoWithZeroVel(
    const eigenmath::VectorNd& v);

// Converts a JointVec proto to VectorNd.
// Returns kInvalidArgument if size does not fit into VectorNd.
absl::StatusOr<eigenmath::VectorNd> FromProto(
    const intrinsic_proto::icon::JointVec& proto);

namespace details {
template <typename T>
void ToRepeatedDouble(const T& values,
                      google::protobuf::RepeatedField<double>* output) {
  output->Clear();
  output->Reserve(static_cast<size_t>(values.size()));
  for (size_t i = 0; i < static_cast<size_t>(values.size()); ++i) {
    output->Add(values[i]);
  }
}

template <typename T>
T FromRepeatedDouble(const google::protobuf::RepeatedField<double>& values) {
  T result(values.size());
  for (size_t i = 0; i < static_cast<size_t>(values.size()); ++i) {
    result[i] = values[i];
  }

  return result;
}

}  // namespace details

// Converts a VectorXd to a proto repeated field double.
inline void VectorXdToRepeatedDouble(
    const eigenmath::VectorXd& values,
    google::protobuf::RepeatedField<double>* output) {
  details::ToRepeatedDouble(values, output);
}

// Converts a VectorNd to a proto repeated field double.
inline void VectorNdToRepeatedDouble(
    const eigenmath::VectorNd& values,
    google::protobuf::RepeatedField<double>* output) {
  details::ToRepeatedDouble(values, output);
}

// Converts a proto double repeated field to a VectorXd.
inline eigenmath::VectorXd RepeatedDoubleToVectorXd(
    const google::protobuf::RepeatedField<double>& values) {
  return details::FromRepeatedDouble<eigenmath::VectorXd>(values);
}

// Converts a proto double repeated field to a VectorNd.
inline absl::StatusOr<eigenmath::VectorNd> RepeatedDoubleToVectorNd(
    const google::protobuf::RepeatedField<double>& values) {
  if (values.size() > eigenmath::MAX_EIGEN_VECTOR_SIZE) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Size of values ", values.size(), " is too large, must be less than ",
        eigenmath::MAX_EIGEN_VECTOR_SIZE, " to convert to VectorNd"));
  }
  return details::FromRepeatedDouble<eigenmath::VectorNd>(values);
}

// Converts a Vector3d to a proto repeated field of doubles (with 3 elements).
inline void Vector3dToRepeatedDouble(
    const eigenmath::Vector3d& values,
    google::protobuf::RepeatedField<double>* output) {
  details::ToRepeatedDouble(values, output);
}

// Converts a proto repeated field of doubles to a Vector3d.
//
// Returns InvalidArgumentError if the repeated field does not have three
// elements.
inline absl::StatusOr<eigenmath::Vector3d> RepeatedDoubleToVector3d(
    const google::protobuf::RepeatedField<double>& values) {
  if (values.size() != 3) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Cannot convert repeated double field to Vector3d; expected size 3, "
        "but size is ",
        values.size(), "; values=[", absl::StrJoin(values, ", "), "]"));
  }
  return details::FromRepeatedDouble<eigenmath::Vector3d>(values);
}

// Converts a 6x6 matrix to a proto.
intrinsic_proto::icon::Matrix6d ToProto(const eigenmath::Matrix6d& matrix);

// Converts a 6x6 matrix proto to an eigenmath::Matrix6d.
//
// Returns InvalidArgumentError if the `data` field does not have 36 elements.
absl::StatusOr<eigenmath::Matrix6d> FromProto(
    const intrinsic_proto::icon::Matrix6d& proto);

// Converts an eigenmath::Vector6d to a CartVec6 proto.
intrinsic_proto::icon::CartVec6 ToProto(const eigenmath::Vector6d& vector);

// Converts a CartVec6 proto to an eigenmath::Vector6d.
eigenmath::Vector6d FromProto(const intrinsic_proto::icon::CartVec6& proto);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_PROTO_EIGEN_CONVERSION_H_
