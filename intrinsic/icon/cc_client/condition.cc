// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/cc_client/condition.h"

#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/types/span.h"
#include "google/protobuf/message.h"
#include "google/protobuf/text_format.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {
namespace icon {

namespace {
// Helper for variant visitors.
template <class T>
struct always_false : std::false_type {};

// Helper for text formatting a proto into a string.
std::string ProtoToString(const google::protobuf::Message& message) {
  std::string out;
  if (!google::protobuf::TextFormat::PrintToString(message, &out)) {
    return "(could not serialize proto)";
  }
  return out;
}
}  // namespace

Comparison::Comparison(absl::string_view state_variable_name,
                       intrinsic_proto::icon::Comparison::OpEnum operation,
                       ComparisonValue value, double max_abs_error)
    : state_variable_name_(state_variable_name),
      operation_(operation),
      value_(value),
      max_abs_error_(max_abs_error) {}

Comparison::Comparison(absl::string_view state_variable_name,
                       BooleanOperator operation, bool value)
    : state_variable_name_(state_variable_name),
      // Validity of static_cast is tested in condition_test.cc
      operation_(
          static_cast<intrinsic_proto::icon::Comparison::OpEnum>(operation)),
      value_(value),
      max_abs_error_(kDefaultMaxAbsError) {}

Comparison::Comparison(absl::string_view state_variable_name,
                       FloatOperator operation, double value,
                       double max_abs_error)
    : state_variable_name_(state_variable_name),
      // Validity of static_cast is tested in condition_test.cc
      operation_(
          static_cast<intrinsic_proto::icon::Comparison::OpEnum>(operation)),
      value_(value),
      max_abs_error_(max_abs_error) {}

Comparison::Comparison(absl::string_view state_variable_name,
                       IntOperator operation, int64_t value)
    : state_variable_name_(state_variable_name),
      // Validity of static_cast is tested in condition_test.cc
      operation_(
          static_cast<intrinsic_proto::icon::Comparison::OpEnum>(operation)),
      value_(value),
      max_abs_error_(kDefaultMaxAbsError) {}

absl::string_view Comparison::state_variable_name() const {
  return state_variable_name_;
}

// static
absl::StatusOr<Comparison> Comparison::Create(
    absl::string_view state_variable_name,
    intrinsic_proto::icon::Comparison::OpEnum operation, ComparisonValue value,
    double max_abs_error) {
  if (std::holds_alternative<bool>(value)) {
    if (!(operation == intrinsic_proto::icon::Comparison::EQUAL ||
          operation == intrinsic_proto::icon::Comparison::NOT_EQUAL)) {
      return absl::InvalidArgumentError(absl::StrCat(
          "Cannot create Condition for state variable \"", state_variable_name,
          "\": boolean value is incompatible with operation \"",
          intrinsic_proto::icon::Comparison_OpEnum_Name(operation), "\""));
    }
  } else if (std::holds_alternative<double>(value)) {
    if (operation == intrinsic_proto::icon::Comparison::EQUAL ||
        operation == intrinsic_proto::icon::Comparison::NOT_EQUAL) {
      return absl::InvalidArgumentError(absl::StrCat(
          "Cannot create Condition for state variable \"", state_variable_name,
          "\": double value is incompatible with operation \"",
          intrinsic_proto::icon::Comparison_OpEnum_Name(operation),
          "\" Use Approx-Comparison."));
    }
  } else if (std::holds_alternative<int64_t>(value)) {
    if (operation == intrinsic_proto::icon::Comparison::APPROX_EQUAL ||
        operation == intrinsic_proto::icon::Comparison::APPROX_NOT_EQUAL) {
      return absl::InvalidArgumentError(absl::StrCat(
          "Cannot create Condition for state variable \"", state_variable_name,
          "\": integer value is incompatible with operation \"",
          intrinsic_proto::icon::Comparison_OpEnum_Name(operation),
          "\". Use Equal-Comparison."));
    }
  }
  return Comparison(state_variable_name, operation, value, max_abs_error);
}

absl::StatusOr<Comparison> FromProto(
    const intrinsic_proto::icon::Comparison& proto) {
  ComparisonValue value;
  switch (proto.value_case()) {
    case intrinsic_proto::icon::Comparison::kDoubleValue:
      value = proto.double_value();
      break;
    case intrinsic_proto::icon::Comparison::kInt64Value:
      value = proto.int64_value();
      break;
    case intrinsic_proto::icon::Comparison::kBoolValue:
      value = proto.bool_value();
      break;
    default:
      return absl::InvalidArgumentError(absl::StrCat(
          "Cannot create Condition from proto: value not set or has "
          "unsupported type: proto=",
          ProtoToString(proto)));
  }
  return Comparison::Create(proto.state_variable_name(), proto.operation(),
                            value, proto.max_abs_error());
}

intrinsic_proto::icon::Comparison ToProto(const Comparison& condition) {
  intrinsic_proto::icon::Comparison out;
  out.set_state_variable_name(std::string(condition.state_variable_name()));
  out.set_operation(condition.operation());
  out.set_max_abs_error(condition.max_abs_error());
  std::visit(
      [&out](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same<T, bool>::value) {
          out.set_bool_value(arg);
        } else if constexpr (std::is_same<T, double>::value) {
          out.set_double_value(arg);
        } else if constexpr (std::is_same<T, int64_t>::value) {
          out.set_int64_value(arg);
        } else {
          static_assert(always_false<T>::value, "non-exhaustive visitor!");
        }
      },
      condition.value());
  return out;
}

