# Copyright 2023 Intrinsic Innovation LLC

"""Shared Python helpers for usage in other workspaces."""

load("@local_config_python//:defs.bzl", _interpreter = "interpreter")

# Target (string) of the interpreter of the Python toolchain which is setup as
# part of the workspace macros intrinsic_sdks_deps_0()-intrinsic_sdks_deps_3().
#
# Useful, e.g., to add your own pip requirements in your WORKSPACE file:
#
#   # Call intrinsic_sdks_deps_0()-intrinsic_sdks_deps_3() (see deps_0.bzl).
#
#   load("@rules_python//python:pip.bzl", "pip_parse")
#   load("@ai_intrinsic_sdks//bazel:python.bzl", "interpreter")
#   pip_parse(
#     name = "my_pip_deps",
#     python_interpreter_target = interpreter,
#     requirements_lock = "//:requirements.txt",
#   )
#
#   load("@my_pip_deps//:requirements.bzl", "install_deps")
#   install_deps()
#
interpreter = _interpreter
