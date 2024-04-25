// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

#include <dlfcn.h>

#include <string>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_helpers.h"
#include "tools/cpp/runfiles/runfiles.h"

#define GET_FUNCTION_PTR(handle, func) GetFunctionHandle(handle, #func, &func);

namespace intrinsic {

constexpr char libZenohPath[] = "/intrinsic/insrc/middleware/libimw_zenoh.so.1";
// NOLINTBEGIN(clang-diagnostic-unused-const-variable)
constexpr char libTestAsanZenohPath[] =
    "/intrinsic/insrc/middleware/"
    "libimw_intraprocess_only_asan.so.1";
constexpr char libTestMsanZenohPath[] =
    "/intrinsic/insrc/middleware/"
    "libimw_intraprocess_only_msan.so.1";
constexpr char libTestTsanZenohPath[] =
    "/intrinsic/insrc/middleware/"
    "libimw_intraprocess_only_tsan.so.1";
// NOLINTEND(clang-diagnostic-unused-const-variable)

template <typename T>
void GetFunctionHandle(void* handle, const std::string& name, T* func_ptr) {
  *func_ptr = reinterpret_cast<T>(dlsym(handle, name.c_str()));
  if (*func_ptr == nullptr) {
    LOG(FATAL) << "Failed to resolve function '" << name << "'";
  }
}

void zenoh_static_callback(const char* keyexpr, const void* blob,
                           const size_t blob_len, void* fptr) {
  (*static_cast<imw_callback_functor_t*>(fptr))(keyexpr, blob, blob_len);
}

ZenohHandle* ZenohHandle::CreateZenohHandle() {
  auto* zenoh = new ZenohHandle();
  zenoh->Initialize();
  return zenoh;
}

void ZenohHandle::Initialize() {
  std::string runfiles_dir;
  std::string path;
  if (!RunningInKubernetes()) {
    runfiles_dir = bazel::tools::cpp::runfiles::Runfiles::Create("")->Rlocation(
        "ai_intrinsic_sdks");

#if defined(MEMORY_SANITIZER)
    path = libTestMsanZenohPath;
#elif defined(THREAD_SANITIZER)
    path = libTestTsanZenohPath;
#elif defined(ADDRESS_SANITIZER)
    path = libTestAsanZenohPath;
#else
    path = libZenohPath;
#endif
  } else {
    // These are here to avoid any unused variable linter warnings.
    (void)libTestAsanZenohPath;
    (void)libTestMsanZenohPath;
    (void)libTestTsanZenohPath;
    path = libZenohPath;
  }

#if defined(MEMORY_SANITIZER) || defined(THREAD_SANITIZER) || \
    defined(ADDRESS_SANITIZER)
  // When using the sanitizers, we can allow the loader to use the default
  // behavior of sharing symbols between the parent process and the shared
  // object, since absl::log (among other libraries) is guaranteed to have the
  // same code, since the sanitizer-friendly intra-process implementation is
  // built from the same source tree as the parent process. For complex
  // reasons, setting RTLD_DEEPBIND here causes the sanitizers to fail with
  // many false-alarms.
  handle = dlopen((runfiles_dir + path).c_str(), RTLD_LAZY);
#else
  // The "full" externally-built IMW implementation links against the external
  // absl::log implementation (among other libraries), which is different from
  // the internal build in the parent process. Allowing the loader to share
  // symbols between the parent process and the Zenoh shared object has led to
  // undefined behavior and weird crashes in LOG() calls. To prevent this,
  // RTLD_DEEPBIND causes dlopen() to not mix symbols from the parent
  // executable with symbols it finds in the shared-object, so LOG() calls in
  // the shared-object will use the absl::log implementation and globals that
  // it was built against.
  handle = dlopen((runfiles_dir + path).c_str(), RTLD_LAZY | RTLD_DEEPBIND);
#endif

  if (handle == nullptr) {
    LOG(FATAL) << "Cannot open the shared library at: " << runfiles_dir + path;
  }
  GET_FUNCTION_PTR(handle, imw_init);
  GET_FUNCTION_PTR(handle, imw_fini);
  GET_FUNCTION_PTR(handle, imw_create_publisher);
  GET_FUNCTION_PTR(handle, imw_destroy_publisher);
  GET_FUNCTION_PTR(handle, imw_publish);
  GET_FUNCTION_PTR(handle, imw_create_subscription);
  GET_FUNCTION_PTR(handle, imw_destroy_subscription);
  GET_FUNCTION_PTR(handle, imw_keyexpr_includes);
  GET_FUNCTION_PTR(handle, imw_keyexpr_intersects);
  GET_FUNCTION_PTR(handle, imw_keyexpr_is_canon);
  GET_FUNCTION_PTR(handle, imw_version);
  GET_FUNCTION_PTR(handle, imw_create_queryable);
  GET_FUNCTION_PTR(handle, imw_destroy_queryable);
  GET_FUNCTION_PTR(handle, imw_queryable_reply);
  GET_FUNCTION_PTR(handle, imw_query);
}

absl::StatusOr<std::string> ZenohHandle::add_topic_prefix(
    absl::string_view topic) {
  if (topic.empty()) {
    return absl::InvalidArgumentError("Empty topic string");
  } else if (topic[0] == '/') {
    return absl::StrCat("in", topic);
  } else {
    return absl::StrCat("in/", topic);
  }
}

absl::StatusOr<std::string> ZenohHandle::remove_topic_prefix(
    absl::string_view topic) {
  if (topic.length() < 3) {
    return absl::InvalidArgumentError("Topic string too short");
  }
  topic.remove_prefix(2);
  return std::string(topic);
}

const ZenohHandle& Zenoh() {
  static auto* zenoh_handle = ZenohHandle::CreateZenohHandle();
  return *zenoh_handle;
}

}  // namespace intrinsic
