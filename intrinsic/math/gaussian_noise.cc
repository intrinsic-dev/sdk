// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/math/gaussian_noise.h"

#include "absl/random/distributions.h"

namespace intrinsic {

GaussianGenerator::GaussianGenerator(absl::BitGenRef gen, double mean,
                                     double stddev)
    : gen_(gen), mean_(mean), stddev_(stddev) {}

double GaussianGenerator::Generate() {
  return absl::Gaussian(gen_, mean_, stddev_);
}

eigenmath::VectorXd GaussianGenerator::Generate(int n) {
  eigenmath::VectorXd r(n);
  for (size_t i = 0; i < n; i++) r(i) = absl::Gaussian(gen_, mean_, stddev_);
  return r;
}

}  // namespace intrinsic
