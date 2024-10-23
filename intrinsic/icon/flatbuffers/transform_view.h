// Copyright 2023 Intrinsic Innovation LLC


#ifndef INTRINSIC_ICON_FLATBUFFERS_TRANSFORM_VIEW_H_
#define INTRINSIC_ICON_FLATBUFFERS_TRANSFORM_VIEW_H_

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/vector.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/icon/flatbuffers/transform_types.h"

#define MUTATE_VECTORND(message, field)                      \
  ::intrinsic_fbs::ViewAs<::intrinsic::eigenmath::VectorNd>( \
      (message)->mutable_##field())

#define VIEW_VECTORND(message, field) \
  ::intrinsic_fbs::ViewAs<::intrinsic::eigenmath::VectorNd>((message)->field())

namespace intrinsic_fbs {

// Point <-> Eigen::Vector3d

// Returns a reference to memory stored in Point as a
// Eigen::Map<Eigen::Vector3d>
template <typename T>
Eigen::Map<T> ViewAs(Point *point);
template <>
Eigen::Map<Eigen::Vector3d> ViewAs(Point *point);

template <typename T>
const Eigen::Map<const T> ViewAs(const Point &point);
template <>
const Eigen::Map<const Eigen::Vector3d> ViewAs(const Point &point);

// Returns a pointer to the raw memory stored in Eigen::Vector3d as
// Point.
template <typename T>
T *ViewAs(Eigen::Vector3d *vector);
template <>
Point *ViewAs(Eigen::Vector3d *vector);

template <typename T>
const T *ViewAs(const Eigen::Vector3d &vector);
template <>
const Point *ViewAs(const Eigen::Vector3d &vector);

// Rotation <-> Quaterniond

// Returns a reference to memory stored in Rotation as a
// Eigen::Map<Eigen::Quaterniond>
template <typename T>
Eigen::Map<T> ViewAs(Rotation *rotation);
template <>
Eigen::Map<Eigen::Quaterniond> ViewAs(Rotation *rotation);

template <typename T>
const Eigen::Map<const T> ViewAs(const Rotation &rotation);
template <>
const Eigen::Map<const Eigen::Quaterniond> ViewAs(const Rotation &rotation);

// Returns a pointer to the raw memory stored in Eigen::Quaterniond as
// Rotation.
template <typename T>
T *ViewAs(Eigen::Quaterniond *quaternion);
template <>
Rotation *ViewAs(Eigen::Quaterniond *quaternion);

template <typename T>
const T *ViewAs(const Eigen::Quaterniond &quaternion);
template <>
const Rotation *ViewAs(const Eigen::Quaterniond &quaternion);

// Twist <-> intrinsic::eigenmath::Vector6d

// Returns a reference to memory stored in Twist as a
// Eigen::Map<intrinsic::eigenmath::Vector6d>
template <typename T>
Eigen::Map<T> ViewAs(Twist *twist);
template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Twist *twist);

template <typename T>
const Eigen::Map<const T> ViewAs(const Twist &twist);
template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Twist &twist);

// Returns a pointer to the raw memory stored in intrinsic::eigenmath::Vector6d
// as Twist.
template <typename T>
T *ViewAs(intrinsic::eigenmath::Vector6d *vector);
template <>
Twist *ViewAs(intrinsic::eigenmath::Vector6d *vector);

// Acceleration <-> intrinsic::eigenmath::Vector6d

// Returns a reference to memory stored in Acceleration as a
// Eigen::Map<intrinsic::eigenmath::Vector6d>
template <typename T>
Eigen::Map<T> ViewAs(Acceleration *acceleration);
template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Acceleration *acceleration);

template <typename T>
const Eigen::Map<const T> ViewAs(const Acceleration &acceleration);
template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Acceleration &acceleration);

// Returns a pointer to the raw memory stored in intrinsic::eigenmath::Vector6d
// as Acceleration.
template <typename T>
T *ViewAs(intrinsic::eigenmath::Vector6d *vector);
template <>
Acceleration *ViewAs(intrinsic::eigenmath::Vector6d *vector);

