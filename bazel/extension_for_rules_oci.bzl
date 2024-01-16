# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for @rules_oci
"""

load("@rules_oci//oci:pull.bzl", "oci_pull")

def extension_for_rules_oci():
    oci_pull(
        name = "distroless_base_amd64_oci",
        digest = "sha256:eaddb8ca70848a43fab351226d9549a571f68d9427c53356114fedd3711b5d73",
        image = "gcr.io/distroless/base",
    )

    oci_pull(
        name = "distroless_python3",
        digest = "sha256:baac841d0711ecbb673fa410a04793f876a242a6ca801d148ef867f02745b156",
        image = "gcr.io/distroless/python3",
        platforms = ["linux/amd64"],
    )

def _extension_for_rules_oci_impl(ctx):  # @unused
    extension_for_rules_oci()

extension_for_rules_oci_ext = module_extension(implementation = _extension_for_rules_oci_impl)
