// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_util/zenoh_helpers.h"

#include <cstdlib>

namespace intrinsic {

bool RunningUnderTest() {
  return (getenv("TEST_TMPDIR") != nullptr) ||
         (getenv("PORTSERVER_ADDRESS") != nullptr);
}

bool RunningInKubernetes() {
  return getenv("KUBERNETES_SERVICE_HOST") != nullptr;
}

}  // namespace intrinsic
