// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_KINEMATICS_TYPES_JOINT_STATE_H_
#define INTRINSIC_KINEMATICS_TYPES_JOINT_STATE_H_

#include "intrinsic/kinematics/types/state_rn.h"

namespace intrinsic {

// A collection of convenience typedefs for joint states as Euclidean states.
using JointStateP = StateRnP;
using JointStateV = StateRnV;
using JointStateA = StateRnA;
using JointStateJ = StateRnJ;
using JointStateT = StateRnT;
using JointStatePV = StateRnPV;
using JointStatePA = StateRnPA;
using JointStatePVA = StateRnPVA;
using JointStatePVT = StateRnPVT;
using JointStatePVAJ = StateRnPVAJ;
using JointStatePVAT = StateRnPVAT;
using JointStateVAJ = StateRnVAJ;

template <int N = eigenmath::MAX_EIGEN_VECTOR_SIZE>
using JointStatePVAWithMaxSize = StateRnPVAWithMaxSize<N>;

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_JOINT_STATE_H_
