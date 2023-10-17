# Copyright 2023 Intrinsic Innovation LLC

"""Workspace dependencies needed for the Intrinsic SDKs as a 3rd-party consumer (part 3)."""

# Python pip dependencies
load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "install_deps")

def intrinsic_sdks_deps_3():
    """Loads workspace dependencies needed for the Intrinsic SDKs.

    This is one out of several non-optional parts. Please see intrinsic_sdks_deps_0() in
    intrinsic_sdks_deps_0.bzl for more details."""

    # Python pip dependencies
    install_deps()
