// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MATH_POSE3_H_
#define INTRINSIC_MATH_POSE3_H_

#include <iostream>
#include <ostream>

#include "Eigen/Core"
#include "absl/base/attributes.h"
#include "intrinsic/eigenmath/so3.h"
#include "intrinsic/eigenmath/types.h"

namespace intrinsic {

// Transformation for 3D space
template <typename Scalar, int Options = eigenmath::kDefaultOptions>
class Pose3 {
 public:
  template <int OtherOptions>
  using Quaternion = eigenmath::Quaternion<Scalar, OtherOptions>;

  // Identity pose
  EIGEN_DEVICE_FUNC Pose3() : translation_(ZeroTranslation()), rotation_{} {}

  // Creates a pose with given translation
  EIGEN_DEVICE_FUNC explicit Pose3(
      const eigenmath::Vector3<Scalar>& translation)
      : translation_{translation}, rotation_{} {}

  // Creates a pose with given rotation
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC explicit Pose3(
      const eigenmath::SO3<Scalar, OtherOptions>& rotation)
      : translation_{ZeroTranslation()}, rotation_{rotation} {}

  // Creates a pose with given rotation
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC explicit Pose3(const Quaternion<OtherOptions>& rotation)
      : translation_{ZeroTranslation()}, rotation_{rotation} {}

  // Creates a pose from a 3 x 3 rotation matrix
  EIGEN_DEVICE_FUNC explicit Pose3(
      const eigenmath::Matrix3<Scalar>& rotation_matrix)
      : translation_(ZeroTranslation()), rotation_(rotation_matrix) {}

  // Creates a pose with given translation and rotation
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3(const eigenmath::SO3<Scalar, OtherOptions>& rotation,
                          const eigenmath::Vector3<Scalar>& translation)
      : translation_{translation}, rotation_{rotation} {}

  // Creates a pose with given translation and rotation.
  // The \p policy provides control over whether the rotation quaternion should
  // be normalized again or not. This can be relevant, e.g., to guarantee
  // bit-true representations on deserialization.
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3(
      const Quaternion<OtherOptions>& rotation,
      const eigenmath::Vector3<Scalar>& translation,
      const eigenmath::NormalizationPolicy policy = eigenmath::kNormalize)
      : translation_{translation},
        rotation_(rotation, policy == eigenmath::kNormalize) {}

  // Creates a pose from a 3 x 3 rotation matrix and a translation vector
  EIGEN_DEVICE_FUNC Pose3(const eigenmath::Matrix3<Scalar>& rotation_matrix,
                          const eigenmath::Vector3<Scalar>& translation)
      : translation_(translation), rotation_(rotation_matrix) {}

  // Creates a pose from a 4 x 4 affine transformation matrix
  template <int OtherOptions = eigenmath::kDefaultOptions>
  EIGEN_DEVICE_FUNC explicit Pose3(
      const eigenmath::Matrix4<Scalar, OtherOptions>& affine)
      : translation_(affine.template topRightCorner<3, 1>().eval()),
        rotation_(affine.template topLeftCorner<3, 3>().eval()) {}

  // Conversion operator for other Pose3 types with different
  // Eigen::Options
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3(const Pose3<Scalar, OtherOptions>& other)  // NOLINT
      : translation_{other.translation()}, rotation_{other.so3()} {}

  // Assignment operator for other Pose3 types with different Eigen::Options.
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3& operator=(const Pose3<Scalar, OtherOptions>& other) {
    translation_ = other.translation();
    rotation_ = other.so3();
    return *this;
  }

  // Gives identity pose, same as default constructor, more readable.
  EIGEN_DEVICE_FUNC static Pose3<Scalar, Options> Identity() {
    return Pose3<Scalar, Options>{};
  }

  // 3D translation vector
  EIGEN_DEVICE_FUNC const eigenmath::Vector3<Scalar>& translation() const {
    return translation_;
  }
  EIGEN_DEVICE_FUNC eigenmath::Vector3<Scalar>& translation() {
    return translation_;
  }

