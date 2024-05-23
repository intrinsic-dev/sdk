// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_PROTO_TYPE_URL_H_
#define INTRINSIC_UTIL_PROTO_TYPE_URL_H_

#include <string>
#include <string_view>
#include <type_traits>

#include "absl/base/attributes.h"
#include "absl/strings/str_cat.h"
#include "google/protobuf/message.h"

namespace intrinsic {

constexpr char kTypeUrlPrefix[] = "type.googleapis.com/";
constexpr char kTypeUrlSeparator = '/';

inline std::string AddTypeUrlPrefix(std::string_view proto_type) {
  if (proto_type.starts_with(kTypeUrlPrefix)) {
    return std::string(proto_type);
  }
  return absl::StrCat(kTypeUrlPrefix, proto_type);
}

inline std::string_view StripTypeUrlPrefix(
    std::string_view type_url ABSL_ATTRIBUTE_LIFETIME_BOUND) {
  std::string_view::size_type pos = type_url.find_last_of(kTypeUrlSeparator);
  if (pos == std::string_view::npos) {
    return type_url;
  }
  return type_url.substr(pos + 1);
}

template <typename M, typename = std::enable_if_t<
                          std::is_base_of_v<google::protobuf::Message, M>>>
inline std::string AddTypeUrlPrefix() {
  return AddTypeUrlPrefix(M::descriptor()->full_name());
}

inline std::string AddTypeUrlPrefix(const google::protobuf::Message& m) {
  return AddTypeUrlPrefix(m.GetDescriptor()->full_name());
}

inline std::string AddTypeUrlPrefix(const google::protobuf::Message* m) {
  return AddTypeUrlPrefix(m->GetDescriptor()->full_name());
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_TYPE_URL_H_
