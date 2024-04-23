// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/page_fault_info.h"

#include <sys/mman.h>
#include <sys/resource.h>

namespace intrinsic {

PagefaultInfo GetPagefaultInfo() {
  static PagefaultInfo info;

  rusage usage;
  getrusage(RUSAGE_THREAD, &usage);

  info.delta_major_faults = usage.ru_majflt - info.major_faults;
  info.delta_minor_faults = usage.ru_minflt - info.minor_faults;
  info.major_faults = usage.ru_majflt;
  info.minor_faults = usage.ru_minflt;

  return info;
}

}  // namespace intrinsic
