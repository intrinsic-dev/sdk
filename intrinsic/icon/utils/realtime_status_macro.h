// Copyright 2023 Intrinsic Innovation LLC

// Helper macros and methods to return and propagate errors with RealtimeStatus
// and RealtimeStatusOr
//
// NOTE: This file uses "expression statement" syntax which is a non-standard
//       language extension.
//
// Public macros in this file are created with formatting options. Most of the
// macros support up to ten arguments for the formatting, but unlimited can be
// used by using the _F equivalent of a macro.
#ifndef INTRINSIC_ICON_UTILS_REALTIME_STATUS_MACRO_H_
#define INTRINSIC_ICON_UTILS_REALTIME_STATUS_MACRO_H_

#include <utility>

#include "absl/base/optimization.h"
#include "intrinsic/icon/utils/fixed_str_cat.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
namespace icon {
namespace status_macro_internal {

// Assigning a status and comparing its value to
// ::intrinsic::icon::RealtimeStatus::OK in a conditional doesn't compile, so
// this class exists solely to convert ::intrinsic::icon::RealtimeStatus to
// bool.
class RealtimeStatusToBool {
 public:
  // Can't be marked explicit, the macro relies on implicit conversion.
  RealtimeStatusToBool(RealtimeStatus status) : status_(status) {}  // NOLINT

  explicit operator bool() const { return status_.ok(); }
  RealtimeStatus ToRealtimeStatus() { return status_; }

 private:
  RealtimeStatus status_;
};

}  // namespace status_macro_internal
}  // namespace icon
}  // namespace intrinsic

// Evaluates an expression that produces a RealtimeStatus.
// Returns RealtimeStatus from the current function if it is not OK.
//
// Equivalent declaration:
//  void INTRINSIC_RT_RETURN_IF_ERROR(RealtimeStatus expr);
//
// Example:
//    RealtimeStatus Bar();
//
//    RealtimeStatus Foo(int n) {
//      INTRINSIC_RT_RETURN_IF_ERROR(Bar(n));
//      return RealtimeStatus::OK;
//    }
#define INTRINSIC_RT_RETURN_IF_ERROR(expr)                             \
  do {                                                                 \
    if (::intrinsic::icon::status_macro_internal::RealtimeStatusToBool \
            converter = (expr)) {                                      \
    } else {                                                           \
      return converter.ToRealtimeStatus();                             \
    }                                                                  \
  } while (0)

// Generally similar to INTR_ASSIGN_OR_RETURN, but with different behavior for
// >=4 arguments. Leaks a _status_or_value# variable into the scope.
//
// For >= 4 arguments, concatenation of the status message is performed instead
// of formatting.
//
// Example:
// INTRINSIC_RT_ASSIGN_OR_RETURN(auto foo,
// RealtimeStatusOr(InvalidArgument("Foo")) "He", 110, " world") will return
// InvalidArgument("Foo; He110 world").
//
// If the lefthand side of the assignment has a ',' in it (for example, type is
// a template with multiple parameters), the expression can be wrapped in
// parenthesis.
//
// Example:
// INTRINSIC_RT_ASSIGN_OR_RETURN((std::map<int, int> my_map),
// MakeMapOrError(...)); Example: INTRINSIC_RT_ASSIGN_OR_RETURN((auto [a, b]),
// MakeTupleOrError(...));
//
// NOTE: This will not perform implicit conversions to create a RealtimeStatusOr
//       object, it only compiles for RealtimeStatusOr type.
#define INTRINSIC_RT_ASSIGN_OR_RETURN(...)                                \
  INTRINSIC_SELECT_STATUS_MACRO_IMPL__(                                   \
      __VA_ARGS__, INTRINSIC_RT_ASSIGN_OR_RETURN_F_,                      \
      INTRINSIC_RT_ASSIGN_OR_RETURN_F_, INTRINSIC_RT_ASSIGN_OR_RETURN_F_, \
      INTRINSIC_RT_ASSIGN_OR_RETURN_F_, INTRINSIC_RT_ASSIGN_OR_RETURN_F_, \
      INTRINSIC_RT_ASSIGN_OR_RETURN_F_, INTRINSIC_RT_ASSIGN_OR_RETURN_F_, \
      INTRINSIC_RT_ASSIGN_OR_RETURN_F_, INTRINSIC_RT_ASSIGN_OR_RETURN_F_, \
      INTRINSIC_RT_ASSIGN_OR_RETURN_F_, INTRINSIC_RT_ASSIGN_OR_RETURN_3_, \
      INTRINSIC_RT_ASSIGN_OR_RETURN_2_,                                   \
      INTRINSIC_RT_ASSIGN_OR_RETURN_CALLED_WITH_TOO_FEW_ARGUMENTS_1_)     \
  (INTRINSIC_STATUS_MACROS_CONCAT(_status_or_value, __LINE__), __VA_ARGS__)

#define INTRINSIC_RT_ASSIGN_OR_RETURN_2_(statusor, lhs, expr)             \
  auto statusor = (expr);                                                 \
  if (ABSL_PREDICT_FALSE(!statusor.ok())) {                               \
    return statusor.status();                                             \
  }                                                                       \
  INTRINSIC_RT_STATUS_MACROS_IMPL_UNPARENTHESIZE_IF_PARENTHESIZED_(lhs) = \
      std::move(statusor.value())

