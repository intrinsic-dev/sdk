# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for non-module dependencies
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive", "http_file", "http_jar")

def non_module_deps():
    """
    Declare repos here which have not been migrated to Bzlmod yet.
    """

    # Sysroot and libc
    # How to upgrade:
    # - Find image in https://storage.googleapis.com/chrome-linux-sysroot/ for amd64 for
    #   a stable Linux (here: Debian stretch), of this pick a current build.
    # - Verify the image contains expected /lib/x86_64-linux-gnu/libc* and defines correct
    #   __GLIBC_MINOR__ in /usr/include/features.h
    # - If system files are not found, add them in ../BUILD.sysroot
    http_archive(
        name = "com_googleapis_storage_chrome_linux_amd64_sysroot",
        build_file = Label("//intrinsic/production/external:BUILD.sysroot"),
        sha256 = "66bed6fb2617a50227a824b1f9cfaf0a031ce33e6635edaa2148f71a5d50be48",
        urls = [
            # features.h defines GLIBC 2.24. Contains /lib/x86_64-linux-gnu/libc-2.24.so,
            # last modified by Chrome 2018-02-22.
            "https://storage.googleapis.com/chrome-linux-sysroot/toolchain/15b7efb900d75f7316c6e713e80f87b9904791b1/debian_stretch_amd64_sysroot.tar.xz",
        ],
    )

    http_jar(
        name = "firestore_emulator",
        sha256 = "1f08a8f7133edf2e7b355db0da162654df2b0967610d3de2f12b8ce07c493f5f",
        urls = ["https://storage.googleapis.com/firebase-preview-drop/emulator/cloud-firestore-emulator-v1.18.2.jar"],
    )

    http_archive(
        name = "com_google_cel_cpp",
        url = "https://github.com/google/cel-cpp/archive/037873163975964a80a188ad7f936cb4f37f0684.tar.gz",  # 2024-01-29
        strip_prefix = "cel-cpp-037873163975964a80a188ad7f936cb4f37f0684",
        sha256 = "d56e8c15b55240c92143ee3ed717956c67961a24f97711ca410030de92633288",
    )

    # Eigen math library.
    # Repository name should be com_gitlab_libeigen_eigen to serve
    # as transitive dependency for com_google_ceres_solver
    # BCR version is 2 years behind, so we use a specific commit and http_archive.
    EIGEN_COMMIT = "38b9cc263bbaeb03ce408a4e26084543a6c0dedb"  # 2024-05-30
    http_archive(
        name = "com_gitlab_libeigen_eigen",
        build_file = Label("//intrinsic/production/external:BUILD.eigen"),
        sha256 = "136102d1241eb73f0ed3e1f47830707d1e40016ef61ed2d682c1398392879401",
        strip_prefix = "eigen-%s" % EIGEN_COMMIT,
        urls = [
            "https://gitlab.com/libeigen/eigen/-/archive/%s/eigen-%s.zip" % (EIGEN_COMMIT, EIGEN_COMMIT),
        ],
    )

    ################################
    # Google OSS replacement files #
    ################################

    XLS_COMMIT = "507b33b5bdd696adb7933a6617b65c70e46d4703"  # 2024-03-06
    http_file(
        name = "com_google_xls_strong_int_h",
        downloaded_file_path = "strong_int.h",
        urls = ["https://raw.githubusercontent.com/google/xls/%s/xls/common/strong_int.h" % XLS_COMMIT],
        sha256 = "4daad402bc0913e05b83d0bded9dd699738935e6d59d1424c99c944d6e0c2897",
    )

def _non_module_deps_impl(ctx):  # @unused
    non_module_deps()

non_module_deps_ext = module_extension(implementation = _non_module_deps_impl)