  ABSL_DEPRECATED("Assign to non-const translation()")
  void setTranslation(const eigenmath::Vector3<Scalar>& translation) {
    translation_ = translation;
  }

  // 3D rotation
  EIGEN_DEVICE_FUNC const eigenmath::SO3<Scalar, Options>& so3() const {
    return rotation_;
  }
  EIGEN_DEVICE_FUNC eigenmath::SO3<Scalar, Options>& so3() { return rotation_; }

  // Quaternion
  EIGEN_DEVICE_FUNC const Quaternion<Options>& quaternion() const {
    return rotation_.quaternion();
  }

  // Sets the rotation using quaternion
  template <int OtherOptions = eigenmath::kDefaultOptions>
  EIGEN_DEVICE_FUNC void setQuaternion(
      const Quaternion<OtherOptions>& quaternion) {
    rotation_ = quaternion;
  }

  // Gives the 3D rotation matrix
  EIGEN_DEVICE_FUNC eigenmath::Matrix3<Scalar> rotationMatrix() const {
    return rotation_.matrix();
  }

  // Sets the 3D rotation matrix
  EIGEN_DEVICE_FUNC void setRotationMatrix(
      const eigenmath::Matrix3<Scalar>& rotation_matrix) {
    rotation_ = eigenmath::SO3<Scalar, Options>(rotation_matrix);
  }

  // x-axis of the coordinate frame
  EIGEN_DEVICE_FUNC eigenmath::Vector3<Scalar> xAxis() const {
    return rotation_.matrix().template block<3, 1>(0, 0);
  }

  // y-axis of the coordinate frame
  EIGEN_DEVICE_FUNC eigenmath::Vector3<Scalar> yAxis() const {
    return rotation_.matrix().template block<3, 1>(0, 1);
  }

  // z-axis of the coordinate frame
  EIGEN_DEVICE_FUNC eigenmath::Vector3<Scalar> zAxis() const {
    return rotation_.matrix().template block<3, 1>(0, 2);
  }

  // Inverse transformation
  EIGEN_DEVICE_FUNC Pose3<Scalar> inverse() const {
    eigenmath::SO3<Scalar> rotation_inverse = rotation_.inverse();
    return Pose3<Scalar>{rotation_inverse, -(rotation_inverse * translation_)};
  }

  // Returns an affine 4x4 transformation matrix
  EIGEN_DEVICE_FUNC eigenmath::Matrix4<Scalar> matrix() const {
    eigenmath::Matrix4<Scalar> M;
    M.template topLeftCorner<3, 3>() = rotationMatrix();
    M.template topRightCorner<3, 1>() = translation();
    M.template bottomLeftCorner<1, 3>() =
        eigenmath::Matrix<Scalar, 1, 3>::Zero();
    M(3, 3) = Scalar(1);
    return M;
  }

  ABSL_DEPRECATED("Use matrix() instead")
  eigenmath::Matrix4<Scalar> toMatrix() const { return matrix(); }

  // Cast Pose3 instance to other scalar type
  template <typename OtherScalar>
  EIGEN_DEVICE_FUNC Pose3<OtherScalar> cast() const {
    return Pose3<OtherScalar>(rotation_.template cast<OtherScalar>(),
                              translation_.template cast<OtherScalar>());
  }

  // Checks if identical to another pose under a given tolerance
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC bool isApprox(const Pose3<Scalar, OtherOptions>& other,
                                  Scalar tolerance) const {
    return isApprox(other, tolerance, tolerance);
  }

  // Checks if identical to another pose under a given tolerance
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC bool isApprox(const Pose3<Scalar, OtherOptions>& other,
                                  Scalar linear_tolerance,
                                  Scalar angular_tolerance) const {
    return ((translation() - other.translation()).norm() < linear_tolerance) &&
           so3().isApprox(other.so3(), angular_tolerance);
  }

  // Checks if identical to another pose under default tolerance
  template <int OtherOptions>
  EIGEN_DEVICE_FUNC bool isApprox(
      const Pose3<Scalar, OtherOptions>& other) const {
    return isApprox(other, Eigen::NumTraits<Scalar>::dummy_precision());
  }

