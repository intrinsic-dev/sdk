// Copyright 2023 Intrinsic Innovation LLC


#include "intrinsic/icon/flatbuffers/transform_copy.h"

#include "flatbuffers/base.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/flatbuffers/transform_types.fbs.h"
#include "intrinsic/icon/flatbuffers/transform_view.h"

namespace intrinsic_fbs {

void CopyTo(const Eigen::Vector3d &vector, Point *point) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<Eigen::Vector3d>(point) = vector;
}

void CopyTo(const Eigen::Quaterniond &quaternion, Rotation *rotation) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<Eigen::Quaterniond>(rotation) = quaternion;
}

void CopyTo(const Eigen::VectorXd &vector, VectorNd *vector_fbs) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<Eigen::VectorXd>(vector_fbs) = vector;
}

void CopyTo(const intrinsic::eigenmath::Vector6d &vector, Twist *twist) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<intrinsic::eigenmath::Vector6d>(twist) = vector;
}

void CopyTo(const intrinsic::eigenmath::Vector6d &vector,
            Acceleration *acceleration) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<intrinsic::eigenmath::Vector6d>(acceleration) = vector;
}

void CopyTo(const intrinsic::eigenmath::Vector6d &vector, Jerk *jerk) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<intrinsic::eigenmath::Vector6d>(jerk) = vector;
}

void CopyTo(const intrinsic::eigenmath::Vector6d &vector, Wrench *wrench) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<intrinsic::eigenmath::Vector6d>(wrench) = vector;
}

void CopyTo(const intrinsic::eigenmath::VectorNd &vector,
            VectorNd *vector_fbs) {
  static_assert(FLATBUFFERS_LITTLEENDIAN, "Unsupported architecture.");
  ViewAs<intrinsic::eigenmath::VectorNd>(vector_fbs) = vector;
}

}  // namespace intrinsic_fbs
