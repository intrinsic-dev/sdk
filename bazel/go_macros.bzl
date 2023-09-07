# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""This file contains starlark rules for building golang targets."""

load("@io_bazel_rules_go//go:def.bzl", _go_binary = "go_binary", _go_library = "go_library", _go_test = "go_test")
load("@io_bazel_rules_go//proto:def.bzl", _go_proto_library = "go_proto_library")

def go_binary(name, **kwargs):
    _go_binary(
        name = name,
        importpath = "%s/%s" % (native.package_name(), name),
        **kwargs
    )

def go_library(name, **kwargs):
    _go_library(
        name = name,
        importpath = "%s/%s" % (native.package_name(), name),
        **kwargs
    )

def go_grpc_library(name, deps, srcs, **kwargs):
    _go_proto_library(
        name = name,
        compilers = ["@io_bazel_rules_go//proto:go_grpc"],
        deps = deps,
        protos = srcs,
        importpath = "%s/%s" % (native.package_name(), name),
        **kwargs
    )

def go_proto_library(name, deps, go_deps = None, **kwargs):
    _go_proto_library(
        name = name,
        protos = deps,
        deps = go_deps,
        importpath = "%s/%s" % (native.package_name(), name),
        **kwargs
    )

def go_test(name, library = None, **kwargs):
    _go_test(
        name = name,
        embed = [library] if library else None,
        **kwargs
    )
