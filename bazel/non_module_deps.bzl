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

    http_archive(
        name = "com_github_google_flatbuffers",
        urls = [
            "https://github.com/google/flatbuffers/archive/refs/tags/v23.3.3.tar.gz",
        ],
        sha256 = "8aff985da30aaab37edf8e5b02fda33ed4cbdd962699a8e2af98fdef306f4e4d",
        strip_prefix = "flatbuffers-23.3.3",
    )
    http_jar(
        name = "firestore_emulator",
        sha256 = "1f08a8f7133edf2e7b355db0da162654df2b0967610d3de2f12b8ce07c493f5f",
        urls = ["https://storage.googleapis.com/firebase-preview-drop/emulator/cloud-firestore-emulator-v1.18.2.jar"],
    )

    http_archive(
        name = "io_opentelemetry_cpp",
        urls = [
            "https://storage.googleapis.com/cloud-cpp-community-archive/io_opentelemetry_cpp/v1.13.0.tar.gz",
            "https://github.com/open-telemetry/opentelemetry-cpp/archive/v1.13.0.tar.gz",
        ],
        sha256 = "7735cc56507149686e6019e06f588317099d4522480be5f38a2a09ec69af1706",
        strip_prefix = "opentelemetry-cpp-1.13.0",
    )

    # GMock matchers for protocol buffers
    http_archive(
        name = "com_github_inazarenko_protobuf_matchers",
        sha256 = "dbe84ce7cb476580f1f3029e2412d961338d09a3d6ac794e1d3560dc542f1a08",
        strip_prefix = "protobuf-matchers-a76296f5d5369d57f44126acf59c290a397490c6",
        url = "https://github.com/inazarenko/protobuf-matchers/archive/a76296f5d5369d57f44126acf59c290a397490c6.tar.gz",
    )

    http_archive(
        name = "com_google_cel_cpp",
        url = "https://github.com/google/cel-cpp/archive/037873163975964a80a188ad7f936cb4f37f0684.tar.gz",  # 2024-01-29
        strip_prefix = "cel-cpp-037873163975964a80a188ad7f936cb4f37f0684",
        sha256 = "d56e8c15b55240c92143ee3ed717956c67961a24f97711ca410030de92633288",
    )

    http_archive(
        name = "com_google_riegeli",
        url = "https://github.com/google/riegeli/archive/1d90cec619f9b9660ff2db6eb3e35f5ea65dddb2.tar.gz",  # 2024-04-04
        strip_prefix = "riegeli-1d90cec619f9b9660ff2db6eb3e35f5ea65dddb2",
        sha256 = "2304f64a246181b94083cdbc86d69c4b93346c196f93b2c5f05a93767bec793d",
    )

    XLS_COMMIT = "507b33b5bdd696adb7933a6617b65c70e46d4703"  # 2024-03-06
    http_file(
        name = "com_google_xls_strong_int_h",
        downloaded_file_path = "strong_int.h",
        urls = ["https://raw.githubusercontent.com/google/xls/%s/xls/common/strong_int.h" % XLS_COMMIT],
        sha256 = "4daad402bc0913e05b83d0bded9dd699738935e6d59d1424c99c944d6e0c2897",
    )

    http_archive(
        name = "pybind11_abseil",
        sha256 = "1496b112e86416e2dcf288569a3e7b64f3537f0b18132224f492266e9ff76c44",
        strip_prefix = "pybind11_abseil-202402.0",
        urls = ["https://github.com/pybind/pybind11_abseil/archive/refs/tags/v202402.0.tar.gz"],
    )

    http_archive(
        name = "pybind11_protobuf",
        sha256 = "59c5fbb6dfe1427d41217eb58386f16940b6c8d6ff63407a72566daa4f343f59",
        strip_prefix = "pybind11_protobuf-b4a2e87a10cd5f6309e4ff67c040a470d7ec2373",
        urls = ["https://github.com/pybind/pybind11_protobuf/archive/b4a2e87a10cd5f6309e4ff67c040a470d7ec2373.tar.gz"],  #  Feb 23, 2024
    )

def _non_module_deps_impl(ctx):  # @unused
    non_module_deps()

non_module_deps_ext = module_extension(implementation = _non_module_deps_impl)
