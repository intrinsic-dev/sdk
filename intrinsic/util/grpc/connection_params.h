// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_UTIL_GRPC_CONNECTION_PARAMS_H_
#define INTRINSIC_UTIL_GRPC_CONNECTION_PARAMS_H_

#include <iosfwd>
#include <ostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace intrinsic {

struct ConnectionParams {
  // Constructs a ConnectionParams that is appropriately configured to work with
  // the no-ingress case, such as integration tests.
  static ConnectionParams NoIngress(std::string_view address);

  // Helper for connecting to a local instance of ICON on a specific port. This
  // primarily should be used for testing purposes.  It will not specify
  // information for ingress into a kubernetes cluster.
  static ConnectionParams LocalPort(int port);

  // The full address of the server "ip_address_or_hostname:port_number".
  std::string address;
  // The ingress instance name.  This determines which VirtualService in
  // kubernetes is targeted.  If empty, the header information is not added to
  // the gRPC connection.
  std::string instance_name;
  // The header to be used when establishing a gRPC connection to the ingress.
  // The header's value will be instance_name.
  std::string header;

  // Returns the metadata required by the connection to talk to the server, if
  // it is necessary.  Each pair represents the key, and value of the metadata,
  // respectively.
  std::vector<std::pair<std::string, std::string>> Metadata() const;

  friend bool operator==(const ConnectionParams& lhs,
                         const ConnectionParams& rhs) {
    return lhs.address == rhs.address &&
           lhs.instance_name == rhs.instance_name && lhs.header == rhs.header;
  }

  friend bool operator!=(const ConnectionParams& lhs,
                         const ConnectionParams& rhs) {
    return !(lhs == rhs);
  }

  template <typename H>
  friend H AbslHashValue(H h, const ConnectionParams& p) {
    return H::combine(std::move(h), p.address, p.instance_name, p.header);
  }

  friend std::ostream& operator<<(std::ostream& os, const ConnectionParams& p);
};

namespace icon {
using ::intrinsic::ConnectionParams;
}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_GRPC_CONNECTION_PARAMS_H_
