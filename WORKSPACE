# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

workspace(name = "ai_intrinsic_sdks")

# Suppress "bazel_gazelle is not declared in WORKSPACE" error caused
# by 'bazel_gazelle' being declared inside of intrinsic_sdks_deps_0().
# gazelle:repo bazel_gazelle

# Load shared dependencies for Intrinsic SDKs.
#
# New dependencies should be added to these workspace macros only if they are
# useful in other workspaces that depend on this workspace. Otherwise, add new
# dependencies directly to this workspace file.
load("//bazel:deps_0.bzl", "intrinsic_sdks_deps_0")

intrinsic_sdks_deps_0()

load("//bazel:deps_1.bzl", "intrinsic_sdks_deps_1")

intrinsic_sdks_deps_1()

load("//bazel:deps_2.bzl", "intrinsic_sdks_deps_2")

intrinsic_sdks_deps_2()

load("//bazel:deps_3.bzl", "intrinsic_sdks_deps_3")

intrinsic_sdks_deps_3()

# Exclude examples from "bazel build //..."
local_repository(
    name = "examples",
    path = "./examples/",
)