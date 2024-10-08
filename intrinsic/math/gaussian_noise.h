// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MATH_GAUSSIAN_NOISE_H_
#define INTRINSIC_MATH_GAUSSIAN_NOISE_H_

#include "absl/random/bit_gen_ref.h"
#include "intrinsic/eigenmath/types.h"

namespace intrinsic {

// Uses absl::Gaussian() with the provided generator, mean and stddev to create
// random values.
class GaussianGenerator {
 public:
  GaussianGenerator() = delete;

  // Maintains a reference to `gen` until destruction.
  explicit GaussianGenerator(absl::BitGenRef gen, double mean = 0.0,
                             double stddev = 1.0);

  // Generates a random number, generated using absl::Gaussian(gen, mean,
  // stddev)
  double Generate();

  // Generates a random vector of size `n`, where each element is set to
  // absl::Gaussian(gen, mean, stddev);
  eigenmath::VectorXd Generate(int n);

 private:
  absl::BitGenRef gen_;  // owned externally.
  double mean_;
  double stddev_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_MATH_GAUSSIAN_NOISE_H_
