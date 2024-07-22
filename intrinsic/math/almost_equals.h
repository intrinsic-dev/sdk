// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_MATH_ALMOST_EQUALS_H_
#define INTRINSIC_MATH_ALMOST_EQUALS_H_

#include <algorithm>
#include <cmath>
#include <limits>

namespace intrinsic {
// 32 is 5 bits of mantissa error; should be adequate for common errors.
constexpr double kStdError = 32 * std::numeric_limits<double>::epsilon();

// Tests whether two values are close enough to each other to be considered
// equal. The purpose of AlmostEquals() is to avoid false positive error reports
// due to minute differences in floating point arithmetic (for example, due to a
// different compiler).
//
static inline bool AlmostEquals(const double x, const double y,
                                const double std_error = kStdError) {
  // If standard == says they are equal then we can return early.
  if (x == y) return true;

  const double abs_x = std::fabs(x);
  const double abs_y = std::fabs(y);

  if (abs_x <= std_error && abs_y <= std_error) return true;

  if (std::isinf(x) || std::isnan(x) || std::isinf(y) || std::isnan(y)) {
    return false;
  }

  const double relative_margin = std_error * std::max(abs_x, abs_y);
  const double max_error = std::max(std_error, relative_margin);

  if (x > y) {
    return (x - y) <= max_error;
  } else {
    return (y - x) <= max_error;
  }
}

}  // namespace intrinsic

#endif  // INTRINSIC_MATH_ALMOST_EQUALS_H_
