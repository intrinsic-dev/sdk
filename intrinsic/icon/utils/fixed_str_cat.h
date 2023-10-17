// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_FIXED_STR_CAT_H_
#define INTRINSIC_ICON_UTILS_FIXED_STR_CAT_H_

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <initializer_list>

#include "absl/base/attributes.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/utils/fixed_string.h"

namespace intrinsic::icon {

namespace internal {

// NB: This differs slightly from the absl implementation by checking against
// MaxSize before resizing, and not attempting to copy past the end. To port to
// absl's exact algorithm we'd need to either implement a real-time safe
// allocator, possibly TLSF for more flexible real-time safe strings, or assert
// when MaxSize is exceeded. For now, we implement it this way for consistency
// with FixedString's constructor.
template <size_t MaxSize>
FixedString<MaxSize> CatPieces(
    std::initializer_list<absl::string_view> pieces) {
  FixedString<MaxSize> result;
  size_t total_size = 0;
  for (const absl::string_view& piece : pieces) {
    total_size += piece.size();
  }
  if (total_size == 0) {
    return result;
  }
  result.resize(std::min(MaxSize, total_size));

  char* const begin = &result[0];
  char* out = begin;
  for (const absl::string_view& piece : pieces) {
    const size_t current_size = out - begin;
    int num_chars_to_copy = piece.size();
    if (num_chars_to_copy + current_size > MaxSize) {
      num_chars_to_copy = MaxSize - current_size;
      if (num_chars_to_copy <= 0) {
        return result;
      }
    }

    if (num_chars_to_copy != 0) {
      memcpy(out, piece.data(), num_chars_to_copy);
      out += num_chars_to_copy;
    }
  }
  return result;
}

inline absl::string_view ToStringView(
    const absl::AlphaNum& a ABSL_ATTRIBUTE_LIFETIME_BOUND) {
  return a.Piece();
}

template <size_t MaxSize>
inline absl::string_view ToStringView(
    const FixedString<MaxSize>& a ABSL_ATTRIBUTE_LIFETIME_BOUND) {
  return a;
}

}  // namespace internal

// Concatenates pieces to create a new string. If the combined size of the
// pieces exceeds MaxSize, then excess pieces are dropped from the resulting
// string.
template <size_t MaxSize, typename... AV>
ABSL_MUST_USE_RESULT FixedString<MaxSize> FixedStrCat(const AV&... args) {
  return internal::CatPieces<MaxSize>({internal::ToStringView(args)...});
}

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_FIXED_STR_CAT_H_
