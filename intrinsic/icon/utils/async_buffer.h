// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_ASYNC_BUFFER_H_
#define INTRINSIC_ICON_UTILS_ASYNC_BUFFER_H_

#include <atomic>
#include <cstdint>
#include <memory>

namespace intrinsic {

// A real time safe producer/consumer buffer container
//
// AsyncBuffer implements a triple buffered single producer/single consumer
// container.
//
// Terminology:
// \li Active Buffer: the buffer that is being read by the consumer
// \li Free Buffer: a buffer ready to be updated by the producer
// \li Mailbox Buffer: a buffer not currently owned by either the producer or
// the consumer.  The mailbox buffer may be "full" (because it has recently been
// committed by the producer) or "empty" (because it was recently fetched by the
// consumer)
//
// A producer updates a buffer by:
// \code
// Buffer* free_buff = async.GetFreeBuffer();
// free_buff->update();
// async.CommitFreeBuffer();
// \endcode
//
// A consumer can get the most up to date buffer by:
// \code
// Buffer* active = async.GetActiveBuffer();
// \endcode
//
// The act of committing the free buffer atomically swaps the free buffer with
// the mailbox buffer.  After a commit operation, the mailbox buffer is
// considered to be "full" and will be the buffer fetched by the consumer the
// next time GetActiveBuffer() is called.
//
// The act of getting the active buffer either just gets the current active
// buffer if the mailbox is empty, or atomically swaps the current active buffer
// with the mailbox buffer, and returns the new active buffer if the mailbox is
// full.  In either case, the mailbox is considered to be empty after a call to
// GetActiveBuffer.
template <typename T>
class AsyncBuffer {
 public:
  // Creates an AsyncBuffer with internally allocated storage.
  template <typename... InitArgs>
  explicit AsyncBuffer(const InitArgs&... args);

  // Returns the active buffer to the consumer. This buffer is guaranteed not
  // to be modified until the next call to GetActiveBuffer() by the consumer.
  // This may be the same buffer which was returned to last call to
  // GetActiveBuffer().
  //
  // Returns true if the mailbox buffer was full and the returned pointer
  // points to it. Returns false if the mailbox buffer was empty and the
  // returned pointer points to the buffer that was already active at the time
  // of this call.
  bool GetActiveBuffer(T** buffer);

  // Commits the free buffer by swapping it with the mailbox buffer.
  //
  // Each call to this function must be preceded by a call to GetFreeBuffer()
  // or else it has no effect. Returns true if this call was preceded by a call
  // to GetFreeBuffer(), false otherwise.
  bool CommitFreeBuffer();

  // Returns a free buffer to the producer. This buffer can be modified until
  // the producer calls CommitFreeBuffer().
  T* GetFreeBuffer();

