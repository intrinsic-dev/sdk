// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/grpc/connection_params.h"

#include <ostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "absl/strings/str_format.h"

namespace intrinsic {

// static
ConnectionParams ConnectionParams::ResourceInstance(
    std::string_view instance_name) {
  return ConnectionParams::ResourceInstance(
      /*instance_name=*/instance_name,
      /*address=*/"xfa.lan:17080");
}

// static
ConnectionParams ConnectionParams::ResourceInstance(
    std::string_view instance_name, std::string_view address) {
  return {
      .address = std::string(address),
      .instance_name = std::string(instance_name),
      .header = "x-resource-instance-name",
  };
}

// static
ConnectionParams ConnectionParams::NoIngress(std::string_view address) {
  return {
      .address = std::string(address),
      .instance_name = "",
      .header = "",
  };
}

// static
ConnectionParams ConnectionParams::LocalPort(int port) {
  return NoIngress(absl::StrFormat("localhost:%d", port));
}

std::vector<std::pair<std::string, std::string>> ConnectionParams::Metadata()
    const {
  if (header.empty() || instance_name.empty()) {
    return {};
  }
  return std::vector<std::pair<std::string, std::string>>{
      {header, instance_name}};
}

std::ostream& operator<<(std::ostream& os, const ConnectionParams& p) {
  if (p.instance_name.empty()) {
    return os << p.address;
  }
  return os << absl::StreamFormat("%s (%s=%s)", p.address, p.header,
                                  p.instance_name);
}

}  // namespace intrinsic
