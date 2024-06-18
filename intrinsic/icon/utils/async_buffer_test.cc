// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/async_buffer.h"

#include <gtest/gtest.h>

#include <cstdint>
#include <random>

#include "absl/strings/str_cat.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic::icon {
namespace {

class AsyncBufferTest : public testing::Test {
 protected:
  class Buffer {
   private:
    uint32_t seq_no_;
    uint32_t data_[4096 / 4 - 1];  // seq_no + data = 4K

   public:
    Buffer() { Fill(0); }

    explicit Buffer(uint32_t seq_no) { Fill(seq_no); }

    void Fill(uint32_t seq_no) {
      seq_no_ = seq_no;

      std::mt19937 rng(seq_no);
      for (uint32_t& value : data_) {
        value = rng();
      }
    }

    void Check(uint32_t seq_no, intrinsic::SourceLocation loc =
                                    intrinsic::SourceLocation::current()) {
      testing::ScopedTrace scope(loc.file_name(), loc.line(),
                                 absl::StrCat("Called: ", __func__));
      ASSERT_EQ(seq_no_, seq_no);

      std::mt19937 rng(seq_no);
      for (uint32_t value : data_) {
        ASSERT_EQ(value, rng());
      }
    }
  };

  static void VerifyActive(
      AsyncBuffer<Buffer>& async, uint32_t seq_no,
      intrinsic::SourceLocation loc = intrinsic::SourceLocation::current()) {
    testing::ScopedTrace scope(loc.file_name(), loc.line(),
                               absl::StrCat("Called: ", __func__));
    Buffer* active;
    async.GetActiveBuffer(&active);
    ASSERT_NE(active, nullptr);
    active->Check(seq_no);
  }

