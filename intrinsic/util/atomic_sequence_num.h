// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_ATOMIC_SEQUENCE_NUM_H_
#define INTRINSIC_UTIL_ATOMIC_SEQUENCE_NUM_H_
//
// Atomic operation to generate unique sequence numbers from a counter.
//
//     SequenceNumber<intptr_t> x;
//      ...
//     intptr_t y = x.GetNext();     // get the next sequence number
//
// This can also be used with user-defined strong integer types:
//
//     DEFINE_STRONG_INT_TYPE(MyIntId64, int64);
//     SequenceNumber<MyIntId64> sequence;
//      ...
//     MyIntId64 y = sequence.GetNext();     // get the next sequence number
//
// If your code already uses a Mutex, you may find it faster to protect a
// simple counter with that Mutex.
#include <atomic>
#include <type_traits>

#include "intrinsic/production/external/intops/strong_int.h"

namespace intrinsic {

template <typename T, class IsIntIdCheck = void>
class SequenceNumber;

template <typename ValueT>
class SequenceNumber<
    ValueT, typename std::enable_if<!IsStrongInt<ValueT>::value>::type> {
 public:
  constexpr SequenceNumber() : word_(0) {}

  SequenceNumber(const SequenceNumber&) = delete;
  SequenceNumber& operator=(const SequenceNumber&) = delete;

  ~SequenceNumber() = default;

  using Value = ValueT;

  // Return the integer one greater than was returned by the previous call on
  // this instance, or 0 if there have been no such calls.
  // Provided overflow does not occur, no two calls on the same instance will
  // return the same value, even in the face of concurrency.
  Value GetNext() {
    // As always, clients may not assume properties implied by the
    // implementation, which may change.
    return word_.fetch_add(1, std::memory_order_relaxed);
  }

  // SequenceNumber is implemented as a class specifically to stop clients
  // from reading the value of word_ without also incrementing it.
  // Please do not add such a call.

 private:
  std::atomic<Value> word_;
};

// Specialization for strong ints.
template <typename ValueT>
class SequenceNumber<
    ValueT, typename std::enable_if<IsStrongInt<ValueT>::value>::type> {
 public:
  constexpr SequenceNumber() : word_(0) {}

  SequenceNumber(const SequenceNumber&) = delete;
  SequenceNumber& operator=(const SequenceNumber&) = delete;

  ~SequenceNumber() = default;

  using Value = ValueT;

  Value GetNext() {
    return ValueT(word_.fetch_add(1, std::memory_order_relaxed));
  }

 private:
  std::atomic<typename Value::ValueType> word_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_ATOMIC_SEQUENCE_NUM_H_