Comparison IsTrue(absl::string_view state_variable_name) {
  return Comparison(state_variable_name, Comparison::BooleanOperator::kEqual,
                    true);
}

Comparison IsFalse(absl::string_view state_variable_name) {
  // Should never fail.
  return Comparison(state_variable_name, Comparison::BooleanOperator::kEqual,
                    false);
}

Comparison IsEqual(absl::string_view state_variable_name, int64_t value) {
  return Comparison(state_variable_name, Comparison::IntOperator::kEqual,
                    value);
}

Comparison IsNotEqual(absl::string_view state_variable_name, int64_t value) {
  return Comparison(state_variable_name, Comparison::IntOperator::kNotEqual,
                    value);
}

Comparison IsLessThanOrEqual(absl::string_view state_variable_name,
                             int64_t value) {
  return Comparison(state_variable_name,
                    Comparison::IntOperator::kLessThanOrEqual, value);
}

Comparison IsLessThan(absl::string_view state_variable_name, int64_t value) {
  return Comparison(state_variable_name, Comparison::IntOperator::kLessThan,
                    value);
}

Comparison IsGreaterThanOrEqual(absl::string_view state_variable_name,
                                int64_t value) {
  return Comparison(state_variable_name,
                    Comparison::IntOperator::kGreaterThanOrEqual, value);
}

Comparison IsGreaterThan(absl::string_view state_variable_name, int64_t value) {
  return Comparison(state_variable_name, Comparison::IntOperator::kGreaterThan,
                    value);
}

Comparison IsApprox(absl::string_view state_variable_name, double value,
                    double max_abs_error) {
  return Comparison(state_variable_name,
                    Comparison::FloatOperator::kApproxEqual, value,
                    max_abs_error);
}

Comparison IsNotApprox(absl::string_view state_variable_name, double value,
                       double max_abs_error) {
  return Comparison(state_variable_name,
                    Comparison::FloatOperator::kApproxNotEqual, value,
                    max_abs_error);
}

Comparison IsLessThanOrEqual(absl::string_view state_variable_name,
                             double value) {
  return Comparison(state_variable_name,
                    Comparison::FloatOperator::kLessThanOrEqual, value);
}

Comparison IsLessThan(absl::string_view state_variable_name, double value) {
  return Comparison(state_variable_name, Comparison::FloatOperator::kLessThan,
                    value);
}

Comparison IsGreaterThanOrEqual(absl::string_view state_variable_name,
                                double value) {
  return Comparison(state_variable_name,
                    Comparison::FloatOperator::kGreaterThanOrEqual, value);
}

Comparison IsGreaterThan(absl::string_view state_variable_name, double value) {
  return Comparison(state_variable_name,
                    Comparison::FloatOperator::kGreaterThan, value);
}

