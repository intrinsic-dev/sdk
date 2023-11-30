// Copyright 2023 Intrinsic Innovation LLC

#include <string>

#include "absl/flags/flag.h"

ABSL_FLAG(std::string, zenoh_router, "",
          "Override the default Zenoh connection to PROTOCOL/HOSTNAME:PORT");
