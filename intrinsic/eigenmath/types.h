// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// This header brings in Vector, Matrix, Quaternion and Plane types from the
// blue::eigenmath namespace.

#ifndef INTRINSIC_EIGENMATH_TYPES_H_
#define INTRINSIC_EIGENMATH_TYPES_H_

#include "Eigen/Core"      // IWYU pragma: export
#include "Eigen/Geometry"  // IWYU pragma: export

namespace intrinsic {
namespace eigenmath {

constexpr int kDefaultOptions =
    Eigen::AutoAlign | EIGEN_DEFAULT_MATRIX_STORAGE_ORDER_OPTION;

// Maximum size of vectors and matrices. Increase as needed.
inline constexpr int MAX_EIGEN_VECTOR_SIZE = 25;
inline constexpr int MAX_EIGEN_MATRIX_SIZE = 25;

template <class Scalar, int N, int Options = Eigen::AutoAlign>
using Vector = Eigen::Matrix<Scalar, N, 1, Options>;
template <int N, int Options = Eigen::AutoAlign>
using Vectord = Vector<double, N, Options>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Vector2 = Vector<Scalar, 2, Options>;
using Vector2f = Vector2<float>;  // Fixed sized, non-vectorizable type
using Vector2dAligned = Vector2<double, Eigen::AutoAlign>;
using Vector2d = Vector2<double, Eigen::DontAlign>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Vector3 = Vector<Scalar, 3, Options>;
using Vector3f = Vector3<float>;   // Fixed sized, non-vectorizable type
using Vector3d = Vector3<double>;  // Fixed sized, non-vectorizable type
using Vector3i = Vector3<int>;
using Vector3b = Vector3<bool>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Vector4 = Vector<Scalar, 4, Options>;
using Vector4fAligned = Vector4<float, Eigen::AutoAlign>;
using Vector4dAligned = Vector4<double, Eigen::AutoAlign>;
using Vector4f = Vector4<float, Eigen::DontAlign>;
using Vector4d = Vector4<double, Eigen::DontAlign>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Vector6 = Vector<Scalar, 6, Options>;
using Vector6dAligned = Vector6<double, Eigen::AutoAlign>;
using Vector6d = Vector6<double, Eigen::DontAlign>;
using Vector6f = Vector6<float>;  // Fixed sized, non-vectorizable type
using Vector6b = Vector6<bool>;   // Fixed sized, non-vectorizable type

template <class Scalar, int Options = Eigen::AutoAlign>
using Vector7 = Vector<Scalar, 7, Options>;
using Vector7dAligned = Vector7<double, Eigen::AutoAlign>;
using Vector7d = Vector7<double, Eigen::DontAlign>;
using Vector7f = Vector7<float>;  // Fixed sized, non-vectorizable type
using Vector7b = Vector7<bool>;   // Fixed sized, non-vectorizable type

using Matrix3Nd = Eigen::Matrix<double, 3, Eigen::Dynamic, Eigen::DontAlign, 3,
                                MAX_EIGEN_MATRIX_SIZE>;
using Matrix6Nd = Eigen::Matrix<double, 6, Eigen::Dynamic, Eigen::DontAlign, 6,
                                MAX_EIGEN_MATRIX_SIZE>;
template <int N = Eigen::Dynamic>
using Matrix6NdAligned = Eigen::Matrix<double, 6, N, Eigen::AutoAlign>;
using MatrixNd =
    Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::DontAlign,
                  MAX_EIGEN_MATRIX_SIZE, MAX_EIGEN_MATRIX_SIZE>;
using MatrixNMd =
    Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::DontAlign,
                  MAX_EIGEN_MATRIX_SIZE, MAX_EIGEN_MATRIX_SIZE>;

// Eigen vector of doubles with a given maximum size
template <int N>
using VectorNdWithMaxSize =
    Eigen::Matrix<double, Eigen::Dynamic, 1, Eigen::DontAlign, N, 1>;
// default version using MAX_EIGEN_MATRIX_SIZE
using VectorNd = VectorNdWithMaxSize<MAX_EIGEN_VECTOR_SIZE>;

using VectorNb =
    Eigen::Matrix<bool, Eigen::Dynamic, 1, 0, MAX_EIGEN_VECTOR_SIZE, 1>;

template <typename Scalar>
using VectorX = Eigen::Matrix<Scalar, Eigen::Dynamic, 1>;
using VectorXd = VectorX<double>;
using VectorXf = VectorX<float>;
using VectorXb = VectorX<bool>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Quaternion = Eigen::Quaternion<Scalar, Options>;
using QuaternionfAligned = Quaternion<float, Eigen::AutoAlign>;
using Quaternionf = Quaternion<float, Eigen::DontAlign>;
using QuaterniondAligned = Quaternion<double, Eigen::AutoAlign>;
using Quaterniond = Quaternion<double, Eigen::DontAlign>;

template <class Scalar>
using AngleAxis = Eigen::AngleAxis<Scalar>;
using AngleAxisf = AngleAxis<float>;
using AngleAxisd = AngleAxis<double>;

template <class Scalar, int Dim, int Mode, int Options>
using Transform = Eigen::Transform<Scalar, Dim, Mode, Options>;

template <class Scalar, int Options>
using AffineTransform3 = Transform<Scalar, 3, Eigen::Affine, Options>;
using AffineTransform3f = AffineTransform3<float, Eigen::DontAlign>;
using AffineTransform3d = AffineTransform3<double, Eigen::DontAlign>;

template <class Scalar, int Rows, int Cols,
          int Options = Eigen::AutoAlign |
                        ((Rows == 1 && Cols != 1) ? Eigen::RowMajor
                         : (Cols == 1 && Rows != 1)
                             ? Eigen::ColMajor
                             : EIGEN_DEFAULT_MATRIX_STORAGE_ORDER_OPTION)>
using Matrix = Eigen::Matrix<Scalar, Rows, Cols, Options>;
template <int N, int M = N, int Options = Eigen::AutoAlign>
using Matrixd = Matrix<double, N, M, Options>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Matrix2 = Matrix<Scalar, 2, 2, Options>;
using Matrix2fAligned = Matrix2<float, Eigen::AutoAlign>;
using Matrix2f = Matrix2<float, Eigen::DontAlign>;
using Matrix2dAligned = Matrix2<double, Eigen::AutoAlign>;
using Matrix2d = Matrix2<double, Eigen::DontAlign>;
using Eigen::Matrix2Xd;
using Eigen::Matrix2Xf;
using Eigen::MatrixX2d;
using Eigen::MatrixX2f;

template <class Scalar, int Options = Eigen::AutoAlign>
using Matrix3 = Matrix<Scalar, 3, 3, Options>;
using Matrix3f = Matrix3<float>;   // Fixed sized, non-vectorizable type
using Matrix3d = Matrix3<double>;  // Fixed sized, non-vectorizable type
using Eigen::Matrix3Xd;
using Eigen::Matrix3Xf;
using Eigen::MatrixX3d;
using Eigen::MatrixX3f;

template <class Scalar, int Options = Eigen::AutoAlign>
using Matrix4 = Matrix<Scalar, 4, 4, Options>;
using Matrix4fAligned = Matrix4<float, Eigen::AutoAlign>;
using Matrix4f = Matrix4<float, Eigen::DontAlign>;
using Matrix4dAligned = Matrix4<double, Eigen::AutoAlign>;
using Matrix4d = Matrix4<double, Eigen::DontAlign>;
using Eigen::Matrix4Xd;
using Eigen::Matrix4Xf;
using Eigen::MatrixX4d;
using Eigen::MatrixX4f;

template <class Scalar, int Options = Eigen::AutoAlign>
using Matrix6 = Matrix<Scalar, 6, 6, Options>;
using Matrix6fAligned = Matrix6<float, Eigen::AutoAlign>;
using Matrix6f = Matrix6<float, Eigen::DontAlign>;
using Matrix6dAligned = Matrix6<double, Eigen::AutoAlign>;
using Matrix6d = Matrix6<double, Eigen::DontAlign>;
using Matrix6Xf = Eigen::Matrix<float, 6, Eigen::Dynamic>;
using Matrix6Xd = Eigen::Matrix<double, 6, Eigen::Dynamic>;
using MatrixX6f = Eigen::Matrix<float, Eigen::Dynamic, 6>;
using MatrixX6d = Eigen::Matrix<double, Eigen::Dynamic, 6>;

template <class Scalar, int Options = Eigen::AutoAlign>
using MatrixX = Matrix<Scalar, Eigen::Dynamic, Eigen::Dynamic, Options>;
using MatrixXf = MatrixX<float, Eigen::DontAlign>;
using MatrixXd = MatrixX<double, Eigen::DontAlign>;
using MatrixXb = MatrixX<bool, Eigen::DontAlign>;

template <class Scalar, int Options = Eigen::AutoAlign>
using Plane3 = Eigen::Hyperplane<Scalar, 3, Options>;
using Plane3dAligned =
    Plane3<double, Eigen::AutoAlign>;  // Dim coefficients is 3 + 1 = 4
using Plane3d =
    Plane3<double, Eigen::DontAlign>;  // Dim coefficients is 3 + 1 = 4

using Plane3fAligned =
    Plane3<float, Eigen::AutoAlign>;  // Dim coefficients is 3 + 1 = 4
using Plane3f =
    Plane3<float, Eigen::DontAlign>;  // Dim coefficients is 3 + 1 = 4

template <class Scalar, int Options = Eigen::AutoAlign>
using Line2 = Eigen::Hyperplane<Scalar, 2, Options>;
using Line2dAligned =
    Line2<double, Eigen::AutoAlign>;  // Dim coefficients is 2 + 1 = 3
using Line2d =
    Line2<double, Eigen::DontAlign>;  // Dim coefficients is 2 + 1 = 3

using Line2fAligned =
    Line2<float, Eigen::AutoAlign>;             // Dim coefficients is 2 + 1 = 3
using Line2f = Line2<float, Eigen::DontAlign>;  // Dim coefficients is 2 + 1 = 3

// Policy whether to normalize quaternions on construction.
enum NormalizationPolicy { kNormalize, kDoNotNormalize };

}  // namespace eigenmath
}  // namespace intrinsic

#endif  // INTRINSIC_EIGENMATH_TYPES_H_
