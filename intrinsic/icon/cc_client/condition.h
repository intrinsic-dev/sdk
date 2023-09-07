// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CC_CLIENT_CONDITION_H_
#define INTRINSIC_ICON_CC_CLIENT_CONDITION_H_

#include <memory>
#include <string>
#include <utility>
#include <variant>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/types/span.h"
#include "absl/types/variant.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic {
namespace icon {

// The type of a comparison value used in comparisons like greater, equal etc.
using ComparisonValue = std::variant<bool, double, int64_t>;
// The type of a state variable value of actions.
using StateVariableValue = std::variant<bool, double, int64_t>;

static constexpr double kDefaultMaxAbsError = 0x1p-10;

// A Comparison is used to compare an Action-specific state variable or any
// supported field of the robot system status to a fixed value.
//
// Helper functions to create the state variable strings for fields of the
// robot system state can be found in
// "intrinsic/icon/cc_client/state_variable_path.h".
//
// The length of a state variable name is limited when used for action state
// variables; too long names will cause an error when the comparison is
// converted into its realtime equivalent.
class Comparison {
 public:
  // The set of comparison operations available for boolean conditions.
  enum class BooleanOperator {
    kEqual = 1,
    kNotEqual = 2,
  };

  // The set of comparison operations available for integer conditions.
  enum class IntOperator {
    kEqual = 1,
    kNotEqual = 2,
    // Skips index 3 and 4 to stay compatible with
    // intrinsic/icon/proto/types.proto.
    kLessThanOrEqual = 5,
    kLessThan = 6,
    kGreaterThanOrEqual = 7,
    kGreaterThan = 8,
  };

  // The set of comparison operations available for floating point conditions.
  enum class FloatOperator {
    // Skips index 1 and 2 to stay compatible with
    // intrinsic/icon/proto/types.proto.
    kApproxEqual = 3,
    kApproxNotEqual = 4,
    kLessThanOrEqual = 5,
    kLessThan = 6,
    kGreaterThanOrEqual = 7,
    kGreaterThan = 8,
  };

  // Constructs a Comparison between `state_variable_name` and `value`.
  //
  // `max_abs_error` is used for APPROX_EQUAL and APPROX_NOT_EQUAL comparisons,
  // and is ignored otherwise.
  //
  // Returns `InvalidArgumentError` if `value` holds a bool and `operation` is
  // anything other than EQUAL or NOT_EQUAL.
  static absl::StatusOr<Comparison> Create(
      absl::string_view state_variable_name,
      intrinsic_proto::icon::Comparison::OpEnum operation,
      ComparisonValue value, double max_abs_error = kDefaultMaxAbsError);

  // Constructs a Comparison between `state_variable_name` and `value`.
  Comparison(absl::string_view state_variable_name, BooleanOperator operation,
             bool value);

  // Constructs a Comparison between `state_variable_name` and `value`.
  //
  // `max_abs_error` is used for kApproxEqual and kApproxNotEqual comparisons,
  // and is ignored otherwise.
  Comparison(absl::string_view state_variable_name, FloatOperator operation,
             double value, double max_abs_error = kDefaultMaxAbsError);

  Comparison(absl::string_view state_variable_name, IntOperator operation,
             int64_t value);

  // Gets a reference to this Comparison's state variable name.
  // The returned reference is only valid for the lifetime of this Comparison
  // object.
  absl::string_view state_variable_name() const;

  // Gets the comparison operation to perform.
  intrinsic_proto::icon::Comparison::OpEnum operation() const {
    return operation_;
  }

  // Gets the value of the second operand.
  const ComparisonValue& value() const { return value_; }

  // Gets the max absolute error to use for APPROX_EQUAL and APPROX_NOT_EQUAL
  // comparisons.
  double max_abs_error() const { return max_abs_error_; }

  friend bool operator==(const Comparison& lhs, const Comparison& rhs);
  friend bool operator!=(const Comparison& lhs, const Comparison& rhs);

