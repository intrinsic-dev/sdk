// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/util.h"

#include <sched.h>

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <ios>
#include <iterator>
#include <string>
#include <vector>

#include "absl/container/flat_hash_set.h"
#include "absl/functional/any_invocable.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/ascii.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/str_split.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/util/status/status_macros.h"
#include "re2/re2.h"

namespace intrinsic {
// Returns the contents of the file at `path` as string.
// Is only intended for small files because the full file as read into a string.
// Returns NotFoundError if the file can't be opened.
absl::StatusOr<std::string> ReadFileToString(absl::string_view path) {
  const std::string path_to_file = std::string(path);
  std::ifstream input_stream(path_to_file);
  if (!input_stream.is_open()) {
    return absl::NotFoundError(absl::StrCat("File not found: ", path_to_file));
  }

  std::string str;
  input_stream.seekg(0, std::ios::end);
  str.reserve(input_stream.tellg());
  input_stream.seekg(0, std::ios::beg);

  str.assign((std::istreambuf_iterator<char>(input_stream)),
             std::istreambuf_iterator<char>());

  return str;
}

absl::StatusOr<absl::flat_hash_set<int>> ReadCpuAffinitySetFromCommandLine(
    absl::string_view path_for_testing) {
  // Example of cat/proc/cmdline on a RTPC
  // init=/usr/lib/systemd/systemd boot=local rootwait ro noresume loglevel=7
  // console=tty1 console=ttyS0,115200 apparmor=0 virtio_net.napi_tx=1
  // systemd.unified_cgroup_hierarchy=true csm.disabled=1
  // loadpin.exclude=kernel-module modules-load=loadpin_trigger
  // module.sig_enforce=1 i915.modeset=1 efi=runtime processor.max_cstate=0
  // idle=poll isolcpus=5 nohz=on nohz_full=5 rcu_nocbs=5 rcu_nocb_poll
  // nowatchdog pcie_aspm=off   dm_verity.error_behavior=3
  // dm_verity.max_bios=-1 dm_verity.dev_wait=1 root=/dev/dm-0 dm="1 vroot
  // none ro 1,0 4077568 verity payload=PARTLABEL=IROOT-B
  // hashtree=PARTLABEL=IROOT-B hashstart=4077568 alg=sha256
  INTR_ASSIGN_OR_RETURN(std::string rcu_nocbs,
                        ReadFileToString(path_for_testing));

  // Can be a single entry, a range, or a mix.
  // https://man7.org/linux/man-pages/man7/cpuset.7.html
  //  Examples of the List Format:
  //    0-4,9           # bits 0, 1, 2, 3, 4, and 9 set
  //    0-2,7,12-14     # bits 0, 1, 2, 7, 12, 13, and 14 set
  // External build is broken when using absl::string_view.
  std::string entries = "";

  // Group1 is the affinity definition.
  const RE2 kRCU_NOCBSRegex(R"(rcu_nocbs=([^\s]+))");
  // Every comma separated affinity entry matches one of those regexes.
  // The regex ensures that the CPU index cannot be negative.
  const RE2 kSingleEntryRegex(R"(([\d]+))");
  const RE2 kRangeRegex(R"(([\d]+)-([\d]+))");

  if (!RE2::PartialMatch(rcu_nocbs, kRCU_NOCBSRegex, &entries)) {
    return absl::FailedPreconditionError(
        absl::StrCat("Failed to parse [", path_for_testing,
                     "]. 'rcu_nocbs' is not defined."));
  }
  std::vector<std::string> cpu_strings =
      absl::StrSplit(entries, ',', absl::SkipWhitespace());
  absl::flat_hash_set<int> values;
  for (const absl::string_view entry : cpu_strings) {
    // Removes the AsciiWhitespace that may be present.
    if (uint32_t value; RE2::FullMatch(entry, kSingleEntryRegex, &value)) {
      if (values.contains(value)) {
        return absl::FailedPreconditionError(
            absl::StrCat("Duplicate entry for CPU[", value, "]."));
      }
      values.insert(value);
      continue;
    } else if (uint32_t value_0, value_1;
               RE2::FullMatch(entry, kRangeRegex, &value_0, &value_1)) {
      for (uint32_t i = std::min(value_0, value_1);
           i <= std::max(value_0, value_1); ++i) {
        if (values.contains(i)) {
          return absl::FailedPreconditionError(
              absl::StrCat("Duplicate entry for CPU[", i, "]."));
        }
        values.insert(i);
      }
      continue;
    }
    return absl::FailedPreconditionError(absl::StrCat(
        "Failed to parse '", entry, "'. Expected Format: '2', or '0-2'."));
  }
  return values;
}

bool WaitForNotificationWithInterrupt(absl::Notification& notification,
                                      absl::AnyInvocable<bool()> should_quit,
                                      const absl::Duration poll_interval) {
  auto poll_deadline = absl::Now();
  while (!should_quit()) {
    if (notification.WaitForNotificationWithDeadline(poll_deadline +=
                                                     poll_interval)) {
      return true;
    }
  }

  return notification.HasBeenNotified();
}

bool WaitForNotificationWithDeadlineAndInterrupt(
    absl::Notification& notification, const absl::Time deadline,
    absl::AnyInvocable<bool()> should_quit,
    const absl::Duration poll_interval) {
  auto poll_deadline = absl::Now();
  while (!should_quit() && absl::Now() < deadline) {
    if (notification.WaitForNotificationWithDeadline(
            std::min(deadline, poll_deadline += poll_interval))) {
      return true;
    }
  }

  return notification.HasBeenNotified();
}

}  // namespace intrinsic
