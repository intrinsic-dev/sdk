// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_KINEMATICS_TYPES_STATE_RN_H_
#define INTRINSIC_KINEMATICS_TYPES_STATE_RN_H_

#include "Eigen/Core"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/util/aggregate_type.h"

namespace intrinsic {

namespace state_rn_details {

// Helper macro for accessing a named data member from `data()` call
#define CREATE_STATE_RN_BASE(CLASS_NAME, TYPE, VAR_NAME) \
  template <int N = eigenmath::MAX_EIGEN_VECTOR_SIZE>    \
  struct CLASS_NAME {                                    \
    TYPE<N> VAR_NAME;                                    \
                                                         \
   protected:                                            \
    TYPE<N>& value() { return VAR_NAME; }                \
    const TYPE<N>& value() const { return VAR_NAME; }    \
  }

// use trivial derived types here so we can use the class type to set to
// -inf or inf directly
template <int N = eigenmath::MAX_EIGEN_VECTOR_SIZE>
struct MinVectorNd : public eigenmath::VectorNdWithMaxSize<N> {
  using eigenmath::VectorNdWithMaxSize<N>::VectorNdWithMaxSize;
};
template <int N = eigenmath::MAX_EIGEN_VECTOR_SIZE>
struct MaxVectorNd : public eigenmath::VectorNdWithMaxSize<N> {
  using eigenmath::VectorNdWithMaxSize<N>::VectorNdWithMaxSize;
};

CREATE_STATE_RN_BASE(StateRnBaseP, eigenmath::VectorNdWithMaxSize, position);
CREATE_STATE_RN_BASE(StateRnBaseV, eigenmath::VectorNdWithMaxSize, velocity);
CREATE_STATE_RN_BASE(StateRnBaseA, eigenmath::VectorNdWithMaxSize,
                     acceleration);
CREATE_STATE_RN_BASE(StateRnBaseJ, eigenmath::VectorNdWithMaxSize, jerk);
CREATE_STATE_RN_BASE(StateRnBaseT, eigenmath::VectorNdWithMaxSize, torque);

#undef CREATE_STATE_RN_BASE

}  // namespace state_rn_details

template <int N, typename... Bases>
struct StateRn : AggregateType<Bases...> {
  using AggregateType<Bases...>::AggregateType;

  static StateRn Zero(Eigen::Index size) {
    StateRn state;
    CHECK_OK(state.SetSize(size));
    return state;
  }

  Eigen::Index size() const {
    using B = std::tuple_element_t<0, std::tuple<Bases...>>;
    return B::value().rows();
  }

  bool IsSizeConsistent() const {
    const Eigen::Index size = this->size();
    return ((Bases::value().rows() == size) && ...);
  }

  icon::RealtimeStatus SetSize(Eigen::Index size) {
    if (size > N) {
      return icon::InvalidArgumentError(icon::RealtimeStatus::StrCat(
          "MAX_EIGEN_VECTOR_SIZE set to ", N, ", but dof= ", size));
    }
    (Bases::value().resize(size), ...);
    (Bases::value().setConstant(0.), ...);
    return icon::OkStatus();
  }
};

using StateRnP =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>>;
using StateRnV =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseV<>>;
using StateRnA =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseA<>>;
using StateRnJ =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseJ<>>;
using StateRnT =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseT<>>;
using StateRnPV =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>,
            state_rn_details::StateRnBaseV<>>;
using StateRnPA =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>,
            state_rn_details::StateRnBaseA<>>;

// Joint state (PVA) where the limits have the given maximum size
template <int N = eigenmath::MAX_EIGEN_VECTOR_SIZE>
using StateRnPVAWithMaxSize = StateRn<N, state_rn_details::StateRnBaseP<N>,
                                      state_rn_details::StateRnBaseV<N>,
                                      state_rn_details::StateRnBaseA<N>>;
// default version using MAX_EIGEN_MATRIX_SIZE
using StateRnPVA = StateRnPVAWithMaxSize<eigenmath::MAX_EIGEN_VECTOR_SIZE>;

using StateRnPVT =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>,
            state_rn_details::StateRnBaseV<>, state_rn_details::StateRnBaseT<>>;
using StateRnPVAJ =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>,
            state_rn_details::StateRnBaseV<>, state_rn_details::StateRnBaseA<>,
            state_rn_details::StateRnBaseJ<>>;
using StateRnPVAT =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseP<>,
            state_rn_details::StateRnBaseV<>, state_rn_details::StateRnBaseA<>,
            state_rn_details::StateRnBaseT<>>;
using StateRnVA =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseV<>,
            state_rn_details::StateRnBaseA<>>;
using StateRnVAJ =
    StateRn<eigenmath::MAX_EIGEN_VECTOR_SIZE, state_rn_details::StateRnBaseV<>,
            state_rn_details::StateRnBaseA<>, state_rn_details::StateRnBaseJ<>>;

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_STATE_RN_H_
