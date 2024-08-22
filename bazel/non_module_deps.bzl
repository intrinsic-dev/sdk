# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for non-module dependencies
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive", "http_file", "http_jar")

def _non_module_deps_impl(ctx):  # @unused
    # Sysroot and libc
    # How to upgrade:
    # - Find image in https://storage.googleapis.com/chrome-linux-sysroot/ for amd64 for
    #   a stable Linux (here: Debian bullseye), of this pick a current build.
    # - Verify the image contains expected /lib/x86_64-linux-gnu/libc* and defines correct
    #   __GLIBC_MINOR__ in /usr/include/features.h
    # - If system files are not found, add them in ../BUILD.sysroot
    http_archive(
        name = "com_googleapis_storage_chrome_linux_amd64_sysroot",
        build_file = Label("//intrinsic/production/external:BUILD.sysroot"),
        sha256 = "5df5be9357b425cdd70d92d4697d07e7d55d7a923f037c22dc80a78e85842d2c",
        urls = [
            # features.h defines GLIBC 2.31.
            "https://storage.googleapis.com/chrome-linux-sysroot/toolchain/4f611ec025be98214164d4bf9fbe8843f58533f7/debian_bullseye_amd64_sysroot.tar.xz",
        ],
    )

    http_archive(
        name = "com_google_cel_cpp",
        url = "https://github.com/google/cel-cpp/archive/037873163975964a80a188ad7f936cb4f37f0684.tar.gz",  # 2024-01-29
        strip_prefix = "cel-cpp-037873163975964a80a188ad7f936cb4f37f0684",
        sha256 = "d56e8c15b55240c92143ee3ed717956c67961a24f97711ca410030de92633288",
    )

    # Last released version 3.4.0 has been released 2 years ago
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

    http_archive(
        name = "io_opencensus_cpp",
        sha256 = "e3857e1267cb6329a7b23209ce8a2108b8f264e4adf336776323fb163fa23f9a",
        strip_prefix = "opencensus-cpp-50eb5de762e5f87e206c011a4f930adb1a1775b1",
        url = "https://github.com/census-instrumentation/opencensus-cpp/archive/50eb5de762e5f87e206c011a4f930adb1a1775b1.tar.gz",  # 2024-03-25
    )
    OR_TOOLS_COMMIT = "286089e617f75b8aa9a01eaaaec218d843370159"  # Added RecursivelyCreateDir
    http_archive(
        name = "or_tools",
        strip_prefix = "or-tools-%s" % OR_TOOLS_COMMIT,
        sha256 = "58d014109d50b90b02b422171264f5dfa53af1df5d12783de0d510536789cac3",
        urls = ["https://github.com/google/or-tools/archive/%s.tar.gz" % OR_TOOLS_COMMIT],
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

non_module_deps_ext = module_extension(implementation = _non_module_deps_impl)
