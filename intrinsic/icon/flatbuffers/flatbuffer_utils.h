// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_FLATBUFFERS_FLATBUFFER_UTILS_H_
#define INTRINSIC_ICON_FLATBUFFERS_FLATBUFFER_UTILS_H_

#include <cstddef>
#include <cstdint>

#include "flatbuffers/array.h"
namespace intrinsic_fbs {

// Helper function to get the number of elements of a flatbuffer struct's array
// member at compile time.
//
// This function takes a parameter `array_getter_ptr` of type
//                                             ╲
// const ArrayType* (FlatbufferStructT::*array_getter_ptr)() const
// └───────┬──────┘  └─────────┬────────┘                      │
//         │                   ├───────────────────────────────┘
//         │       pointer to const member function of FlatbufferStructT...
//         │
//  ...that returns const ArrayType*
//
// Usage:
//
// constexpr kMyArraySize =
//     FlatbufferArrayNumElements(
//         &::my::fbs::namespace::MyStruct::array_member);
//
// NOTE: You do *not* need to specify any of the template parameters, the
//       compiler can infer all three from the function pointer you pass into
//       this function.
template <typename FlatbufferStructT, typename ArrayT, uint16_t array_length>
constexpr size_t FlatbufferArrayNumElements(
    const flatbuffers::Array<ArrayT, array_length>* (
        FlatbufferStructT::*array_getter_ptr)() const) {
  return array_length;
}

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_FLATBUFFERS_FLATBUFFER_UTILS_H_
