// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_

#include <fstream>
#include <ios>
#include <iostream>
#include <string>

#include "absl/log/log.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_helpers.h"
#include "tools/cpp/runfiles/runfiles.h"

namespace intrinsic {

inline std::string GetZenohPeerConfig() {
  std::string config;

  std::string config_path =
      "/intrinsic/platform/pubsub/zenoh_util/peer_config.json";
  std::string runfiles_path;

  if (!RunningInKubernetes()) {
    runfiles_path =
        bazel::tools::cpp::runfiles::Runfiles::Create("")->Rlocation(
            "ai_intrinsic_sdks");
  }

  std::ifstream file(runfiles_path + config_path);
  if (file.is_open()) {
    // Read the entire file into a string
    file.seekg(0, std::ios::end);
    config.resize(file.tellg());
    file.seekg(0, std::ios::beg);
    file.read(&config[0], config.size());
    file.close();
  } else {
    LOG(ERROR) << "Could not open config file: " << runfiles_path + config_path;
  }

  if (!config.empty()) {
    if (RunningUnderTest()) {
      // Remove listen endpoints when running in test. (go/forge-limits#ipv4)
      std::string listenIp("\"tcp/0.0.0.0:0\"");
      size_t pos = config.find(listenIp);
      config.replace(pos, listenIp.length(), std::string(""));
    } else if (const char* allowed_ip = getenv("ALLOWED_PUBSUB_IPv4");
               allowed_ip != nullptr) {
      std::string listenIp("0.0.0.0");
      size_t pos = config.find(listenIp);
      config.replace(pos, listenIp.length(), std::string(allowed_ip));
    }
  }
  return config;
}

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_