#define INTRINSIC_RT_ASSIGN_OR_RETURN_3_(statusor, lhs, expr, mesg)       \
  auto statusor = (expr);                                                 \
  if (ABSL_PREDICT_FALSE(!statusor.ok())) {                               \
    return ::intrinsic::icon::RealtimeStatus(                             \
        statusor.status().code(),                                         \
        ::intrinsic::icon::FixedStrCat<                                   \
            ::intrinsic::icon::RealtimeStatus::kMaxMessageLength>(        \
            mesg, "; ", statusor.status().message()));                    \
  }                                                                       \
  INTRINSIC_RT_STATUS_MACROS_IMPL_UNPARENTHESIZE_IF_PARENTHESIZED_(lhs) = \
      std::move(statusor.value())

#define INTRINSIC_RT_ASSIGN_OR_RETURN_F_(statusor, lhs, expr, mesg, ...)  \
  auto statusor = (expr);                                                 \
  if (ABSL_PREDICT_FALSE(!statusor.ok())) {                               \
    return ::intrinsic::icon::RealtimeStatus(                             \
        statusor.status().code(),                                         \
        ::intrinsic::icon::FixedStrCat<                                   \
            ::intrinsic::icon::RealtimeStatus::kMaxMessageLength>(        \
            mesg, __VA_ARGS__, "; ", statusor.status().message()));       \
  }                                                                       \
  INTRINSIC_RT_STATUS_MACROS_IMPL_UNPARENTHESIZE_IF_PARENTHESIZED_(lhs) = \
      std::move(statusor.value())

// Internal helpers for macro expansion.
#define INTRINSIC_RT_STATUS_MACROS_IMPL_EAT_(...)
#define INTRINSIC_RT_STATUS_MACROS_IMPL_REM_(...) __VA_ARGS__
#define INTRINSIC_RT_STATUS_MACROS_IMPL_EMPTY_()

// Internal helpers for emptyness arguments check. Expands to "0_" if empty and
// otherwise "1_".
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_(...) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_HELPER_((__VA_ARGS__, 0_, 1_))
// MSVC expands variadic macros incorrectly, so we need this extra indirection
// to work around that.
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_HELPER_(args) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_I_ args
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_I_(e0, e1, is_empty, \
                                                          ...)              \
  is_empty

#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_(...) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_I_(__VA_ARGS__)
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_I_(...) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_INNER_(_, ##__VA_ARGS__)

// Internal helpers for if statement.
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IF_1_(_Then, _Else) _Then
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IF_0_(_Then, _Else) _Else
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IF_(_Cond, _Then, _Else)             \
  INTRINSIC_STATUS_MACROS_CONCAT(INTRINSIC_RT_STATUS_MACROS_IMPL_IF_, _Cond) \
  (_Then, _Else)

// Expands to 1_ if the input is parenthesized. Otherwise expands to 0_.
#define INTRINSIC_RT_STATUS_MACROS_IMPL_IS_PARENTHESIZED_(...) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IS_EMPTY_(                   \
      INTRINSIC_RT_STATUS_MACROS_IMPL_EAT_ __VA_ARGS__)

// If the input is parenthesized, removes the parentheses. Otherwise expands to
// the input unchanged.
#define INTRINSIC_RT_STATUS_MACROS_IMPL_UNPARENTHESIZE_IF_PARENTHESIZED_(...) \
  INTRINSIC_RT_STATUS_MACROS_IMPL_IF_(                                        \
      INTRINSIC_RT_STATUS_MACROS_IMPL_IS_PARENTHESIZED_(__VA_ARGS__),         \
      INTRINSIC_RT_STATUS_MACROS_IMPL_REM_,                                   \
      INTRINSIC_RT_STATUS_MACROS_IMPL_EMPTY_())                               \
  __VA_ARGS__

// RealtimeStatus success comparison.
// This is better than CHECK((val).ok()) because the embedded
// error string gets printed by the CHECK_EQ.
#define INTRINSIC_RT_ASSIGN_OR_DIE(lhs, expr) \
  INTRINSIC_RT_ASSIGN_OR_DIE_IMPL_(           \
      INTRINSIC_STATUS_MACROS_CONCAT(_status_or_value, __LINE__), lhs, expr)

#define INTRINSIC_RT_ASSIGN_OR_DIE_IMPL_(result, lhs, expr)               \
  auto result = (expr);                                                   \
  CHECK_EQ(::intrinsic::icon::OkStatus(), result.status());               \
  INTRINSIC_RT_STATUS_MACROS_IMPL_UNPARENTHESIZE_IF_PARENTHESIZED_(lhs) = \
      std::move(result.value());

// This macro selects the correct version of a macro depending on the
// number of arguments (up to thirteen).
#define INTRINSIC_SELECT_STATUS_MACRO_IMPL__(one, two, three, four, five, six, \
                                             seven, eight, nine, ten, eleven,  \
                                             twelve, thirteen, name, ...)      \
  name

#define _INTRINSIC_STATUS_MACROS_CONCAT_INNER(x, y) x##y
#define INTRINSIC_STATUS_MACROS_CONCAT(x, y) \
  _INTRINSIC_STATUS_MACROS_CONCAT_INNER(x, y)

#endif  // INTRINSIC_ICON_UTILS_REALTIME_STATUS_MACRO_H_
