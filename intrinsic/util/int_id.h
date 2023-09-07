// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

//
// IntId<T> is a simple template class mechanism for defining "logical"
// integer-like class types that support almost all of the same comparison
// operations  as native integer types, but which prevents assignment,
// construction, and other operations from other integer-like types.  In other
// words, you cannot assign from raw integer types or other IntId<> types, nor
// can you do most arithmetic or logical operations.
//
// A IntId<T> should compile away to a raw T in optimized mode.  What this means
// is that the generated assembly for:
//
//   int64 foo = 123;
//   int64 bar = 456;
//   int64 baz = foo + bar;
//   constexpr int64 fubar = 789;
//
// ...should be identical to the generated assembly for:
//
//    INTRINSIC_DEFINE_INT_ID_TYPE(MyIntId, int64);
//    MyIntId foo(123);
//    MyIntId bar(456);
//    MyIntId baz = foo + bar;
//    constexpr MyIntId fubar(789);
//
// Since the methods are all inline and non-virtual and the class has just
// one data member, the compiler can erase the IntId class entirely in its
// code-generation phase.  This also means that you can pass IntId<T>
// around by value just as you would a raw T.
//
// It is important to note that IntId does NOT generate compile time
// warnings or errors for overflows on implicit constant conversions.
// For example, the below demonstrates a case where the 2 are not equivalent
// at compile time and can lead to subtle initialization bugs:
//
//    INTRINSIC_DEFINE_INT_ID_TYPE(MyIntId8, int8);
//    int8 foo = 1024;        // Compile error: const conversion to ...
//    MyIntId8 foo(1024); // Compiles ok: foo has undefined / 0 value.
//
// Usage:
//   INTRINSIC_DEFINE_INT_ID_TYPE(Name, NativeType);
//
//     Defines a new IntId type named 'Name' in the current namespace with
//     no validation of operations.
//
//     Name: The desired name for the new IntId typedef.  Must be unique
//         within the current namespace.
//     NativeType: The primitive integral type this IntId will hold, as
//         defined by std::numeric_limits::is_integer (see <type_traits>).
//
//   This class also provides a .value() accessor method and defines a hash
//   functor that allows the IntType to be used as key to hashable containers.
//
// When creating a new int id type, it's suggested that you tell iwyu to export
// the int_id.h header in the header where you define the new type, to avoid
// unexpected inclusions in dependents. For example, in my_int.h do:
//
// #include "intrinsic/util/int_id.h" // IWYU pragma: export
//
// INTRINSIC_DEFINE_INT_ID_TYPE(my_int, int64_t);

#ifndef INTRINSIC_UTIL_INT_ID_H_
#define INTRINSIC_UTIL_INT_ID_H_

#include <cstdint>
#include <functional>
#include <iosfwd>
#include <limits>
#include <ostream>
#include <type_traits>
#include <utility>

#include "absl/meta/type_traits.h"
#include "absl/strings/string_view.h"

namespace intrinsic {

// Holds an integer value (of type NativeType) and behaves as a NativeType by
// exposing assignment, unary, comparison, and arithmetic operators.
//
// This class is thread-compatible.
template <typename TagType, typename NativeType>
class IntId {
 public:
  using ValueType = NativeType;

  static constexpr absl::string_view TypeName() { return TagType::TypeName(); }

  // Default value initialization.
  constexpr IntId() : value_(NativeType()) {}

