// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/kvstore.h"

#include <cstddef>
#include <memory>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_helpers.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

absl::Status KeyValueStore::SetAny(absl::string_view key,
                                   const google::protobuf::Any& value,
                                   const NamespaceConfig& config) {
  INTR_RETURN_IF_ERROR(intrinsic::ValidZenohKeyexpr(key));
  absl::StatusOr<std::string> prefixed_name = ZenohHandle::add_key_prefix(key);
  if (!prefixed_name.ok()) {
    // Should not happen since ValidKeyexpr was called before this.
    return prefixed_name.status();
  }
  imw_ret_t ret =
      Zenoh().imw_set(prefixed_name->c_str(), value.SerializeAsString().c_str(),
                      value.ByteSizeLong());
  if (ret != IMW_OK) {
    return absl::InternalError(
        absl::StrFormat("Error setting a key, return code: %d", ret));
  }
  return absl::OkStatus();
}

absl::StatusOr<std::unique_ptr<google::protobuf::Any>> KeyValueStore::Get(
    absl::string_view key, const NamespaceConfig& config,
    absl::Duration timeout) {
  INTR_RETURN_IF_ERROR(intrinsic::ValidZenohKey(key));
  INTR_ASSIGN_OR_RETURN(absl::StatusOr<std::string> prefixed_name,
                        ZenohHandle::add_key_prefix(key));
  auto value = std::make_unique<google::protobuf::Any>();
  absl::Notification notif;
  absl::Status lambda_status = absl::OkStatus();
  auto callback = std::make_unique<imw_callback_functor_t>(
      [value = value.get(), notif = &notif, lambda_status = &lambda_status](
          const char* keyexpr, const void* response_bytes,
          const size_t response_bytes_len) {
        bool ok = value->ParseFromString(absl::string_view(
            static_cast<const char*>(response_bytes), response_bytes_len));
        if (!ok) {
          *lambda_status = absl::InternalError("Failed to parse response");
        }
        notif->Notify();
      });
  imw_ret ret = Zenoh().imw_query(prefixed_name->c_str(), zenoh_static_callback,
                                  nullptr, 0, callback.get());
  if (ret != IMW_OK) {
    return absl::InternalError(
        absl::StrFormat("Error getting a key, return code: %d", ret));
  }
  bool returned = notif.WaitForNotificationWithTimeout(timeout);
  if (!returned) {
    return absl::DeadlineExceededError("Timeout waiting for key");
  }
  if (!lambda_status.ok()) {
    return lambda_status;
  }

  return std::move(value);
}

absl::Status KeyValueStore::GetAll(absl::string_view keyexpr,
                                   const WildcardQueryConfig& config,
                                   KeyValueCallback callback) {
  INTR_RETURN_IF_ERROR(intrinsic::ValidZenohKey(keyexpr));
  INTR_ASSIGN_OR_RETURN(absl::StatusOr<std::string> prefixed_name,
                        ZenohHandle::add_key_prefix(keyexpr));
  auto functor = std::make_unique<imw_callback_functor_t>(
      [callback = std::move(callback)](const char* keyexpr,
                                       const void* response_bytes,
                                       const size_t response_bytes_len) {
        auto value = std::make_unique<google::protobuf::Any>();
        value->ParseFromString(absl::string_view(
            static_cast<const char*>(response_bytes), response_bytes_len));
        callback(std::move(value));
      });
  imw_ret_t ret = Zenoh().imw_query(
      prefixed_name->c_str(), zenoh_static_callback, nullptr, 0, functor.get());
  if (ret != IMW_OK) {
    return absl::InternalError(
        absl::StrFormat("Error getting a key, return code: %d", ret));
  }

  return absl::OkStatus();
}

absl::Status KeyValueStore::Delete(absl::string_view key,
                                   const NamespaceConfig& config) {
  INTR_RETURN_IF_ERROR(intrinsic::ValidZenohKey(key));
  INTR_ASSIGN_OR_RETURN(absl::StatusOr<std::string> prefixed_name,
                        ZenohHandle::add_key_prefix(key));
  imw_ret_t ret = Zenoh().imw_delete_keyexpr(prefixed_name->c_str());
  if (ret != IMW_OK) {
    return absl::InternalError(
        absl::StrFormat("Error deleting a key, return code: %d", ret));
  }
  return absl::OkStatus();
}

}  // namespace intrinsic