  static constexpr int kStateCount =
      sizeof(async_buffer_internal::kStateLookupTable) /
      sizeof(async_buffer_internal::kStateLookupTable[0]);
};

// Test the invariants of the internal state machine. See async_buffer.h for
// a detailed explanation of the invariants.
// These tests are run against a purely constant structure.
TEST_F(AsyncBufferTest, OneToOneBufferIDToSlot) {
  // Enforces for every state of the state machine, that each buffer ID must
  // be represented exactly once in each of the slots.
  for (const auto& s : async_buffer_internal::kStateLookupTable) {
    // Active and free buf IDs must be in range.
    EXPECT_LT(s.active_buf, 3);
    EXPECT_LT(s.free_buf, 3);

    // Active must not equal Free.
    EXPECT_NE(s.active_buf, s.free_buf);

    // Active and Free are on the range [0, 2], and Active != Free, we know
    // that the implied Mailbox buffer is in range and unique.
  }
}

TEST_F(AsyncBufferTest, GetActiveEmptiesMailbox) {
  // Enforces after any GetActive state transition, that the system must be in
  // one of the "mailbox empty" states (states 0-5).
  for (const auto& s : async_buffer_internal::kStateLookupTable) {
    EXPECT_LT(s.get_active, kStateCount / 2);
  }
}

TEST_F(AsyncBufferTest, GetActiveWithEmptyMailboxHoldsState) {
  // Enforces that if the system starts in a "mailbox empty" state, after a
  // GetActive state transition, the system must be in the same state it
  // started in.
  for (uint8_t i = 0; i < kStateCount / 2; ++i) {
    const auto& s = async_buffer_internal::kStateLookupTable[i];
    EXPECT_EQ(s.get_active, i);
  }
}

TEST_F(AsyncBufferTest,
       GetActiveWithFullMailboxEmptiesMailboxAndSwapsActiveAndMailbox) {
  // Enforces that if the system starts in a "mailbox full" state, after after
  // a GetActive state transition, the buffer in the Free slot must be
  // unchanged, and the buffer in the Active slot must have exchanged positions
  // with the buffer in the Mailbox slot.  Since the buffer ID of the buffer in
  // the mailbox slot is implied from the IDs in the Active and Free slots,
  // this is the same as saying that the buffer in the Active slot is different
  // from the buffer previously in the active slot, and not the same as the
  // buffer in the Free slot.
  for (uint8_t i = kStateCount / 2; i < kStateCount; ++i) {
    const auto& s = async_buffer_internal::kStateLookupTable[i];

    // It is unsafe to proceed if the next array index is invalid.  Also
    // checks to make sure that the next state is an "empty mailbox" state.
    ASSERT_LT(s.get_active, kStateCount / 2);

    const auto& next = async_buffer_internal::kStateLookupTable[s.get_active];
    EXPECT_EQ(s.free_buf, next.free_buf);
    EXPECT_NE(s.active_buf, next.active_buf);
  }
}

TEST_F(AsyncBufferTest, CommitFreeFillsMailbox) {
  // Enforces that after any CommitFree state transition, the system must be in
  // one of the "mailbox full" states (states 6-11)
  for (const auto& s : async_buffer_internal::kStateLookupTable) {
    EXPECT_GE(s.commit_free, kStateCount / 2);
    EXPECT_LT(s.commit_free, kStateCount);
  }
}

TEST_F(AsyncBufferTest, CommitFreeSwapsFreeAndMailbox) {
  // Enforces after any CommitFree state transition, the buffer in the Active
  // slot must be unchanged, and the buffer in the Free slot must have exchanged
  // positions with the buffer in the Mailbox slot.
  for (const auto& s : async_buffer_internal::kStateLookupTable) {
    // It is unsafe to proceed if the next array index is invalid.
    ASSERT_LT(s.commit_free, kStateCount);

    const auto& next = async_buffer_internal::kStateLookupTable[s.commit_free];
    EXPECT_NE(s.free_buf, next.free_buf);
    EXPECT_EQ(s.active_buf, next.active_buf);
  }
}

// Unit-tests for the AsyncBuffer<T> class.
TEST_F(AsyncBufferTest, FillCheck) {
  for (uint32_t i = 0; i < 0x1000; i++) {
    Buffer buff(i);
    buff.Check(i);
  }
}

TEST_F(AsyncBufferTest, WellOrdered) {
  AsyncBuffer<Buffer> async;

  Buffer* active = async.GetFreeBuffer();

  // Note: we use ASSERT here instead of EXPECT.  If any of these checks fail,
  // chances are all of them are going to fail, and there is no point in
  // spamming the test log with ~4000 reports that this test failed.
  ASSERT_TRUE(active != nullptr);
  VerifyActive(async, 0);

  for (uint32_t i = 1; i < 0x1000; i++) {
    Buffer* free_buff = async.GetFreeBuffer();
    free_buff->Fill(i);

    VerifyActive(async, i - 1);

    ASSERT_TRUE(async.CommitFreeBuffer());

    VerifyActive(async, i);
    VerifyActive(async, i);
  }
}

TEST_F(AsyncBufferTest, ReturnValueSemantics) {
  AsyncBuffer<Buffer> async;

  Buffer* active_buffer = nullptr;
  Buffer* other_buffer = nullptr;

  // the mailbox is empty; expect false return value
  ASSERT_FALSE(async.GetActiveBuffer(&active_buffer));
  ASSERT_NE(active_buffer, nullptr);

  // call not preceded by call to GetFreeBuffer();
  // expect false return value
  ASSERT_FALSE(async.CommitFreeBuffer());

  // nothing has changed; continue to expect false return value
  ASSERT_FALSE(async.GetActiveBuffer(&active_buffer));
  ASSERT_NE(active_buffer, nullptr);

  // commit a buffer into mailbox
  ASSERT_NE(async.GetFreeBuffer(), nullptr);
  ASSERT_TRUE(async.CommitFreeBuffer());

  // the mailbox is full; expect true return value
  ASSERT_TRUE(async.GetActiveBuffer(&other_buffer));
  ASSERT_NE(active_buffer, other_buffer);
  ASSERT_NE(other_buffer, nullptr);
}

}  // namespace
}  // namespace intrinsic::icon
