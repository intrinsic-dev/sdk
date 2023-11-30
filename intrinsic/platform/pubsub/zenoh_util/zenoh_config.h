// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_

#include <fstream>
#include <ios>
#include <iostream>
#include <string>

#include "absl/flags/declare.h"
#include "absl/flags/flag.h"
#include "absl/log/log.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_helpers.h"
#include "tools/cpp/runfiles/runfiles.h"

ABSL_DECLARE_FLAG(std::string, zenoh_router);

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

  // If requested by the zenoh_router flag, try to alter the default router
  // connection provided in peer_config.json
  if (!absl::GetFlag(FLAGS_zenoh_router).empty()) {
    std::string router_endpoint("tcp/zenoh-router.app-intrinsic-base:7447");
    size_t pos = config.find(router_endpoint);
    if (pos != std::string::npos) {
      config.replace(pos, router_endpoint.length(),
                     absl::GetFlag(FLAGS_zenoh_router));
    }
  }
  return config;
}

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_CONFIG_H_
