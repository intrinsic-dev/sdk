// Copyright 2023 Intrinsic Innovation LLC

// A custom main for running unit tests and microbenchmarks.

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <cstdio>

#include "absl/flags/parse.h"
#include "benchmark/benchmark.h"

int main(int argc, char** argv) {
  printf("Running main() from %s\n", __FILE__);

  // Run benchmarks if there are any and --benchmark_filter is provided.
  benchmark::Initialize(&argc, argv);
  if (!benchmark::GetBenchmarkFilter().empty()) {
    benchmark::RunSpecifiedBenchmarks();
    benchmark::Shutdown();
    return 0;
  }

  // Run unit tests if there are any. Since Google Mock depends on Google
  // Test, InitGoogleMock() is also responsible for initializing Google Test.
  // Thus, there is no need to call InitGoogleTest() separately. Note that
  // not calling InitGoogleTest() before calling RUN_ALL_TESTS() is INVALID.
  // Valid usage will be enforced in the future.
  testing::InitGoogleMock(&argc, argv);

  // absl::ParseCommandLine to return error on invalid flags.
  absl::ParseCommandLine(argc, argv);

  return RUN_ALL_TESTS();
}
