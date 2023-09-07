// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// This header file provides a few convenience functions to access general
// information about a set of shared memory data.
// It specifically provides access to a `SegmentInfo` struct as defined in
// `segment_info.fbs`.
#ifndef INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_INFO_UTILS_H_
#define INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_INFO_UTILS_H_

#include <string>
#include <vector>

#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_generated.h"

namespace intrinsic::icon {

// Extracts the SegmentNames from the SegmentInfo struct.
// Convenience function to represent the fixed size flatbuffer struct
// `SegmentName` (c.f. segment_info.fbs) into a vector of std::string.
std::vector<std::string> GetNamesFromSegmentInfo(
    const SegmentInfo& segment_info);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_SHARED_MEMORY_MANAGER_SEGMENT_INFO_UTILS_H_