namespace {
struct ToProtoVisitor {
  template <typename T>
  intrinsic_proto::icon::Condition operator()(const T&);
};

template <>
intrinsic_proto::icon::Condition ToProtoVisitor::operator()(
    const Comparison& c) {
  intrinsic_proto::icon::Condition result;
  *result.mutable_comparison() = ToProto(c);
  return result;
}

template <>
intrinsic_proto::icon::Condition ToProtoVisitor::operator()(
    const ConjunctionCondition& c) {
  intrinsic_proto::icon::Condition result;
  *result.mutable_conjunction_condition() = ToProto(c);
  return result;
}

template <>
intrinsic_proto::icon::Condition ToProtoVisitor::operator()(
    const NegatedCondition& c) {
  intrinsic_proto::icon::Condition result;
  *result.mutable_negated_condition() = ToProto(c);
  return result;
}
}  // namespace

intrinsic_proto::icon::Condition ToProto(const Condition& condition) {
  return std::visit(ToProtoVisitor(), condition);
}

absl::StatusOr<Condition> FromProto(
    const intrinsic_proto::icon::Condition& proto) {
  switch (proto.condition_case()) {
    case (intrinsic_proto::icon::Condition::kComparison):
      return FromProto(proto.comparison());
    case (intrinsic_proto::icon::Condition::kConjunctionCondition):
      return FromProto(proto.conjunction_condition());
    default:
      return absl::InvalidArgumentError("Unhandled condition type.");
  }
}

ConjunctionCondition::ConjunctionCondition(
    ConjunctionCondition::Operation operation,
    absl::Span<const Condition> conditions)
    : operation_(operation),
      conditions_(conditions.begin(), conditions.end()) {}

const std::vector<Condition>& ConjunctionCondition::GetConditions() const {
  return conditions_;
}

ConjunctionCondition::Operation ConjunctionCondition::GetOperation() const {
  return operation_;
}

NegatedCondition::NegatedCondition(const Condition& condition) {
  condition_ = std::make_unique<Condition>(condition);
}

NegatedCondition::NegatedCondition(Condition&& condition) {
  condition_ = std::make_unique<Condition>(std::move(condition));
}

NegatedCondition::NegatedCondition(const NegatedCondition& condition) {
  *this = condition;
}

NegatedCondition& NegatedCondition::operator=(
    const NegatedCondition& condition) {
  this->condition_ = std::make_unique<Condition>(*condition.condition_);
  return *this;
}

intrinsic_proto::icon::ConjunctionCondition ToProto(
    const ConjunctionCondition& condition) {
  intrinsic_proto::icon::ConjunctionCondition result;
  result.set_operation(
      static_cast<intrinsic_proto::icon::ConjunctionCondition::OpEnum>(
          condition.GetOperation()));
  for (const auto& c : condition.GetConditions()) {
    *result.add_conditions() = ToProto(c);
  }
  return result;
}

absl::StatusOr<ConjunctionCondition> FromProto(
    const intrinsic_proto::icon::ConjunctionCondition& proto) {
  std::vector<Condition> conditions;
  for (const auto& c : proto.conditions()) {
    INTRINSIC_ASSIGN_OR_RETURN(auto case_value, FromProto(c));
    conditions.emplace_back(case_value);
  }
  return ConjunctionCondition(
      static_cast<ConjunctionCondition::Operation>(proto.operation()),
      conditions);
}

ConjunctionCondition AllOf(absl::Span<const Condition> conditions) {
  return ConjunctionCondition(ConjunctionCondition::Operation::kAllOf,
                              conditions);
}

ConjunctionCondition AnyOf(absl::Span<const Condition> conditions) {
  return ConjunctionCondition(ConjunctionCondition::Operation::kAnyOf,
                              conditions);
}

NegatedCondition Not(const Condition& condition) {
  return NegatedCondition(condition);
}

intrinsic_proto::icon::NegatedCondition ToProto(
    const NegatedCondition& condition) {
  intrinsic_proto::icon::NegatedCondition result;
  *result.mutable_condition() = ToProto(condition.GetCondition());
  return result;
}

}  // namespace icon
}  // namespace intrinsic
