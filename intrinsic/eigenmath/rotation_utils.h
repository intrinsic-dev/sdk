// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_EIGENMATH_ROTATION_UTILS_H_
#define INTRINSIC_EIGENMATH_ROTATION_UTILS_H_

#include <cmath>
#include <complex>
#include <limits>

#include "Eigen/Core"
#include "Eigen/Geometry"
#include "absl/log/check.h"
#include "intrinsic/eigenmath/types.h"

namespace intrinsic {
namespace eigenmath {

// Converts an arbitrary NxN matrix to a rotation matrix using SVD.
template <class Scalar, int N, int Options>
Matrix<Scalar, N, N> OrthogonalizeRotationMatrix(
    const Matrix<Scalar, N, N, Options>& A) {
  Eigen::JacobiSVD<Matrix<Scalar, N, N>, Eigen::NoQRPreconditioner> svd(
      A, Eigen::ComputeFullU | Eigen::ComputeFullV);
  return svd.matrixU() * svd.matrixV().transpose();
}

// Converts roll-pitch-yaw values to a quaternion.
template <typename Scalar, int Options>
void QuaternionFromRPY(Scalar roll, Scalar pitch, Scalar yaw,
                       Quaternion<Scalar, Options>* q) {
  CHECK(q != nullptr);
  using std::cos;
  using std::sin;  // for ADL

  const double phi = roll / Scalar(2.0);
  const double the = pitch / Scalar(2.0);
  const double psi = yaw / Scalar(2.0);

  q->w() = cos(phi) * cos(the) * cos(psi) + sin(phi) * sin(the) * sin(psi);
  q->x() = sin(phi) * cos(the) * cos(psi) - cos(phi) * sin(the) * sin(psi);
  q->y() = cos(phi) * sin(the) * cos(psi) + sin(phi) * cos(the) * sin(psi);
  q->z() = cos(phi) * cos(the) * sin(psi) - sin(phi) * sin(the) * cos(psi);

  q->normalize();
}

// Overload to convert roll-pitch-yaw values to a quaternion.
template <typename Scalar, int Options>
void RotationFromRPY(Scalar roll, Scalar pitch, Scalar yaw,
                     Quaternion<Scalar, Options>* q) {
  QuaternionFromRPY(roll, pitch, yaw, q);
}

// Converts roll-pitch-yaw values to a rotation matrix.
template <typename Scalar, int Options>
void RotationFromRPY(Scalar roll, Scalar pitch, Scalar yaw,
                     Matrix3<Scalar, Options>* A) {
  CHECK(A != nullptr);
  using std::cos;
  using std::sin;  // for ADL
  Matrix3<Scalar, Options> R_z = Matrix3<Scalar, Options>::Identity();
  R_z(0, 0) = cos(yaw);
  R_z(0, 1) = -sin(yaw);
  R_z(1, 0) = sin(yaw);
  R_z(1, 1) = cos(yaw);
  Matrix3<Scalar, Options> R_y = Matrix3<Scalar, Options>::Identity();
  R_y(0, 0) = cos(pitch);
  R_y(0, 2) = sin(pitch);
  R_y(2, 0) = -sin(pitch);
  R_y(2, 2) = cos(pitch);
  Matrix3<Scalar, Options> R_x = Matrix3<Scalar, Options>::Identity();
  R_x(1, 1) = cos(roll);
  R_x(1, 2) = -sin(roll);
  R_x(2, 1) = sin(roll);
  R_x(2, 2) = cos(roll);
  (*A) = R_z * R_y * R_x;
}

// Converts roll-pitch-yaw values to a given rotation representation.
template <class RotationType, class Scalar>
RotationType RotationFromRPY(Scalar roll, Scalar pitch, Scalar yaw) {
  RotationType result;
  RotationFromRPY(roll, pitch, yaw, &result);
  return result;  // NRVO
}

// Converts roll-pitch-yaw values to a quaternion.
template <class Scalar>
Quaternion<Scalar> QuaternionFromRPY(Scalar roll, Scalar pitch, Scalar yaw) {
  Quaternion<Scalar> result;
  QuaternionFromRPY(roll, pitch, yaw, &result);
  return result;  // NRVO
}

// Converts a quaternion to roll-pitch-yaw values.
//
// This function can be used to compute partial values (e.g., yaw only).
template <class Scalar, int Options>
void QuaternionToRPY(const Quaternion<Scalar, Options>& q, Scalar* roll,
                     Scalar* pitch, Scalar* yaw) {
  using std::asin;  // for ADL
  using std::atan2;
  constexpr Scalar kAlmostOne =
      Scalar(1) - std::numeric_limits<Scalar>::epsilon();
  if (Scalar(-2) * (q.x() * q.z() - q.w() * q.y()) > kAlmostOne) {
    if (roll != nullptr) {
      *roll = Scalar(0);
    }
    if (pitch != nullptr) {
      *pitch = Scalar(M_PI_2);
    }
    if (yaw != nullptr) {
      *yaw = Scalar(2) * atan2(q.z(), q.w());
    }
  } else if (Scalar(-2) * (q.x() * q.z() - q.w() * q.y()) < -kAlmostOne) {
    if (roll != nullptr) {
      *roll = Scalar(0);
    }
    if (pitch != nullptr) {
      *pitch = Scalar(-M_PI_2);
    }
    if (yaw != nullptr) {
      *yaw = Scalar(2) * atan2(q.z(), q.w());
    }
  } else {
    if (roll != nullptr) {
      *roll =
          atan2(Scalar(2) * (q.y() * q.z() + q.w() * q.x()),
                q.w() * q.w() - q.x() * q.x() - q.y() * q.y() + q.z() * q.z());
    }
    if (pitch != nullptr) {
      *pitch = asin(Scalar(-2) * (q.x() * q.z() - q.w() * q.y()));
    }
    if (yaw != nullptr) {
      *yaw =
          atan2(Scalar(2) * (q.x() * q.y() + q.w() * q.z()),
                q.w() * q.w() + q.x() * q.x() - q.y() * q.y() - q.z() * q.z());
    }
  }
}

// Converts a quaternion to roll-pitch-yaw values.
//
// This function can be used to compute partial values (e.g., yaw only).
template <class Scalar, int Options>
void RotationToRPY(const Quaternion<Scalar, Options>& q, Scalar* roll,
                   Scalar* pitch, Scalar* yaw) {
  return QuaternionToRPY(q, roll, pitch, yaw);
}

// Converts a rotation matrix to roll-pitch-yaw values.
//
// This function can be used to compute partial values (e.g., yaw only).
template <class Scalar, int Options>
void RotationToRPY(const Matrix3<Scalar, Options>& A, Scalar* roll,
                   Scalar* pitch, Scalar* yaw) {
  Quaternion<Scalar, Options> q{A};
  RotationToRPY(q, roll, pitch, yaw);
}

// Returns an angle-axis vector (a vector with the length of the rotation angle
// pointing to the direction of the rotation axis) representing the same
// rotation as the given 'quaternion'. This conversion is particularly
// numerically stable for auto differentiation, due to the linearization for
// small angles (in comparison to the Eigen::AngleAxis conversion).
template <typename T, int Options>
Vector3<T> QuaternionToAngleAxisVector(Quaternion<T, Options> quaternion) {
  quaternion.normalize();
  // We choose the quaternion with positive 'w', i.e., the one with a smaller
  // angle that represents this orientation.
  if (quaternion.w() < 0.) {
    // Multiply by -1. http://eigen.tuxfamily.org/bz/show_bug.cgi?id=560
    quaternion.w() *= T(-1.);
    quaternion.x() *= T(-1.);
    quaternion.y() *= T(-1.);
    quaternion.z() *= T(-1.);
  }
  // We convert the quaternion into a vector along the rotation axis with
  // length of the rotation angle.
  const T vec_norm = quaternion.vec().norm();
  const T angle = T(2.) * atan2(vec_norm, quaternion.w());
  constexpr double kCutoffAngle = 1e-7;  // We linearize below this angle.
  if (angle < kCutoffAngle) {
    const T scale{2.};
    return Vector3<T>(scale * quaternion.x(), scale * quaternion.y(),
                      scale * quaternion.z());
  } else {
    const T scale = angle / vec_norm;
    return Vector3<T>(scale * quaternion.x(), scale * quaternion.y(),
                      scale * quaternion.z());
  }
}

template <typename T>
AngleAxis<T> AngleTimesAxisToAngleAxis(const Vector3<T>& angle_times_axis) {
  double angle = angle_times_axis.norm();
  Vector3<T> axis;
  constexpr double kCutoffAngle = 1e-7;  // We use the default axis below this.
  if (angle < kCutoffAngle) {
    // when angle (norm) is so small and close to zero, setting the axis
    // arbitrarily is fine, as it will map to pretty much the identity rotation
    // or the identity quaternion anyways. Here we set it to the default axis.
    axis << 0, 0, 1;
  } else {
    axis = angle_times_axis / angle;
  }
  return {AngleAxis<T>(angle, axis)};
}

template <typename T>
Vector3<T> AngleAxisToAngleTimesAxis(const AngleAxis<T>& angle_axis) {
  return (angle_axis.angle() * angle_axis.axis());
}

}  // namespace eigenmath
}  // namespace intrinsic

#endif  // INTRINSIC_EIGENMATH_ROTATION_UTILS_H_
