# Copyright 2023 Intrinsic Innovation LLC

"""This file contains starlark rules for building golang targets."""

load("@io_bazel_rules_go//go:def.bzl", _go_binary = "go_binary", _go_library = "go_library", _go_test = "go_test")
load("@io_bazel_rules_go//proto:def.bzl", _go_grpc_library = "go_grpc_library", _go_proto_library = "go_proto_library")

# Only for use in this repository. Other repositories should use the rules from rules_go directly.
visibility(["//..."])

def calculate_importpath(name):
    label = native.package_relative_label(name)
    return label.package + "/" + label.name

def go_binary(name, **kwargs):
    _go_binary(
        name = name,
        importpath = calculate_importpath(name),
        **kwargs
    )

def go_library(name, **kwargs):
    _go_library(
        name = name,
        importpath = calculate_importpath(name),
        **kwargs
    )

def go_grpc_library(name, srcs, deps = None, **kwargs):
    _go_grpc_library(
        name = name,
        deps = deps,
        protos = srcs,
        importpath = calculate_importpath(name),
        **kwargs
    )

def go_proto_library(name, deps, go_deps = None, **kwargs):
    _go_proto_library(
        name = name,
        protos = deps,
        deps = go_deps,
        importpath = calculate_importpath(name),
        **kwargs
    )

def go_test(name, library = None, **kwargs):
    _go_test(
        name = name,
        embed = [library] if library else None,
        importpath = calculate_importpath(name),
        **kwargs
    )
