// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/proto/type_url.h"

#include <gtest/gtest.h>

#include <string>

#include "google/protobuf/wrappers.pb.h"

namespace intrinsic {

namespace {

TEST(TypeUrl, AddPrefix) {
  std::string proto_type =
      google::protobuf::Int64Value::descriptor()->full_name();
  EXPECT_EQ(AddTypeUrlPrefix(proto_type),
            "type.googleapis.com/google.protobuf.Int64Value");
}

TEST(TypeUrl, AddPrefixIdempotent) {
  std::string type_url = "type.googleapis.com/google.protobuf.Int64Value";
  EXPECT_EQ(AddTypeUrlPrefix(type_url), type_url);
}

TEST(TypeUrl, StripPrefix) {
  EXPECT_EQ(
      StripTypeUrlPrefix("type.googleapis.com/google.protobuf.Int64Value"),
      "google.protobuf.Int64Value");
}

TEST(TypeUrl, StripPrefixIdempotent) {
  std::string proto_type = "google.protobuf.Int64Value";
  EXPECT_EQ(StripTypeUrlPrefix(proto_type), proto_type);
}

}  // namespace
}  // namespace intrinsic