  // Explicit initialization from another IntId type that has an
  // implementation of:
  //
  //    ToType IntIdConvert(FromType source, ToType*);
  //
  // This uses Argument Dependent Lookup (ADL) to find which function to
  // call.
  //
  // Example: Assume you have two IntId types.
  //
  //      INTRINSIC_DEFINE_INT_ID_TYPE(Bytes, int64);
  //      INTRINSIC_DEFINE_INT_ID_TYPE(Megabytes, int64);
  //
  //  If you want to be able to (explicitly) construct an instance of Bytes from
  //  an instance of Megabytes, simply define a converter function in the same
  //  namespace as either Bytes or Megabytes (or both):
  //
  //      Megabytes IntIdConvert(Bytes arg, Megabytes* /* unused */) {
  //        return Megabytes((arg >> 20).value());
  //      };
  //
  //  The second argument is needed to differentiate conversions, and it always
  //  passed as NULL.
  template <typename ArgTagType, typename ArgNativeType>
  explicit constexpr IntId(IntId<ArgTagType, ArgNativeType> arg)
      // We have to pass both the "from" type and the "to" type as args for the
      // conversions to be differentiated.  The converter can not be a template
      // because explicit template call syntax defeats ADL.
      : value_(IntIdConvert(arg, static_cast<IntId *>(nullptr)).value()) {}

  // Explicit initialization from a numeric primitive.
  template <class T, class = std::enable_if_t<std::is_same<
                         decltype(static_cast<ValueType>(std::declval<T>())),
                         ValueType>::value>>
  explicit constexpr IntId(T init_value)
      : value_(static_cast<ValueType>(init_value)) {}

  // Accesses the raw value.
  constexpr ValueType value() const { return value_; }

  // Accesses the raw value, with cast.
  // Primarily for compatibility with int-type.h
  template <typename ValType>
  constexpr ValType value() const {
    return static_cast<ValType>(value_);
  }

  // Explicitly cast the raw value only if the underlying value is convertible
  // to T.
  template <
      typename T,
      typename = absl::enable_if_t<absl::conjunction<
          std::integral_constant<bool, std::numeric_limits<T>::is_integer>,
          std::is_convertible<ValueType, T>>::value>>
  constexpr explicit operator T() const {
    return value_;
  }

  // Metadata functions.
  static constexpr IntId Max() {
    return IntId(std::numeric_limits<ValueType>::max());
  }
  static constexpr IntId Min() {
    return IntId(std::numeric_limits<ValueType>::min());
  }

  template <typename H>
  friend H AbslHashValue(H h, const IntId &i) {
    return H::combine(std::move(h), i.value_);
  }

 private:
  // The integer value of type ValueType.
  ValueType value_;

  static_assert(std::numeric_limits<ValueType>::is_integer,
                "invalid integer type for int id");
};

// Provide the << operator, primarily for logging purposes.
template <typename TagType, typename ValueType>
std::ostream &operator<<(std::ostream &os, IntId<TagType, ValueType> arg) {
  return os << arg.value();
}

// Provide the << operator, primarily for logging purposes. Specialized for int8
// so that an integer and not a character is printed.
template <typename TagType>
std::ostream &operator<<(std::ostream &os, IntId<TagType, int8_t> arg) {
  return os << static_cast<int>(arg.value());
}

// Provide the << operator, primarily for logging purposes. Specialized for
// uint8 so that an integer and not a character is printed.
template <typename TagType>
std::ostream &operator<<(std::ostream &os, IntId<TagType, uint8_t> arg) {
  return os << static_cast<unsigned int>(arg.value());
}

// Define comparison operators.  We allow all comparison operators.
#define INTRINSIC_INT_ID_COMPARISON_OP(op)                    \
  template <typename TagType, typename ValueType>             \
  constexpr bool operator op(IntId<TagType, ValueType> lhs,   \
                             IntId<TagType, ValueType> rhs) { \
    return lhs.value() op rhs.value();                        \
  }
INTRINSIC_INT_ID_COMPARISON_OP(==);  // NOLINT(whitespace/operators)
INTRINSIC_INT_ID_COMPARISON_OP(!=);  // NOLINT(whitespace/operators)
INTRINSIC_INT_ID_COMPARISON_OP(<);   // NOLINT(whitespace/operators)
INTRINSIC_INT_ID_COMPARISON_OP(<=);  // NOLINT(whitespace/operators)
INTRINSIC_INT_ID_COMPARISON_OP(>);   // NOLINT(whitespace/operators)
INTRINSIC_INT_ID_COMPARISON_OP(>=);  // NOLINT(whitespace/operators)
#undef INTRINSIC_INT_ID_COMPARISON_OP

// Type trait for detecting if a type T is a IntId type.
template <typename T>
struct IsIntId : public std::false_type {};

template <typename... Ts>
struct IsIntId<IntId<Ts...>> : public std::true_type {};

}  // namespace intrinsic

