// Copyright 2023 Intrinsic Innovation LLC


#include "intrinsic/icon/flatbuffers/transform_view.h"

#include "flatbuffers/base.h"
#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/vector.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"

namespace intrinsic_fbs {

// Point <-> Eigen::Vector3d

template <>
Eigen::Map<Eigen::Vector3d> ViewAs(Point *point) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Point memory layout is equivalent to Eigen::Vector3d raw
  // data
  return Eigen::Map<Eigen::Vector3d>(reinterpret_cast<double *>(point));
}

template <>
const Eigen::Map<const Eigen::Vector3d> ViewAs(const Point &point) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Point memory layout is equivalent to Eigen::Vector3d raw
  // data
  return Eigen::Map<const Eigen::Vector3d>(
      reinterpret_cast<const double *>(&point));
}

template <>
Point *ViewAs(Eigen::Vector3d *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Point memory layout is equivalent to Eigen::Vector3d raw
  // data
  return reinterpret_cast<Point *>(vector->data());
}

template <>
const Point *ViewAs(const Eigen::Vector3d &vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Point memory layout is equivalent to Eigen::Vector3d raw
  // data
  return reinterpret_cast<const Point *>(vector.data());
}

// Rotation <-> Quaterniond

template <>
Eigen::Map<Eigen::Quaterniond> ViewAs(Rotation *rotation) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Rotation memory layout is equivalent to Eigen::Quaterniond
  // raw data
  return Eigen::Map<Eigen::Quaterniond>(reinterpret_cast<double *>(rotation));
}

template <>
const Eigen::Map<const Eigen::Quaterniond> ViewAs(const Rotation &rotation) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Rotation memory layout is equivalent to Eigen::Quaterniond
  // raw data
  return Eigen::Map<const Eigen::Quaterniond>(
      reinterpret_cast<const double *>(&rotation));
}

template <>
Rotation *ViewAs(Eigen::Quaterniond *quaternion) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Rotation memory layout is equivalent to Eigen::Quaterniond
  // raw data
  return reinterpret_cast<Rotation *>(quaternion->coeffs().data());
}

template <>
const Rotation *ViewAs(const Eigen::Quaterniond &quaternion) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Rotation memory layout is equivalent to Eigen::Quaterniond
  // raw data
  return reinterpret_cast<const Rotation *>(quaternion.coeffs().data());
}

// Twist <-> intrinsic::eigenmath::Vector6d

template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Twist *twist) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Twist memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return Eigen::Map<intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<double *>(twist));
}

template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Twist &twist) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Twist memory layout is equivalent to Eigen::Vector6d raw
  // data
  return Eigen::Map<const intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<const double *>(&twist));
}

template <>
Twist *ViewAs(intrinsic::eigenmath::Vector6d *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Twist memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return reinterpret_cast<Twist *>(vector->data());
}

// Acceleration <-> intrinsic::eigenmath::Vector6d

template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Acceleration *acceleration) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Acceleration memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return Eigen::Map<intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<double *>(acceleration));
}

template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Acceleration &acceleration) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Acceleration memory layout is equivalent to Eigen::Vector6d
  // raw data
  return Eigen::Map<const intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<const double *>(&acceleration));
}

template <>
Acceleration *ViewAs(intrinsic::eigenmath::Vector6d *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Acceleration memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return reinterpret_cast<Acceleration *>(vector->data());
}

// Jerk <-> intrinsic::eigenmath::Vector6d

template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Jerk *jerk) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Jerk memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return Eigen::Map<intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<double *>(jerk));
}

template <>
Jerk *ViewAs(intrinsic::eigenmath::Vector6d *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Jerk memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return reinterpret_cast<Jerk *>(vector->data());
}

// Wrench <-> intrinsic::eigenmath::Vector6d

template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Wrench *wrench) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Wrench memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return Eigen::Map<intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<double *>(wrench));
}

template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Wrench *wrench) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Wrench memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return Eigen::Map<const intrinsic::eigenmath::Vector6d>(
      reinterpret_cast<const double *>(wrench));
}

template <>
Wrench *ViewAs(intrinsic::eigenmath::Vector6d *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::Wrench memory layout is equivalent to
  // intrinsic::eigenmath::Vector6d raw data
  return reinterpret_cast<Wrench *>(vector->data());
}

// VectorNd <-> Eigen::VectorXd / double

template <>
Eigen::Map<Eigen::VectorXd> ViewAs(VectorNd *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::VectorNd memory layout is equivalent to Eigen::VectorXd raw
  // data
  return Eigen::Map<Eigen::VectorXd>(vector->mutable_data()->data(),
                                     vector->data()->size());
}

template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(VectorNd *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::VectorNd memory layout is equivalent to
  // intrinsic::eigenmath::VectorNd raw data
  return Eigen::Map<intrinsic::eigenmath::VectorNd>(
      vector->mutable_data()->data(), vector->data()->size());
}

template <>
const Eigen::Map<const intrinsic::eigenmath::VectorNd> ViewAs(
    const VectorNd *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // intrinsic_fbs::VectorNd memory layout is equivalent to
  // intrinsic::eigenmath::VectorNd raw data
  return Eigen::Map<const intrinsic::eigenmath::VectorNd>(
      vector->data()->data(), vector->data()->size());
}

template <>
double *ViewAs(Eigen::VectorXd *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  // there is no direct memory layout from Eigen::VectorXd to
  // intrinsic_fbs::VectorNd
  return reinterpret_cast<double *>(vector->data());
}

// Generic DetachedBuffer <-> Eigen

template <>
Eigen::Map<Eigen::VectorXd> ViewAs(flatbuffers::DetachedBuffer *buffer) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  VectorNd *vector_fbs =
      flatbuffers::GetMutableRoot<intrinsic_fbs::VectorNd>(buffer->data());
  return Eigen::Map<Eigen::VectorXd>(vector_fbs->mutable_data()->data(),
                                     vector_fbs->data()->size());
}

template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(
    flatbuffers::DetachedBuffer *buffer) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  VectorNd *vector_fbs =
      flatbuffers::GetMutableRoot<intrinsic_fbs::VectorNd>(buffer->data());
  return Eigen::Map<intrinsic::eigenmath::VectorNd>(
      vector_fbs->mutable_data()->data(), vector_fbs->data()->size());
}

template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(
    ::flatbuffers::Vector<double> *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  return Eigen::Map<intrinsic::eigenmath::VectorNd>(vector->data(),
                                                    vector->size());
}

template <>
Eigen::Map<const intrinsic::eigenmath::VectorNd> ViewAs(
    const ::flatbuffers::Vector<double> *vector) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  return Eigen::Map<const intrinsic::eigenmath::VectorNd>(vector->data(),
                                                          vector->size());
}

}  // namespace intrinsic_fbs
