# Copyright 2023 Intrinsic Innovation LLC

"""Macro to set up two cc_test from one source with and without malloc counting."""

def cc_test_and_malloc_test(name, deps = [], local_defines = [], tags = [], **kwargs):
    """
    TODO(b/289937660)
    Not implemented in insrc. Acts merely as a placeholder, invoking a cc_test.
    """

    native.cc_test(
        name = name,
        local_defines = local_defines,
        tags = tags,
        deps = deps + ["//intrinsic/util/testing:gtest_wrapper"],
        **kwargs
    )