// Defines the IntId using value_type and typedefs it to type_name, with no
// validation of under/overflow situations.
// The struct int_type_name ## _tag_ trickery is needed to ensure that a new
// type is created per type_name.
#define INTRINSIC_DEFINE_INT_ID_TYPE(type_name, value_type)              \
  struct type_name##_strong_int_tag_ {                                   \
    static constexpr absl::string_view TypeName() { return #type_name; } \
  };                                                                     \
  typedef ::intrinsic::IntId<type_name##_strong_int_tag_, value_type> type_name;

namespace std {

// Allow IntId to be used as a key to hashable containers.
template <typename Tag, typename Value>
struct hash<intrinsic::IntId<Tag, Value>>
    : ::intrinsic::IntId<Tag, Value>::Hasher {};

// Numeric_limits override for strong int.
template <typename TagType, typename NativeType>
struct numeric_limits<intrinsic::IntId<TagType, NativeType>> {
 private:
  using IntIdT = intrinsic::IntId<TagType, NativeType>;

 public:
  static constexpr bool is_specialized = true;
  static constexpr bool is_signed = numeric_limits<NativeType>::is_signed;
  static constexpr bool is_integer = numeric_limits<NativeType>::is_integer;
  static constexpr bool is_exact = numeric_limits<NativeType>::is_exact;
  static constexpr bool has_infinity = numeric_limits<NativeType>::has_infinity;
  static constexpr bool has_quiet_NaN =
      numeric_limits<NativeType>::has_quiet_NaN;
  static constexpr bool has_signaling_NaN =
      numeric_limits<NativeType>::has_signaling_NaN;
  static constexpr float_denorm_style has_denorm =
      numeric_limits<NativeType>::has_denorm;
  static constexpr bool has_denorm_loss =
      numeric_limits<NativeType>::has_denorm_loss;
  static constexpr float_round_style round_style =
      numeric_limits<NativeType>::round_style;
  static constexpr bool is_iec559 = numeric_limits<NativeType>::is_iec559;
  static constexpr bool is_bounded = numeric_limits<NativeType>::is_bounded;
  static constexpr bool is_modulo = numeric_limits<NativeType>::is_modulo;
  static constexpr int digits = numeric_limits<NativeType>::digits;
  static constexpr int digits10 = numeric_limits<NativeType>::digits10;
  static constexpr int max_digits10 = numeric_limits<NativeType>::max_digits10;
  static constexpr int radix = numeric_limits<NativeType>::radix;
  static constexpr int min_exponent = numeric_limits<NativeType>::min_exponent;
  static constexpr int min_exponent10 =
      numeric_limits<NativeType>::min_exponent10;
  static constexpr int max_exponent = numeric_limits<NativeType>::max_exponent;
  static constexpr int max_exponent10 =
      numeric_limits<NativeType>::max_exponent10;
  static constexpr bool traps = numeric_limits<NativeType>::traps;
  static constexpr bool tinyness_before =
      numeric_limits<NativeType>::tinyness_before;

  static constexpr IntIdT(min)() { return IntIdT(IntIdT::Min()); }
  static constexpr IntIdT lowest() { return IntIdT(IntIdT::Min()); }
  static constexpr IntIdT(max)() { return IntIdT(IntIdT::Max()); }
  static constexpr IntIdT epsilon() { return IntIdT(); }
  static constexpr IntIdT round_error() { return IntIdT(); }
  static constexpr IntIdT infinity() { return IntIdT(); }
  static constexpr IntIdT quiet_NaN() { return IntIdT(); }
  static constexpr IntIdT signaling_NaN() { return IntIdT(); }
  static constexpr IntIdT denorm_min() { return IntIdT(); }
};

}  // namespace std

#endif  // INTRINSIC_UTIL_INT_ID_H_
