# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for @com_google_googleapis
"""

load("@com_google_googleapis//:repository_rules.bzl", "switched_rules_by_language")

def extension_for_com_google_googleapis():
    switched_rules_by_language(
        name = "com_google_googleapis_imports",
        cc = True,
        grpc = True,
        python = True,
        go = True,
    )

def _extension_for_com_google_googleapis_impl(ctx):  # @unused
    extension_for_com_google_googleapis()

extension_for_com_google_googleapis_ext = module_extension(implementation = _extension_for_com_google_googleapis_impl)