 private:
  std::atomic<uint8_t> raw_state_ = 0;
  bool free_buffer_checked_out_ = false;
  // Buffers: active, mailbox, free.
  std::unique_ptr<T> buffers_[3];
};

template <typename T>
template <typename... InitArgs>
inline AsyncBuffer<T>::AsyncBuffer(const InitArgs&... args) {
  for (std::unique_ptr<T>& buf : buffers_) {
    buf = std::make_unique<T>(args...);
  }
}

// The async_buffer_internal holds the constant state machine lookup table
// shared by all AsyncBuffer<T> objects.
namespace async_buffer_internal {
struct State {
  uint8_t active_buf;
  uint8_t free_buf;
  uint8_t get_active;
  uint8_t commit_free;
};

// Internally, the AsyncBuffer is represented as a state machine.  It manages 3
// buffers which, at any instant in time, are distributed across 3 different
// slots (Active, Mailbox and Free).
//
// There are 3! (6) different orders for the buffers to exist in the slots.  In
// addition, the mailbox slot can be considered to be either "full" or "empty".
// This makes the total number of states for the system 2 * 3! = 12.
//
// Three operations need to be supported by the AsyncBuffer.
// \li 1) Getting the free buffer.
// \li 2) Committing the free buffer.
// \li 3) Getting the active buffer.
//
// Operation #1 (getting the free buffer) does not permute the state of the
// system, it only needs to look up which buffer is the free buffer based on
// the state of the system.
//
// Operation #2 (committing the free buffer) always permutes the state of the
// system.  It always swaps the buffers in the Free and Mailbox slots, and it
// always causes the Mailbox to become full.
//
// Operation #3 (fetching the active buffer) permutes the state of the system if
// the mailbox is full (swapping Active and Mailbox and returning the new
// Active), but not if the mailbox is empty.
//
// Given this, the state machine can be described as 12 states, each of which
// defines which buffer is in which slot for each state.  It also needs to store
// which state is the next state in the machine for each of the two state
// permuting operations.
//
// All of this can be represented with 4 integers per state.  Only two are
// needed to store the buffer-to-slot mapping (the ID of the Mailbox buffer is
// always implied by the IDs of the Active and Free buffers).  Another 2 are
// used to define the edges for the GetActive and CommitFree operations.
//
// While there are many valid representations of the state machine states, a
// solution was chosen below which partitions the states a way in which the
// "mailbox empty" states are states 0-5, and the "mailbox full" states are
// states 6-11.
//
// To ensure that the state machine solution chosen below is a valid state
// machine, there are a number of simple invariants which are checked in the
// test code.
//
// \li For every state of the state machine, each buffer ID must be represented
// exactly once in each of the slots.
//
// \li After any GetActive state transition, the system must be in one of the
// "mailbox empty" states (states 0-5)
//
// \li If the system starts in a "mailbox empty" state, after a GetActive state
// transition, the system must be in the same state it started in.
//
// \li If the system starts in a "mailbox full" state, after a GetActive
// state transition, the buffer in the Free slot must be unchanged, and the
// buffer in the Active slot must have exchanged positions with the buffer in
// the Mailbox slot.  Since the buffer ID of the buffer in the mailbox slot is
// implied from the IDs in the Active and Free slots, this is the same as saying
// that the buffer in the Active slot is different from the buffer previously in
// the active slot, and not the same as the buffer in the Free slot.
//
// \li After any CommitFree state transition, the system must be in one of the
// "mailbox full" states (states 6-11)
//
// \li After any CommitFree state transition, the buffer in the Active slot must
// be unchanged, and the buffer in the Free slot must have exchanged positions
// with the buffer in the Mailbox slot.

constexpr State kStateLookupTable[] = {
    //   Empty Mailbox States
    {.active_buf = 0, .free_buf = 2, .get_active = 0, .commit_free = 7},
    {.active_buf = 0, .free_buf = 1, .get_active = 1, .commit_free = 6},
    {.active_buf = 1, .free_buf = 2, .get_active = 2, .commit_free = 9},
    {.active_buf = 1, .free_buf = 0, .get_active = 3, .commit_free = 8},
    {.active_buf = 2, .free_buf = 1, .get_active = 4, .commit_free = 11},
    {.active_buf = 2, .free_buf = 0, .get_active = 5, .commit_free = 10},
    //   Full Mailbox States
    {.active_buf = 0, .free_buf = 2, .get_active = 2, .commit_free = 7},
    {.active_buf = 0, .free_buf = 1, .get_active = 4, .commit_free = 6},
    {.active_buf = 1, .free_buf = 2, .get_active = 0, .commit_free = 9},
    {.active_buf = 1, .free_buf = 0, .get_active = 5, .commit_free = 8},
    {.active_buf = 2, .free_buf = 1, .get_active = 1, .commit_free = 11},
    {.active_buf = 2, .free_buf = 0, .get_active = 3, .commit_free = 10}};

}  // namespace async_buffer_internal

template <typename T>
inline T* AsyncBuffer<T>::GetFreeBuffer() {
  using async_buffer_internal::kStateLookupTable;
  free_buffer_checked_out_ = true;
  return buffers_[kStateLookupTable[raw_state_.load()].free_buf].get();
}

template <typename T>
inline bool AsyncBuffer<T>::GetActiveBuffer(T** buffer) {
  using async_buffer_internal::kStateLookupTable;

  uint8_t cur_state = raw_state_.load();
  uint8_t next_state = 0;
  do {
    next_state = kStateLookupTable[cur_state].get_active;
  } while (!raw_state_.compare_exchange_strong(cur_state, next_state));

  *buffer = buffers_[kStateLookupTable[next_state].active_buf].get();
  return next_state != cur_state;
}

template <typename T>
inline bool AsyncBuffer<T>::CommitFreeBuffer() {
  using async_buffer_internal::kStateLookupTable;

  if (!free_buffer_checked_out_) {
    return false;
  }

  uint8_t cur_state = raw_state_.load();
  uint8_t next_state = 0;
  do {
    next_state = kStateLookupTable[cur_state].commit_free;
  } while (!raw_state_.compare_exchange_strong(cur_state, next_state));

  free_buffer_checked_out_ = false;
  return true;
}

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_UTILS_ASYNC_BUFFER_H_