  template <typename H>
  friend H AbslHashValue(H h, const Comparison& c) {
    return H::combine(std::move(h), c.state_variable_name_, c.operation_,
                      c.value_, c.max_abs_error_);
  }

 private:
  Comparison(absl::string_view state_variable_name,
             intrinsic_proto::icon::Comparison::OpEnum operation,
             ComparisonValue value, double max_abs_error);
  // Name of state variable to use as first operand.
  std::string state_variable_name_;
  // Comparison operation to perform.
  intrinsic_proto::icon::Comparison::OpEnum operation_;
  // Value to use as second operand.
  ComparisonValue value_;
  // Epsilon to use for approx comparisons.
  double max_abs_error_;
};

inline bool operator==(const Comparison& lhs, const Comparison& rhs) {
  return lhs.state_variable_name_ == rhs.state_variable_name_ &&
         lhs.operation_ == rhs.operation_ && lhs.value_ == rhs.value_ &&
         lhs.max_abs_error_ == rhs.max_abs_error_;
}

inline bool operator!=(const Comparison& lhs, const Comparison& rhs) {
  return !(lhs == rhs);
}

// Describes a Comparison that is satisfied when `state_variable_name` is equal
// to `true`.
Comparison IsTrue(absl::string_view state_variable_name);

// Describes a Comparison that is satisfied when `state_variable_name` is equal
// to `false`.
Comparison IsFalse(absl::string_view state_variable_name);

// Describes a Comparison that is satisfied when `state_variable_name` is equal
// to `value`.
Comparison IsEqual(absl::string_view state_variable_name, int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is *not*
// equal to `value`.
Comparison IsNotEqual(absl::string_view state_variable_name, int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// approximately equal to `value`.
Comparison IsApprox(absl::string_view state_variable_name, double value,
                    double max_abs_error = kDefaultMaxAbsError);

// Describes a Comparison that is satisfied when `state_variable_name` is less
// than or equal to `value`.
Comparison IsLessThanOrEqual(absl::string_view state_variable_name,
                             int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is less
// than `value`.
Comparison IsLessThan(absl::string_view state_variable_name, int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// greater than or equal to `value`.
Comparison IsGreaterThanOrEqual(absl::string_view state_variable_name,
                                int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// greater than `value`.
Comparison IsGreaterThan(absl::string_view state_variable_name, int64_t value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// not approximately equal to `value`.
Comparison IsNotApprox(absl::string_view state_variable_name, double value,
                       double max_abs_error = kDefaultMaxAbsError);

// Describes a Comparison that is satisfied when `state_variable_name` is less
// than or equal to `value`.
Comparison IsLessThanOrEqual(absl::string_view state_variable_name,
                             double value);

// Describes a Comparison that is satisfied when `state_variable_name` is less
// than `value`.
Comparison IsLessThan(absl::string_view state_variable_name, double value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// greater than or equal to `value`.
Comparison IsGreaterThanOrEqual(absl::string_view state_variable_name,
                                double value);

// Describes a Comparison that is satisfied when `state_variable_name` is
// greater than `value`.
Comparison IsGreaterThan(absl::string_view state_variable_name, double value);

// Creates a Comparison from proto representation.
absl::StatusOr<Comparison> FromProto(
    const intrinsic_proto::icon::Comparison& proto);

// Converts a Comparison to proto representation.
intrinsic_proto::icon::Comparison ToProto(const Comparison& condition);

class ConjunctionCondition;
class NegatedCondition;

using Condition =
    std::variant<Comparison, ConjunctionCondition, NegatedCondition>;

// A ConjunctionCondition represents a condition comprised of the composition of
// other conditions.
class ConjunctionCondition {
 public:
  enum class Operation { kAllOf = 1, kAnyOf = 2 };

  ConjunctionCondition(Operation operation,
                       absl::Span<const Condition> conditions);

  // Returns the conditions comprising this condition.
  const std::vector<Condition>& GetConditions() const;

  // Returns the operation this condition uses to aggregate its conditions.
  Operation GetOperation() const;

  friend bool operator==(const ConjunctionCondition& lhs,
                         const ConjunctionCondition& rhs);

  friend bool operator!=(const ConjunctionCondition& lhs,
                         const ConjunctionCondition& rhs);

  template <typename H>
  friend H AbslHashValue(H h, const ConjunctionCondition& c) {
    return H::combine(std::move(h), c.operation_, c.conditions_);
  }

 private:
  Operation operation_;
  std::vector<Condition> conditions_;
};

// Randomly-chosen value used to distinguish a negated condition hash from
// contained condition hash.
constexpr int kNegatedConditionId = 0xAEDF098;

// A NegatedCondition represents a negation of the comprised condition.
class NegatedCondition {
 public:
  explicit NegatedCondition(const Condition& condition);
  explicit NegatedCondition(Condition&& condition);
  NegatedCondition(const NegatedCondition& condition);
  NegatedCondition(NegatedCondition&& condition) = default;
  NegatedCondition& operator=(const NegatedCondition& condition);
  NegatedCondition& operator=(NegatedCondition&& condition) = default;
  ~NegatedCondition() = default;

  // Returns the condition to be negated.
  const Condition& GetCondition() const { return *condition_; }

  friend bool operator==(const NegatedCondition& lhs,
                         const NegatedCondition& rhs);

  friend bool operator!=(const NegatedCondition& lhs,
                         const NegatedCondition& rhs);

  template <typename H>
  friend H AbslHashValue(H h, const NegatedCondition& c) {
    return H::combine(
        std::move(h),
        kNegatedConditionId,  // to distinguish from the contained condition
        *c.condition_);
  }

 private:
  // Cannot be just of type Condition since this type is not fully defined until
  // this class is defined.
  std::unique_ptr<Condition> condition_;
};

inline bool operator==(const ConjunctionCondition& lhs,
                       const ConjunctionCondition& rhs) {
  return lhs.operation_ == rhs.operation_ && lhs.conditions_ == rhs.conditions_;
}

inline bool operator!=(const ConjunctionCondition& lhs,
                       const ConjunctionCondition& rhs) {
  return !(lhs == rhs);
}

inline bool operator==(const NegatedCondition& lhs,
                       const NegatedCondition& rhs) {
  return *lhs.condition_ == *rhs.condition_;
}

inline bool operator!=(const NegatedCondition& lhs,
                       const NegatedCondition& rhs) {
  return !(lhs == rhs);
}

// Creates an AllOf condition from the given conditions.
ConjunctionCondition AllOf(absl::Span<const Condition> conditions);

// Creates an AnyOf condition from the given conditions.
ConjunctionCondition AnyOf(absl::Span<const Condition> conditions);

// Creates a negated condition of the given condition.
NegatedCondition Not(const Condition& condition);

// Creates a ConjunctionCondition from proto representation.
absl::StatusOr<ConjunctionCondition> FromProto(
    const intrinsic_proto::icon::ConjunctionCondition& proto);

// Converts a ConjunctionCondition to proto representation.
intrinsic_proto::icon::ConjunctionCondition ToProto(
    const ConjunctionCondition& condition);

intrinsic_proto::icon::NegatedCondition ToProto(
    const NegatedCondition& condition);

// Creates a Condition from proto representation.
absl::StatusOr<Condition> FromProto(
    const intrinsic_proto::icon::Condition& proto);

absl::StatusOr<NegatedCondition> FromProto(
    const intrinsic_proto::icon::NegatedCondition& proto);

// Converts a Condition to proto representation.
intrinsic_proto::icon::Condition ToProto(const Condition& condition);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_CC_CLIENT_CONDITION_H_
