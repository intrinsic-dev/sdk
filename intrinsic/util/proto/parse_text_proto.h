// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_PROTO_PARSE_TEXT_PROTO_H_
#define INTRINSIC_UTIL_PROTO_PARSE_TEXT_PROTO_H_

#include <string>
#include <type_traits>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "google/protobuf/text_format.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
template <typename T, typename = std::enable_if_t<
                          std::is_base_of_v<google::protobuf::Message, T>>>
absl::StatusOr<T> ParseTextProto(absl::string_view asciipb) {
  T message;
  if (!google::protobuf::TextFormat::ParseFromString(std::string(asciipb),
                                                     &message)) {
    return absl::InvalidArgumentError(
        absl::StrCat("Cannot parse protobuf ", typeid(T).name(), " from text"));
  }
  return message;
}

class ParseTextProtoHelper {
 public:
  explicit ParseTextProtoHelper(absl::string_view text) : text_(text) {}

  template <typename T, typename = std::enable_if_t<
                            std::is_base_of_v<google::protobuf::Message, T>>>
  operator T() const {
    auto parse_result = ParseTextProto<T>(text_);
    CHECK_OK(parse_result.status());
    return *parse_result;
  }

 private:
  std::string text_;
  friend ParseTextProtoHelper ParseTextProtoOrDie(absl::string_view);
};

inline ParseTextProtoHelper ParseTextProtoOrDie(absl::string_view asciipb) {
  return ParseTextProtoHelper(asciipb);
}

template <typename T, typename = std::enable_if_t<
                          std::is_base_of_v<google::protobuf::Message, T>>>
T ParseTextOrDie(absl::string_view asciipb) {
  return ParseTextProtoOrDie(asciipb);
}
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_PARSE_TEXT_PROTO_H_
