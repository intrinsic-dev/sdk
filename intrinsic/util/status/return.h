// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_RETURN_H_
#define INTRINSIC_UTIL_STATUS_RETURN_H_

#include <type_traits>
#include <utility>

#include "absl/status/status.h"

namespace intrinsic {
namespace return_internal {
template <typename T>
struct ReturnImpl;
}  // namespace return_internal

template <typename T>
return_internal::ReturnImpl<std::decay_t<T>> Return(T&& value);

class ReturnVoid {
 public:
  void operator()(const absl::Status& s) const {}
};

namespace return_internal {
template <typename T>
struct ReturnImpl {
  T value;
  T operator()(const absl::Status& s) const& { return value; }
  T operator()(const absl::Status& s) && { return std::move(value); }
};
}  // namespace return_internal

template <typename T>
inline return_internal::ReturnImpl<std::decay_t<T>> Return(T&& value) {
  return return_internal::ReturnImpl<std::decay_t<T>>{std::forward<T>(value)};
}
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_RETURN_H_
