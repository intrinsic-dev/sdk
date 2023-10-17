// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_PAGE_FAULT_INFO_H_
#define INTRINSIC_UTIL_PAGE_FAULT_INFO_H_

#include <cstdint>
#include <ostream>

namespace intrinsic {

// PagefaultInfo contains information about the number of pagefaults occurring
// during the runtime of the current process.
struct PagefaultInfo {
  // Absolute number of page faults encountered during the lifetime of this
  // process.
  uint64_t major_faults = 0;
  uint64_t minor_faults = 0;
  // Relative number of new page faults encountered since the previous call to
  // `PageFaultInfo`.
  uint64_t delta_major_faults = 0;
  uint64_t delta_minor_faults = 0;
};

// Returns a PagefaultInfo struct indicating the pagefault count of the current
// process.
PagefaultInfo GetPagefaultInfo();

}  // namespace intrinsic
#endif  // INTRINSIC_UTIL_PAGE_FAULT_INFO_H_
