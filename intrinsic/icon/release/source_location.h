// Copyright 2023 Intrinsic Innovation LLC

// API for capturing source-code location information.
// Based on http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/n4519.pdf.
//
// To define a function that has access to the source location of the
// callsite, define it with a parameter of type `intrinsic::SourceLocation`. The
// caller can then invoke the function, passing `INTRINSIC_LOC` as the argument.
//
// If at all possible, make the `intrinsic::SourceLocation` parameter be the
// function's last parameter. That way, when `std::source_location` is
// available, you will be able to switch to it, and give the parameter a default
// argument of `std::source_location::current()`. Users will then be able to
// omit that argument, and the default will automatically capture the location
// of the callsite.

#ifndef INTRINSIC_ICON_RELEASE_SOURCE_LOCATION_H_
#define INTRINSIC_ICON_RELEASE_SOURCE_LOCATION_H_

#include <cstdint>

#include "absl/base/attributes.h"

namespace intrinsic {

// Class representing a specific location in the source code of a program.
// `intrinsic::SourceLocation` is copyable.
class SourceLocation {
  struct PrivateTag {
   private:
    explicit PrivateTag() = default;
    friend class SourceLocation;
  };

 public:
  // Avoid this constructor; it populates the object with dummy values.
  constexpr SourceLocation() : line_(0), file_name_(nullptr) {}

  // Wrapper to invoke the private constructor below. This should only be used
  // by the `INTRINSIC_LOC` macro, hence the name.
  static constexpr SourceLocation DoNotInvokeDirectly(
      std::uint_least32_t line,
      const char* file_name ABSL_ATTRIBUTE_LIFETIME_BOUND) {
    return SourceLocation(line, file_name);
  }

  // Creates a dummy `SourceLocation` of "<source_location>" at line number 1,
  // if no `SourceLocation::current()` implementation is available.
  // Use INTRINSIC_LOC instead (until std::source_location is available).
  static constexpr SourceLocation current() {
    return SourceLocation(1, "<no source_location>");
  }

  // The line number of the captured source location.
  constexpr std::uint_least32_t line() const { return line_; }

  // The file name of the captured source location.
  constexpr const char* file_name() const { return file_name_; }

  // `column()` and `function_name()` are omitted because we don't have a way to
  // support them.

 private:
  // Do not invoke this constructor directly. Instead, use the `INTRINSIC_LOC`
  // macro below.
  //
  // `file_name` must outlive all copies of the `intrinsic::SourceLocation`
  // object, so in practice it should be a string literal.
  constexpr SourceLocation(std::uint_least32_t line,
                           const char* file_name ABSL_ATTRIBUTE_LIFETIME_BOUND)
      : line_(line), file_name_(file_name) {}

  friend constexpr int UseUnused() {
    static_assert(SourceLocation(0, nullptr).unused_column_ == 0,
                  "Use the otherwise-unused member.");
    return 0;
  }

  // "unused" members are present to minimize future changes in the size of this
  // type.
  std::uint_least32_t line_;
  std::uint_least32_t unused_column_ = 0;
  const char* file_name_;
};

}  // namespace intrinsic

// If a function takes an `intrinsic::SourceLocation` parameter, pass this as
// the argument.
#define INTRINSIC_LOC \
  ::intrinsic::SourceLocation::DoNotInvokeDirectly(__LINE__, __FILE__)

#endif  // INTRINSIC_ICON_RELEASE_SOURCE_LOCATION_H_
