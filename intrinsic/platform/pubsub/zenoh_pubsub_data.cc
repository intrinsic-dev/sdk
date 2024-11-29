// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_pubsub_data.h"

#include <memory>
#include <string>
#include <string_view>

#include "absl/base/const_init.h"
#include "absl/base/no_destructor.h"
#include "absl/log/log.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_config.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

namespace intrinsic {

namespace {
static constinit absl::Mutex session_mutex(absl::kConstInit);
}

namespace {
std::shared_ptr<int> GetSessionData(std::string_view config_param) {
  static absl::NoDestructor<std::shared_ptr<int>> session_data;
  absl::MutexLock lock(&session_mutex);
  if (!*session_data) {
    *session_data = std::make_shared<int>();
  }

  // The session data was just created, or the previous session had been torn
  // down and the static variable above is the only reference.
  if (session_data->use_count() == 1) {
    std::string config(config_param);
    if (config.empty()) {
      config = intrinsic::GetZenohPeerConfig();
      if (config.empty()) {
        LOG(FATAL) << "Could not get PubSub peer config";
      }
    }
    imw_ret_t ret = Zenoh().imw_init(config.c_str());
    if (ret != IMW_OK) {
      LOG(FATAL) << "Error creating a zenoh session with config " << config;
    }
    LOG(INFO) << "Created a zenoh session with libimw_zenoh version: "
              << Zenoh().imw_version();
  }

  return *session_data;
}
}  // namespace

class PubSubData::Session {
 public:
  explicit Session(std::string_view config_param = std::string_view())
      : session_data_(GetSessionData(config_param)) {}
  ~Session() {
    absl::MutexLock lock(&session_mutex);
    // Last instance is being destroyed, kill pubsub session.
    // == 2: one reference is in static session_data in GetSessionData above.
    // The other reference is this Session instance that is about to be deleted.
    if (session_data_.use_count() == 2) {
      Zenoh().imw_fini();
    }
  }

 private:
  std::shared_ptr<int> session_data_;
};

PubSubData::PubSubData(std::string_view config_param)
    : session_(std::make_shared<Session>(config_param)) {}

}  // namespace intrinsic
