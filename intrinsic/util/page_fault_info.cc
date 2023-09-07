// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/util/page_fault_info.h"

#include <sys/mman.h>
#include <sys/resource.h>

#include <ostream>

namespace intrinsic {

PagefaultInfo GetPagefaultInfo() {
  static PagefaultInfo info;

  rusage usage;
  getrusage(RUSAGE_SELF, &usage);

  info.delta_major_faults = usage.ru_majflt - info.major_faults;
  info.delta_minor_faults = usage.ru_minflt - info.minor_faults;
  info.major_faults = usage.ru_majflt;
  info.minor_faults = usage.ru_minflt;

  return info;
}

}  // namespace intrinsic
