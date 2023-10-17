# Copyright 2023 Intrinsic Innovation LLC

"""This file contains basic unit tests for label.bzl"""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":label.bzl", "absolute_label", "parse_label")

def _absolute_label_test_impl(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, "@foo//bar:baz", absolute_label("@foo//bar:baz"))
    asserts.equals(env, "@foo//bar:baz", absolute_label("//bar:baz", repository_name = "@foo"))
    asserts.equals(env, "@foo//bar:bar", absolute_label("//bar", repository_name = "@foo"))
    asserts.equals(env, "@foo//bar:baz", absolute_label(":baz", repository_name = "@foo", package_name = "bar"))
    asserts.equals(env, "@foo//bar:baz", absolute_label("baz", repository_name = "@foo", package_name = "bar"))
    return unittest.end(env)

absolute_label_test = unittest.make(_absolute_label_test_impl)

def _parse_label_test_impl(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, ("foo", "bar", "baz"), parse_label("@foo//bar:baz"))
    asserts.equals(env, ("foo", "bar", "bar"), parse_label("@foo//bar"))
    return unittest.end(env)

parse_label_test = unittest.make(_parse_label_test_impl)

# No need for a test_myhelper() setup function.

def label_test_suite():
    unittest.suite(
        "absolute_label_test",
        absolute_label_test,
    )

    unittest.suite(
        "parse_label_test",
        parse_label_test,
    )
