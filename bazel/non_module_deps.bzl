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

    http_archive(
        name = "io_opencensus_cpp",
        sha256 = "e3857e1267cb6329a7b23209ce8a2108b8f264e4adf336776323fb163fa23f9a",
        strip_prefix = "opencensus-cpp-50eb5de762e5f87e206c011a4f930adb1a1775b1",
        url = "https://github.com/census-instrumentation/opencensus-cpp/archive/50eb5de762e5f87e206c011a4f930adb1a1775b1.tar.gz",  # 2024-03-25
    )

    OR_TOOLS_COMMIT = "ed94162b910fa58896db99191378d3b71a5313af"  # v9.11
    http_archive(
        name = "or_tools",
        strip_prefix = "or-tools-%s" % OR_TOOLS_COMMIT,
        sha256 = "6210f90131ae7256feab097835e3d411316c19d7e9756399079b8595088a7aa5",
        urls = ["https://github.com/google/or-tools/archive/%s.tar.gz" % OR_TOOLS_COMMIT],
    )

    ################################
    # Google OSS replacement files #
    #      go/insrc-g3-to-oss      #
    ################################

    XLS_COMMIT = "507b33b5bdd696adb7933a6617b65c70e46d4703"  # 2024-03-06
    http_file(
        name = "com_google_xls_strong_int_h",
        downloaded_file_path = "strong_int.h",
        urls = ["https://raw.githubusercontent.com/google/xls/%s/xls/common/strong_int.h" % XLS_COMMIT],
        sha256 = "4daad402bc0913e05b83d0bded9dd699738935e6d59d1424c99c944d6e0c2897",
    )

non_module_deps_ext = module_extension(implementation = _non_module_deps_impl)
