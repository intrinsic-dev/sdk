// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/aggregate_type.h"

#include <gtest/gtest.h>

#include <tuple>
#include <type_traits>

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {
namespace {

template <typename T, typename U>
using IsFront = aggregate_type_details::IsFrontOf<T, U>;
template <typename T, typename U>
using IsSubset = aggregate_type_details::IsSubsetOf<T, U>;
template <typename T, typename U>
using IsSequential = aggregate_type_details::IsSequentialSubsetOf<T, U>;

struct P {
  eigenmath::VectorNd position;
};
struct V {
  eigenmath::VectorNd velocity;
};
struct A {
  eigenmath::VectorNd acceleration;
};
struct J {
  eigenmath::VectorNd jerk;
};
struct T {
  eigenmath::VectorNd torque;
};

using JointStateP = AggregateType<P>;
using JointStateV = AggregateType<V>;
using JointStateVA = AggregateType<V, A>;
using JointStateVAJ = AggregateType<V, A, J>;
using JointStatePV = AggregateType<P, V>;
using JointStatePVA = AggregateType<P, V, A>;
using JointStatePVAJ = AggregateType<P, V, A, J>;
using JointStatePVT = AggregateType<P, V, T>;
using JointStatePVAT = AggregateType<P, V, A, T>;

TEST(AggregateTypesTest, ConstexprEvals) {
  struct A {};
  struct B {};
  struct C {};
  struct D {};

  EXPECT_TRUE((IsFront<std::tuple<>, std::tuple<>>::value));
  EXPECT_TRUE((IsFront<std::tuple<>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsFront<std::tuple<>, std::tuple<A, B>>::value));
  EXPECT_TRUE((IsFront<std::tuple<A>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsFront<std::tuple<A, B, C>, std::tuple<A, B, C>>::value));
  EXPECT_FALSE((IsFront<std::tuple<A>, std::tuple<>>::value));
  EXPECT_FALSE((IsFront<std::tuple<B, C>, std::tuple<A, B, C>>::value));

  EXPECT_TRUE((IsSubset<std::tuple<>, std::tuple<>>::value));
  EXPECT_TRUE((IsSubset<std::tuple<>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSubset<std::tuple<A>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSubset<std::tuple<A, C>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSubset<std::tuple<C, A>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSubset<std::tuple<C, B, A>, std::tuple<A, B, C>>::value));
  EXPECT_FALSE((IsSubset<std::tuple<A>, std::tuple<>>::value));
  EXPECT_FALSE((IsSubset<std::tuple<B, D>, std::tuple<A, B, C>>::value));

  EXPECT_TRUE((IsSequential<std::tuple<>, std::tuple<>>::value));
  EXPECT_TRUE((IsSequential<std::tuple<>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSequential<std::tuple<A>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSequential<std::tuple<B>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSequential<std::tuple<A, B>, std::tuple<A, B, C>>::value));
  EXPECT_TRUE((IsSequential<std::tuple<B, C>, std::tuple<A, B, C>>::value));
  EXPECT_FALSE((IsSequential<std::tuple<A>, std::tuple<>>::value));
  EXPECT_FALSE((IsSequential<std::tuple<D>, std::tuple<A, B, C>>::value));
  EXPECT_FALSE((IsSequential<std::tuple<C, D>, std::tuple<A, B, C>>::value));
  EXPECT_FALSE((IsSequential<std::tuple<B, A>, std::tuple<A, B, C>>::value));
}

// Test assignment from other classes using JointStatePV and JointStateP.
TEST(AggregateTypesTest, CopyConstruction) {
  // construction from superset
  EXPECT_TRUE((std::is_constructible_v<JointStateP, JointStatePV>));
  EXPECT_TRUE((std::is_constructible_v<JointStateV, JointStatePV>));
  EXPECT_TRUE((std::is_constructible_v<JointStatePV, JointStatePV>));
  EXPECT_TRUE((std::is_constructible_v<JointStatePVA, JointStatePVAJ>));
  EXPECT_TRUE((std::is_constructible_v<JointStateVAJ, JointStatePVAJ>));
  EXPECT_TRUE((std::is_constructible_v<JointStatePVT, JointStatePVAT>));

  // failure to construct from subset
  EXPECT_FALSE((std::is_constructible_v<JointStatePV, JointStateP>));
  EXPECT_FALSE((std::is_constructible_v<JointStatePV, JointStateV>));
  EXPECT_FALSE((std::is_constructible_v<JointStatePVAJ, JointStatePVA>));
  EXPECT_FALSE((std::is_constructible_v<JointStatePVAJ, JointStateVAJ>));
  EXPECT_FALSE((std::is_constructible_v<JointStatePVAT, JointStatePVT>));
}

TEST(AggregateTypesTest, ConstructionFromMoveList) {
  // we can construct by moving aggregated types
  EXPECT_TRUE((std::is_constructible_v<JointStateP, eigenmath::VectorNd&&>));
  EXPECT_TRUE((std::is_constructible_v<JointStatePV, eigenmath::VectorNd&&,
                                       eigenmath::VectorNd&&>));

  // we fail to construct if we have the wrong number of correct types
  EXPECT_FALSE((std::is_constructible_v<JointStateP, eigenmath::VectorNd&&,
                                        eigenmath::VectorNd&&>));
  EXPECT_FALSE((std::is_constructible_v<JointStatePV, eigenmath::VectorNd&&>));

  // we fail to construct if we have the correct number of wrong types
  EXPECT_FALSE((std::is_constructible_v<JointStateP, double&&>));
}

TEST(AggregateTypesTest, ReferenceCastingConstructors) {
  // reference casting from superset
  EXPECT_TRUE((std::is_convertible_v<JointStatePVAJ, JointStatePV&>));
  EXPECT_TRUE((std::is_convertible_v<JointStatePVAJ, JointStateVA&>));
  EXPECT_TRUE((std::is_convertible_v<JointStatePVAJ, JointStateVAJ&>));

  EXPECT_FALSE((std::is_convertible_v<JointStatePV, JointStatePVA>));
  EXPECT_FALSE((std::is_convertible_v<JointStatePV, JointStatePVA&>));
  EXPECT_FALSE((std::is_convertible_v<JointStateVA, JointStatePVA>));
  EXPECT_FALSE((std::is_convertible_v<JointStateVA, JointStatePVA&>));

  // allow conversion type for a copy of non-sequential types,
  // but fail to create a reference to it
  EXPECT_TRUE((std::is_convertible_v<JointStatePVAT, JointStatePVT>));
  EXPECT_FALSE((std::is_convertible_v<JointStatePVAT, JointStatePVT&>));
}

TEST(AggregateTypesTest, EqualityOperators) {
  struct A {
    int a_value;
    bool operator==(const A& other) const { return a_value == other.a_value; }
  };
  struct B {
    double b_value;
    bool operator==(const B& other) const { return b_value == other.b_value; }
  };

  AggregateType<A, B> a;
  a.a_value = 1;
  a.b_value = 0.1;

  AggregateType<A, B> b = a;
  EXPECT_TRUE(a == b);
  EXPECT_FALSE(a != b);

  AggregateType<A, B> c = a;
  c.b_value = -1.1;
  EXPECT_FALSE(a == c);
  EXPECT_TRUE(a != c);

  AggregateType<A, B> d = a;
  d.a_value = -7;
  d.b_value = -1.1;
  EXPECT_FALSE(a == d);
  EXPECT_TRUE(a != d);
}

}  // namespace
}  // namespace intrinsic
