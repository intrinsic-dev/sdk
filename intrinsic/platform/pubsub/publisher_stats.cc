// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/publisher_stats.h"

#include <limits>

#include "absl/container/flat_hash_map.h"
#include "absl/synchronization/mutex.h"

namespace intrinsic::internal {

int PublisherStats::GetCount(absl::string_view topic) {
  absl::MutexLock lock(&mu_);
  return counts_[topic];
}

void PublisherStats::Increment(absl::string_view topic) {
  absl::MutexLock lock(&mu_);
  if (counts_[topic] == std::numeric_limits<int64_t>::max()) {
    counts_[topic] = 0;
  }
  counts_[topic]++;
}

void PublisherStats::Reset() {
  absl::MutexLock lock(&mu_);
  counts_.clear();
}

void ResetMessagesPublished() { return PublisherStats::Singleton().Reset(); }

int MessagesPublished(absl::string_view topic) {
  return PublisherStats::Singleton().GetCount(topic);
}

}  // namespace intrinsic::internal
