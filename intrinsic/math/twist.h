// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MATH_TWIST_H_
#define INTRINSIC_MATH_TWIST_H_

#include <type_traits>

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {
namespace internal {

/// The basic type used to store a CartesianVector.
using CartesianVectorBase = eigenmath::Vector6d;

/// A 6DOF vector representing one value for each cartesian degreen of freedom.
/// This can be useful to represent twist, acceleration, jerk, wrench, etc.
/// Do not use this to represent a 6DOF Pose or Transform.  Use Pose3d instead.
///
/// CartesianVector has the same interface as eigenmath::Vector6d, but with more
/// flexible constructors.
class CartesianVector : public CartesianVectorBase {
 public:
  // Construct a zero vector
  CartesianVector() : CartesianVectorBase(CartesianVectorBase::Zero()) {}

  // Construct from x,y,z,RX,RY,RZ
  CartesianVector(double x, double y, double z, double RX, double RY,
                  double RZ) {
    *this << x, y, z, RX, RY, RZ;
  }

  // Construct from an eigenmath::Vector6d
  explicit CartesianVector(const eigenmath::Vector6d& v)
      : CartesianVectorBase(v) {}

  // Assign from CartesianVector or CartesianVectorBase.
  CartesianVector& operator=(const CartesianVectorBase& v) {
    *this = CartesianVector(v);
    return *this;
  }

  double& x() { return operator()(0); }
  double& y() { return operator()(1); }
  double& z() { return operator()(2); }
  double& RX() { return operator()(3); }
  double& RY() { return operator()(4); }
  double& RZ() { return operator()(5); }
  double x() const { return operator()(0); }
  double y() const { return operator()(1); }
  double z() const { return operator()(2); }
  double RX() const { return operator()(3); }
  double RY() const { return operator()(4); }
  double RZ() const { return operator()(5); }


  static const CartesianVector ZERO;

 private:
  /// This is private to prevent it being used accidentally.
  /// Use CartesianVector::ZERO instead.
  static CartesianVector Zero(int rows = 0) { return ZERO; }
};

// This is a strongly typed CartesianVector.
template <class UniqueType>
class CartesianVectorSubclass : public CartesianVector {
 public:
  CartesianVectorSubclass() : CartesianVector() {}

  CartesianVectorSubclass(double x, double y, double z, double RX, double RY,
                          double RZ)
      : CartesianVector(x, y, z, RX, RY, RZ) {}

  explicit CartesianVectorSubclass(const eigenmath::Vector6d& v)
      : CartesianVector(v) {}

  template <class T, typename = typename std::enable_if<std::is_convertible<
                         T, CartesianVectorBase>::value>::type>
  CartesianVectorSubclass& operator=(const T& v) {
    *this = CartesianVectorSubclass(v);
    return *this;
  }


  static const CartesianVectorSubclass ZERO;
};

template <class UniqueType>
const CartesianVectorSubclass<UniqueType>
    CartesianVectorSubclass<UniqueType>::ZERO;

}  // namespace internal

/// The 6DOF linear and angular velocity of a frame or rigid body.
/// Units are m/s and rad/s.
///
/// Twist has the same interface as eigenmath::Vector6d, but with the same
/// constructors as CartesianVector.
using Twist = internal::CartesianVectorSubclass<struct InternalTwist>;

/// The 6DOF linear and angular acceleration of a frame or rigid body.
/// Units are m/ss and rad/ss.
///
/// Acceleration has the same interface as eigenmath::Vector6d, but with the
/// same constructors as CartesianVector.
using Acceleration =
    internal::CartesianVectorSubclass<struct InternalAcceleration>;

/// The 6DOF time derivative of acceleration.
/// Units are m/sss and rad/sss.
///
/// Jerk has the same interface as eigenmath::Vector6d, but with the same
/// constructors as CartesianVector.
using Jerk = internal::CartesianVectorSubclass<struct InternalJerk>;

/// The 6DOF force and torque applied from one object to another.
/// Units are N and Nm.
///
/// Wrench has the same interface as eigenmath::Vector6d, but with the same
/// constructors as CartesianVector.
using Wrench = internal::CartesianVectorSubclass<struct InternalWrench>;

}  // namespace intrinsic

#endif  // INTRINSIC_MATH_TWIST_H_
