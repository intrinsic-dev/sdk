// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/kinematics/validate_link_parameters.h"

#include "Eigen/Eigenvalues"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/kinematics/types/to_string.h"

namespace intrinsic::kinematics {
namespace {

const double kMaxDifferenceThreshold = 1e-6;

bool IsSymmetric(const eigenmath::Matrix3d& matrix,
                 double max_difference_threshold = kMaxDifferenceThreshold) {
  return matrix.isApprox(matrix.transpose(), max_difference_threshold);
}

}  // namespace

absl::Status ValidateMass(double mass_kg) {
  if (mass_kg <= 0) {
    return absl::FailedPreconditionError(absl::StrCat(
        "The mass should be > 0.0, but got ", mass_kg, " kg instead."));
  }
  return absl::OkStatus();
}

absl::Status ValidateInertia(const eigenmath::Matrix3d& inertia) {
  // The link inertia tensor should be density realizable. In other words,
  // the inertia tensor expressed at the center of gravity should be positive
  // definite (symmetric and with positive eigenvalues) and its eigenvalues
  // fulfill the triangle inequalities.
  if (!IsSymmetric(inertia)) {
    return absl::FailedPreconditionError(
        absl::StrCat("Inertia tensor is not symmetric. Got ", "[[ ",
                     eigenmath::ToString(inertia.row(0)), "],[ ",
                     eigenmath::ToString(inertia.row(1)), "],[ ",
                     eigenmath::ToString(inertia.row(2)), "]]."));
  }

  Eigen::EigenSolver<eigenmath::Matrix3d> eigen_solver(inertia);
  const eigenmath::Vector3d& eigenvalues = eigen_solver.eigenvalues().real();
  if ((eigenvalues.array() <= 0.0).any()) {
    return absl::FailedPreconditionError(absl::StrCat(
        "Inertia tensor of link is not positive definite. All of its "
        "eigenvalues should be > 0.0, "
        "but got ",
        eigenmath::ToString(eigenvalues), "."));
  }

  for (int i = 0; i < 3; ++i) {
    if (eigenvalues.sum() < 2.0 * eigenvalues[i]) {
      return absl::FailedPreconditionError(
          absl::StrCat("The eigenvalues of the inertia tensor do not satisfy "
                       "the triangle inequality: ",
                       eigenvalues.sum(), " is not larger or equal than ",
                       2.0 * eigenvalues[i], "."));
    }
  }
  return absl::OkStatus();
}
}  // namespace intrinsic::kinematics