  // Compose poses in-place
  template <typename OtherScalar, int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3<Scalar, Options>& operator*=(
      const Pose3<OtherScalar, OtherOptions>& rhs) {
    translation_ += rotation_ * rhs.translation();
    rotation_ *= rhs.so3();
    return *this;
  }

  // Composes two poses
  template <typename OtherScalar, int OtherOptions>
  EIGEN_DEVICE_FUNC Pose3<Scalar> operator*(
      const Pose3<OtherScalar, OtherOptions>& rhs) const {
    Pose3<Scalar> result(*this);
    return result *= rhs;
  }

  template <typename H>
  friend H AbslHashValue(H h, const Pose3<Scalar, Options>& p) {
    Eigen::Quaternion<Scalar, Options> q =
        p.rotation_.quaternion().normalized();
    if (q.w() < 0) {
      // Since we have double coverage, we make the choice that we want to have
      // w be positive to ensure that we hash to the same values.
      q.coeffs() *= -1.0;
    }

    return H::combine(std::move(h), p.translation_[0], p.translation_[1],
                      p.translation_[2], q.w(), q.x(), q.y(), q.z());
  }

 private:
  EIGEN_DEVICE_FUNC static eigenmath::Vector3<Scalar> ZeroTranslation() {
    return eigenmath::Vector3<Scalar>::Zero();
  }

  eigenmath::Vector3<Scalar> translation_;
  // Padding makes aligned and unaligned types match in memory layout.
  Scalar padding_ = Scalar{0.0};
  eigenmath::SO3<Scalar, Options> rotation_;
};

template <typename T, int Options>
std::ostream& operator<<(std::ostream& os, const Pose3<T, Options>& a_pose_b) {
  os << "translation: " << a_pose_b.translation().transpose()
     << " quaternion: " << a_pose_b.quaternion().coeffs().transpose();
  return os;
}

// Transforms a 3D point with a 3D transformation
template <typename Scalar, int Options, typename Derived>
EIGEN_DEVICE_FUNC eigenmath::Vector<Scalar, 3> operator*(
    const Pose3<Scalar, Options>& pose,
    const Eigen::MatrixBase<Derived>& point) {
  return pose.translation() + pose.so3() * point;
}

// Compose Pose3 with a affine transform
template <typename Scalar, int Options_lhs, int Options_rhs>
inline eigenmath::Matrix4<Scalar, Options_rhs> operator*(
    const Pose3<Scalar, Options_lhs>& lhs,
    const eigenmath::Matrix4<Scalar, Options_rhs>& rhs) {
  return lhs.matrix() * rhs;
}

// Compose affine transform and a Pose3
template <typename Scalar, int Options_lhs, int Options_rhs>
inline eigenmath::Matrix4<Scalar, Options_lhs> operator*(
    const eigenmath::Matrix4<Scalar, Options_lhs>& lhs,
    const Pose3<Scalar, Options_rhs>& rhs) {
  return lhs * rhs.matrix();
}
using Pose3dAligned = Pose3<double, Eigen::AutoAlign>;
using Pose3d = Pose3<double, Eigen::DontAlign>;
using Pose3fAligned = Pose3<float, Eigen::AutoAlign>;
using Pose3f = Pose3<float, Eigen::DontAlign>;
using Pose = Pose3d;

//  Creates a pose from angle axis representation
template <typename T>
Pose3<T> CreateAngleAxisPose(T angle, const Eigen::Vector3<T>& axis,
                             const Eigen::Vector3<T>& position) {
  return Pose3<T>(Eigen::AngleAxis<T>(angle, axis).matrix(), position);
}

//  Creates a pose from angle axis representation
template <typename T>
Pose3<T> CreateAngleAxisPose(T angle, const Eigen::Vector3<T>& axis) {
  return Pose3<T>(Eigen::AngleAxis<T>(angle, axis).matrix());
}

}  // namespace intrinsic

#endif  // INTRINSIC_MATH_POSE3_H_