// Jerk <-> intrinsic::eigenmath::Vector6d

// Returns a reference to memory stored in Jerk as a
// Eigen::Map<intrinsic::eigenmath::Vector6d>
template <typename T>
Eigen::Map<T> ViewAs(Jerk *jerk);
template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Jerk *jerk);

// Returns a pointer to the raw memory stored in intrinsic::eigenmath::Vector6d
// as Jerk.
template <typename T>
T *ViewAs(intrinsic::eigenmath::Vector6d *vector);
template <>
Jerk *ViewAs(intrinsic::eigenmath::Vector6d *vector);

// Wrench <-> intrinsic::eigenmath::Vector6d

// Returns a reference to memory stored in Wrench as a
// Eigen::Map<intrinsic::eigenmath::Vector6d>
template <typename T>
Eigen::Map<T> ViewAs(Wrench *wrench);
template <>
Eigen::Map<intrinsic::eigenmath::Vector6d> ViewAs(Wrench *wrench);

template <typename T>
const Eigen::Map<const T> ViewAs(const Wrench *wrench);
template <>
const Eigen::Map<const intrinsic::eigenmath::Vector6d> ViewAs(
    const Wrench *wrench);

// Returns a pointer to the raw memory stored in intrinsic::eigenmath::Vector6d
// as Wrench.
template <typename T>
T *ViewAs(intrinsic::eigenmath::Vector6d *vector);
template <>
Wrench *ViewAs(intrinsic::eigenmath::Vector6d *vector);

// VectorNd <-> Eigen::VectorXd

// Returns a reference to memory stored in VectorNd as a
// Eigen::Map<Eigen::VectorXd>
template <typename T>
Eigen::Map<T> ViewAs(VectorNd *vector);
template <>
Eigen::Map<Eigen::VectorXd> ViewAs(VectorNd *vector);
template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(VectorNd *vector);

template <typename T>
const Eigen::Map<const T> ViewAs(const VectorNd *vector);
template <>
const Eigen::Map<const intrinsic::eigenmath::VectorNd> ViewAs(
    const VectorNd *vector);

// Returns a pointer to the raw memory stored in Eigen::VectorXd as
// double*. We can't return VectorNd (buffer) since we do
// not allocate any memory for the VectorNd offset header in the Eigen memory.
template <typename T>
T *ViewAs(Eigen::VectorXd *vector);
template <>
double *ViewAs(Eigen::VectorXd *vector);

// Generic DetachedBuffer <-> Eigen

// Returns a reference to the memory stored in VectorNd, passed as an input
// to the flatbuffer buffer. The returned result is Eigen::Map<Eigne::VectorXd>
template <typename T>
Eigen::Map<T> ViewAs(flatbuffers::DetachedBuffer *buffer);
template <>
Eigen::Map<Eigen::VectorXd> ViewAs(flatbuffers::DetachedBuffer *buffer);
template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(
    flatbuffers::DetachedBuffer *buffer);

// Returns a mutable reference to the memory pointed at by a
// ::flatbuffers::Vector<double>. The returned result is
// Eigen::Map<Eigen::VectorNd>
template <typename T>
Eigen::Map<T> ViewAs(::flatbuffers::Vector<double> *vector);
template <>
Eigen::Map<intrinsic::eigenmath::VectorNd> ViewAs(
    ::flatbuffers::Vector<double> *vector);

// Returns a reference to the memory pointed at by a
// `const ::flatbuffers::Vector<double>`. The returned result is
// Eigen::Map<const Eigen::VectorNd>
template <typename T>
Eigen::Map<const T> ViewAs(const ::flatbuffers::Vector<double> *vector);
template <>
Eigen::Map<const intrinsic::eigenmath::VectorNd> ViewAs(
    const ::flatbuffers::Vector<double> *vector);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_FLATBUFFERS_TRANSFORM_VIEW_H_
