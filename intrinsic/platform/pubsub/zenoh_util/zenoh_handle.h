// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HANDLE_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HANDLE_H_

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <type_traits>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"

namespace intrinsic {

typedef enum imw_ret {
  IMW_OK = 0,
  IMW_ERROR = 1,
  IMW_NOT_INITIALIZED = 2,
} imw_ret_t;

typedef void imw_subscription_callback_fn(const char *keyexpr,
                                          const void *bytes,
                                          const size_t bytes_len,
                                          void *user_context);

typedef void imw_queryable_callback_fn(const char *keyexpr,
                                       const void *query_bytes,
                                       const size_t query_bytes_len,
                                       const void *query_context,
                                       void *user_context);

typedef void imw_query_callback_fn(const char *keyexpr,
                                   const void *response_bytes,
                                   const size_t response_bytes_len,
                                   void *user_context);

typedef std::function<void(const char *, const void *, const size_t)>
    imw_callback_functor_t;

void zenoh_static_callback(const char *keyexpr, const void *blob,
                           size_t blob_len, void *fptr);

// ZenohHandle loads the zenoh shared library and provides an interface for
// necessary PubSub calls to the shared library.
struct ZenohHandle {
 public:
  static ZenohHandle *CreateZenohHandle();

  std::add_pointer_t<imw_ret_t(const char *config)> imw_init;

  std::add_pointer_t<imw_ret_t()> imw_fini;

  std::add_pointer_t<imw_ret_t(const char *keyexpr, const char *qos)>
      imw_create_publisher;

  std::add_pointer_t<imw_ret_t(const char *keyexpr)> imw_destroy_publisher;

  std::add_pointer_t<imw_ret_t(const char *keyexpr, const void *bytes,
                               const size_t bytes_len)>
      imw_publish;

  std::add_pointer_t<imw_ret_t(const char *keyexpr,
                               imw_subscription_callback_fn *callback,
                               const char *qos, void *user_context)>
      imw_create_subscription;

  std::add_pointer_t<imw_ret_t(const char *keyexpr,
                               imw_subscription_callback_fn *callback,
                               void *user_context)>
      imw_destroy_subscription;

  std::add_pointer_t<int(const char *left, const char *right)>
      imw_keyexpr_intersects;

  std::add_pointer_t<int(const char *left, const char *right)>
      imw_keyexpr_includes;

  std::add_pointer_t<int(const char *keyexpr)> imw_keyexpr_is_canon;

  std::add_pointer_t<imw_ret_t(const char *keyexpr,
                               imw_queryable_callback_fn *callback,
                               void *user_context)>
      imw_create_queryable;

  std::add_pointer_t<imw_ret_t(const char *keyexpr,
                               imw_queryable_callback_fn *callback,
                               void *user_context)>
      imw_destroy_queryable;

  std::add_pointer_t<imw_ret_t(const void *query_context, const char *keyexpr,
                               const void *reply_bytes,
                               const size_t reply_bytes_len)>
      imw_queryable_reply;

  std::add_pointer_t<imw_ret_t(
      const char *keyexpr, imw_query_callback_fn *callback,
      const void *query_payload, const size_t query_payload_len,
      void *user_context)>
      imw_query;

  std::add_pointer_t<const char *const()> imw_version;

  static absl::StatusOr<std::string> add_topic_prefix(absl::string_view topic);
  static absl::StatusOr<std::string> remove_topic_prefix(
      absl::string_view topic);

 private:
  void *handle = nullptr;
  void Initialize();
};

const ZenohHandle &Zenoh();

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HANDLE_H_
