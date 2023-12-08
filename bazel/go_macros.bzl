# Copyright 2023 Intrinsic Innovation LLC

"""This file contains starlark rules for building golang targets."""

load("@io_bazel_rules_go//go:def.bzl", _go_binary = "go_binary", _go_library = "go_library", _go_test = "go_test")
load("@io_bazel_rules_go//proto:def.bzl", _go_grpc_library = "go_grpc_library", _go_proto_library = "go_proto_library")

go_binary = _go_binary
go_library = _go_library

def go_grpc_library(name, deps, srcs, **kwargs):
    _go_grpc_library(
        name = name,
        deps = deps,
        protos = srcs,
        **kwargs
    )

def go_proto_library(name, deps, go_deps = None, **kwargs):
    _go_proto_library(
        name = name,
        protos = deps,
        deps = go_deps,
        **kwargs
    )

def go_test(name, library = None, **kwargs):
    _go_test(
        name = name,
        embed = [library] if library else None,
        **kwargs
    )
