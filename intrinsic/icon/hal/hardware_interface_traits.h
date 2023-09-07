// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_TRAITS_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_TRAITS_H_

#include <type_traits>

namespace intrinsic::icon {
namespace hardware_interface_traits {

// Builder functions for creating a new default-initialized hardware interface.
// Each template specialization is ressponsible for defining a build function
// according to their respective `*utils.h` header.
template <class HardwareInterfaceT>
struct BuilderFunctions : std::false_type {};

// Transition struct to translate from a flatbuffer to a unique URI.
template <class T>
struct TypeID;

// The macro belows allows to register a hardware interface to be used by a
// hardware module. Given the type `INTERFACE_T`, it specifies a function on how
// to construct the message via `BUILDER_FCN` as well as a unique string
// (`TYPE_ID_STRING`) identifying the type of the message.
#define INTRINSIC_ADD_HARDWARE_INTERFACE(INTERFACE_T, BUILDER_FCN, \
                                         TYPE_ID_STRING)           \
  template <>                                                      \
  struct BuilderFunctions<INTERFACE_T> : std::true_type {          \
    static constexpr auto kBuild = BUILDER_FCN;                    \
  };                                                               \
                                                                   \
  template <>                                                      \
  struct TypeID<INTERFACE_T> {                                     \
    static constexpr char kTypeString[] = TYPE_ID_STRING;          \
  };

}  // namespace hardware_interface_traits
}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_TRAITS_H_
