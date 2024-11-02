# Copyright 2023 Intrinsic Innovation LLC

"""Common build definitions for testing."""

load("//intrinsic/testing/dockerized_test_executor:delegated_test.bzl", "delegated_test")

DEFAULT_CLOUD_GUITAR_POOL = "sim-prod-v20240913-rc01"

_INTRINSIC_INTEGRATION_TESTS = "intrinsic-integration-tests"

def intrinsic_cloud_guitar_test(
        name,
        test,
        timeout_minutes,
        pool = DEFAULT_CLOUD_GUITAR_POOL,
        pool_type = "regular_vm",
        presubmit = True,
        spot_vm = True,
        extra_runfiles_generator = None,
        project = _INTRINSIC_INTEGRATION_TESTS):
    """Creates a Cloud Guitar test.

    A Cloud Guitar test will do the same as the local test, but is runnable on Borg
    and will execute on a Cloud Guitar (go/intrinsic-cloud-guitar) worker.
    This test will automatically be picked up and executed by the cloud guitar workflow,
    there's no need to add it to a blueprint file.

    Args:
      name: The generated test's name.
      test: A _test rule.
      timeout_minutes: Timeout per test.
      pool: string. A cloud guitar pool to schedule the test on.
      pool_type: string (one of: "regular_vm", "big_vm") to indicate which vms should underpin the pool
      presubmit: Bool to run this test in the presubmit, or not.
      extra_runfiles_generator: If non-empty, a binary that generates extra runfiles.
      project: Project where this test should run.
    """

    tags = []
    if presubmit:
        if timeout_minutes > 27:
            fail("workflow %s is too long for presubmit" % native.package_name())

        tags = ["intrinsic_cloud_guitar_presubmit"]

    if project != _INTRINSIC_INTEGRATION_TESTS and pool.startswith("sim"):
        fail("'{}' is the only project where we have a fleet of test VMs. If you want to run your test in '{}', please specify a workcell.".format(_INTRINSIC_INTEGRATION_TESTS, project))

    delegated_test(
        name = name,
        wrapped_test = test,
        timeout_minutes = timeout_minutes,
        pool = pool,
        pool_type = pool_type,
        spot_vm = spot_vm,
        project = project,
        storage_bucket = project + "-cloud-guitar",
        visibility = ["//intrinsic/testing:__subpackages__"],
        tags = tags + ["guitar", pool_type],
        extra_runfiles_generator = extra_runfiles_generator,
    )
