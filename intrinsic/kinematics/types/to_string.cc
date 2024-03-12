// Copyright 2023 Intrinsic Innovation LLC


#include <sstream>
#include <string>

#include "intrinsic/eigenmath/types.h"

namespace intrinsic {
namespace eigenmath {

std::string ToString(const VectorNd& vec) {
  Eigen::IOFormat format(Eigen::StreamPrecision, /*flags=*/Eigen::DontAlignCols,
                         /*coeffSeparator=*/" ", /*rowSeparator=*/",");

  std::stringstream ss;
  ss << vec.format(format);
  return ss.str();
}

}  // namespace eigenmath
}  // namespace intrinsic
