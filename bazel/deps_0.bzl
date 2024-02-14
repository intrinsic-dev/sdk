# Copyright 2023 Intrinsic Innovation LLC

"""Workspace dependencies needed for the Intrinsic SDKs as a 3rd-party consumer (part 0)."""

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive", "http_jar")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")
load("//bazel:non_module_deps.bzl", "non_module_deps")

def intrinsic_sdks_deps_0():
    """Loads workspace dependencies needed for the Intrinsic SDKs.

    This is only the first part. Projects which want to use the Intrinsic SDKs with Bazel and which
    don't define the necessary dependencies in another way need to call *all* macros. E.g., do the
    following in your WORKSPACE:

    git_repository(name = "com_googlesource_intrinsic_intrinsic_sdks", remote = "...", ...)
    load("@com_googlesource_intrinsic_intrinsic_sdks//bazel:deps_0.bzl", "intrinsic_sdks_deps_0")
    intrinsic_sdks_deps_0()
    load("@com_googlesource_intrinsic_intrinsic_sdks//bazel:deps_1.bzl", "intrinsic_sdks_deps_1")
    intrinsic_sdks_deps_1()
    load("@com_googlesource_intrinsic_intrinsic_sdks//bazel:deps_2.bzl", "intrinsic_sdks_deps_2")
    intrinsic_sdks_deps_2()
    load("@com_googlesource_intrinsic_intrinsic_sdks//bazel:deps_3.bzl", "intrinsic_sdks_deps_3")
    intrinsic_sdks_deps_3()

    The reason why this is split into multiple files and macros is that .bzl-files can only contain
    loads at the very top. Loads and macro calls that depend on a previous macro call in this file
    are located in intrinsic_sdks_deps_1.bzl/intrinsic_sdks_deps_1() and so on.
    """

    # Include non-bzlmod dependencies
    non_module_deps()

    # Go rules and toolchain
    maybe(
        http_archive,
        name = "io_bazel_rules_go",
        sha256 = "7c76d6236b28ff695aa28cf35f95de317a9472fd1fb14ac797c9bf684f09b37c",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.44.2/rules_go-v0.44.2.zip",
            "https://github.com/bazelbuild/rules_go/releases/download/v0.44.2/rules_go-v0.44.2.zip",
        ],
    )

    maybe(
        http_archive,
        name = "bazel_gazelle",
        sha256 = "d3fa66a39028e97d76f9e2db8f1b0c11c099e8e01bf363a923074784e451f809",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-gazelle/releases/download/v0.33.0/bazel-gazelle-v0.33.0.tar.gz",
            "https://github.com/bazelbuild/bazel-gazelle/releases/download/v0.33.0/bazel-gazelle-v0.33.0.tar.gz",
        ],
    )

    # CC toolchain
    maybe(
        http_archive,
        name = "toolchains_llvm",
        sha256 = "b7cd301ef7b0ece28d20d3e778697a5e3b81828393150bed04838c0c52963a01",
        strip_prefix = "toolchains_llvm-0.10.3",
        canonical_id = "0.10.3",
        url = "https://github.com/grailbio/bazel-toolchain/releases/download/0.10.3/toolchains_llvm-0.10.3.tar.gz",
    )

    # Python rules, toolchain and pip dependencies
    maybe(
        http_archive,
        name = "rules_python",
        strip_prefix = "rules_python-0.27.1",
        url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.27.1.zip",
        sha256 = "19250cc0ab89f052131137a58c993d988d74637b52a5b137a4264d9917c13a3e",
    )

    maybe(
        http_archive,
        name = "rules_license",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/rules_license/releases/download/0.0.7/rules_license-0.0.7.tar.gz",
            "https://github.com/bazelbuild/rules_license/releases/download/0.0.7/rules_license-0.0.7.tar.gz",
        ],
        sha256 = "4531deccb913639c30e5c7512a054d5d875698daeb75d8cf90f284375fe7c360",
    )

    maybe(
        http_archive,
        name = "rules_pkg",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/rules_pkg/releases/download/0.8.1/rules_pkg-0.8.1.tar.gz",
            "https://github.com/bazelbuild/rules_pkg/releases/download/0.8.1/rules_pkg-0.8.1.tar.gz",
        ],
        sha256 = "8c20f74bca25d2d442b327ae26768c02cf3c99e93fad0381f32be9aab1967675",
    )

    maybe(
        http_archive,
        name = "aspect_bazel_lib",
        sha256 = "4c1de11ebabc23a3c976b73a2b2647596f545beda8a61d2c1c034e07f3f8b976",
        strip_prefix = "bazel-lib-2.0.2",
        url = "https://github.com/aspect-build/bazel-lib/releases/download/v2.0.2/bazel-lib-v2.0.2.tar.gz",
    )

    maybe(
        http_archive,
        name = "rules_oci",
        sha256 = "686f871f9697e08877b85ea6c16c8d48f911bf466c3aeaf108ca0ab2603c7306",
        strip_prefix = "rules_oci-1.5.1",
        url = "https://github.com/bazel-contrib/rules_oci/releases/download/v1.5.1/rules_oci-v1.5.1.tar.gz",
    )

    # Overrides gRPC's dependency on re2. Solves a build error in opt mode
    # http://b/277071259
    # http://go/upsalite-prod/8e107935-5aad-422c-bda4-747ffd58f4b9/targets
    RE2_COMMIT = "055e1241fcfde4f19f072b4dd909a824de54ceb8"  # tag: 2023-03-01
    maybe(
        git_repository,
        name = "com_googlesource_code_re2",
        commit = RE2_COMMIT,
        remote = "https://github.com/google/re2.git",
        shallow_since = "1645717357 +0000",
    )

    # Another alias for RE2
    maybe(
        git_repository,
        name = "com_github_google_re2",
        commit = RE2_COMMIT,
        remote = "https://github.com/google/re2.git",
        shallow_since = "1645717357 +0000",
    )

    # Protobuf
    maybe(
        http_archive,
        name = "com_google_protobuf",
        sha256 = "2dc7254fc975bb40efcab799273c9330d7ed11f4b3263dcbf7328f5c6b067d3e",  # v3.23.1
        strip_prefix = "protobuf-2dca62f7296e5b49d729f7384f975cecb38382a0",  # v3.23.1
        urls = ["https://github.com/protocolbuffers/protobuf/archive/2dca62f7296e5b49d729f7384f975cecb38382a0.zip"],  # v3.23.1
    )

    # gRPC
    maybe(
        http_archive,
        name = "com_github_grpc_grpc",
        patch_args = ["-p1"],
        patches = [
            Label("//intrinsic/production/external/patches:0003-Remove-competing-local_config_python-definition.patch"),
            Label("//intrinsic/production/external/patches:0005-Remove-competing-go-deps.patch"),
            Label("//intrinsic/production/external/patches:0007-Also-generate-pyi-files-grpc.patch"),
            Label("//intrinsic/production/external/patches:0011-Public-grpc_library-attr.patch"),
        ],
        sha256 = "194dcaae20b7bcd9fc4fc9a1e091215207842ddb9a1df01419c7c55d3077979b",  # v1.56.0
        strip_prefix = "grpc-6e85620c7e258df79666a4743f862f2f82701c2d",  # v1.56.0
        urls = ["https://github.com/grpc/grpc/archive/6e85620c7e258df79666a4743f862f2f82701c2d.zip"],  # v1.56.0
    )

    # Dependency of Protobuf and gRPC, explicitly pinned here so that we don't get the definition
    # from protobuf_deps() which applies a patch that does not build in our WORKSPACE. See
    # https://github.com/protocolbuffers/protobuf/blob/2dca62f7296e5b49d729f7384f975cecb38382a0/protobuf_deps.bzl#L156
    # Here we use a copy of gRPC's definition, see
    # https://github.com/grpc/grpc/blob/0bf4a618b17a3f0ed61c22364913c7f66fc1c61a/bazel/grpc_deps.bzl#L393-L402
    maybe(
        http_archive,
        name = "upb",
        sha256 = "7d19f2ac9c1e508a86a272913d9aa67c8147827f949035828910bb05d9f2cf03",  # Commit from May 16, 2023
        strip_prefix = "upb-61a97efa24a5ce01fb8cc73c9d1e6e7060f8ea98",  # Commit from May 16, 2023
        urls = [
            # https://github.com/protocolbuffers/upb/commits/23.x
            "https://storage.googleapis.com/grpc-bazel-mirror/github.com/protocolbuffers/upb/archive/61a97efa24a5ce01fb8cc73c9d1e6e7060f8ea98.tar.gz",  # Commit from May 16, 2023
            "https://github.com/protocolbuffers/upb/archive/61a97efa24a5ce01fb8cc73c9d1e6e7060f8ea98.tar.gz",  # Commit from May 16, 2023
        ],
    )

    # GoogleTest/GoogleMock framework. Used by most unit-tests.
    maybe(
        http_archive,
        name = "com_google_googletest",
        sha256 = "ad7fdba11ea011c1d925b3289cf4af2c66a352e18d4c7264392fead75e919363",
        strip_prefix = "googletest-1.13.0",
        urls = ["https://github.com/google/googletest/archive/refs/tags/v1.13.0.tar.gz"],
    )

    # Google benchmark.
    maybe(
        http_archive,
        name = "com_github_google_benchmark",
        sha256 = "59f918c8ccd4d74b6ac43484467b500f1d64b40cc1010daa055375b322a43ba3",
        strip_prefix = "benchmark-16703ff83c1ae6d53e5155df3bb3ab0bc96083be",
        urls = ["https://github.com/google/benchmark/archive/16703ff83c1ae6d53e5155df3bb3ab0bc96083be.zip"],
    )

    # Google Commandline Flags.
    maybe(
        http_archive,
        name = "com_github_gflags_gflags",
        sha256 = "19713a36c9f32b33df59d1c79b4958434cb005b5b47dc5400a7a4b078111d9b5",
        strip_prefix = "gflags-2.2.2",
        urls = [
            "https://github.com/gflags/gflags/archive/refs/tags/v2.2.2.zip",
        ],
    )

    # Google Logging Library.
    maybe(
        http_archive,
        name = "com_github_google_glog",
        sha256 = "122fb6b712808ef43fbf80f75c52a21c9760683dae470154f02bddfc61135022",
        strip_prefix = "glog-0.6.0",
        urls = [
            "https://github.com/google/glog/archive/refs/tags/v0.6.0.zip",
        ],
    )

    # C++ rules for Bazel.
    maybe(
        http_archive,
        name = "rules_cc",
        sha256 = "2037875b9a4456dce4a79d112a8ae885bbc4aad968e6587dca6e64f3a0900cdf",
        strip_prefix = "rules_cc-0.0.9",
        urls = [
            "https://github.com/bazelbuild/rules_cc/releases/download/0.0.9/rules_cc-0.0.9.tar.gz",
        ],
    )

    # Eigen math library.
    # Repository name should be com_gitlab_libeigen_eigen to serve
    # as transitive dependency for com_google_ceres_solver
    maybe(
        http_archive,
        name = "com_gitlab_libeigen_eigen",
        build_file = Label("//intrinsic/production/external:BUILD.eigen"),
        sha256 = "1ccaabbfe870f60af3d6a519c53e09f3dcf630207321dffa553564a8e75c4fc8",
        strip_prefix = "eigen-3.4.0",
        urls = [
            "https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip",
        ],
    )

    maybe(
        http_archive,
        name = "com_google_absl_py",
        sha256 = "d82bb99b96efc726e5d516f6811045097666ea369bbe74f687f71bd3b9390a12",
        strip_prefix = "abseil-py-2.0.0",
        urls = [
            "https://github.com/abseil/abseil-py/archive/refs/tags/v2.0.0.zip",
        ],
    )

    maybe(
        http_archive,
        name = "com_google_absl",
        sha256 = "aa768256d0567f626334fcbe722f564c40b281518fc8423e2708a308e5f983ea",
        # Abseil LTS branch, Aug 2023, Patch 1
        strip_prefix = "abseil-cpp-fb3621f4f897824c0dbe0615fa94543df6192f30",
        urls = [
            "https://github.com/abseil/abseil-cpp/archive/fb3621f4f897824c0dbe0615fa94543df6192f30.zip",
        ],
    )

    # C++ rules for pybind11
    maybe(
        git_repository,
        name = "pybind11_abseil",
        commit = "2bf606ceddb0b7d874022defa8ea6d2d3e1605ad",  # May 24, 2023
        remote = "https://github.com/pybind/pybind11_abseil.git",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        shallow_since = "1684958620 -0700",
    )

    maybe(
        git_repository,
        name = "pybind11_bazel",
        commit = "b162c7c88a253e3f6b673df0c621aca27596ce6b",  # May 3, 2023
        remote = "https://github.com/pybind/pybind11_bazel.git",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        shallow_since = "1638580149 -0800",
    )

    maybe(
        git_repository,
        name = "pybind11_protobuf",
        commit = "5baa2dc9d93e3b608cde86dfa4b8c63aeab4ac78",  #  Jun 19, 2023
        remote = "https://github.com/pybind/pybind11_protobuf.git",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        shallow_since = "1687199891 -0700",
    )

    maybe(
        http_archive,
        name = "pybind11",
        build_file = "@pybind11_bazel//:pybind11.BUILD",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        sha256 = "b011a730c8845bfc265f0f81ee4e5e9e1d354df390836d2a25880e123d021f89",
        strip_prefix = "pybind11-2.11.1",
        urls = ["https://github.com/pybind/pybind11/archive/v2.11.1.zip"],  #  Jul 17, 2023
    )

    # Bazel skylib
    maybe(
        http_archive,
        name = "bazel_skylib",
        sha256 = "f7be3474d42aae265405a592bb7da8e171919d74c16f082a5457840f06054728",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.2.1/bazel-skylib-1.2.1.tar.gz",
            "https://github.com/bazelbuild/bazel-skylib/releases/download/1.2.1/bazel-skylib-1.2.1.tar.gz",
        ],
    )

    # Rules for building C/C++ projects using foreign build systems inside Bazel projects
    maybe(
        http_archive,
        name = "rules_foreign_cc",
        sha256 = "476303bd0f1b04cc311fc258f1708a5f6ef82d3091e53fd1977fa20383425a6a",
        strip_prefix = "rules_foreign_cc-0.10.1",
        url = "https://github.com/bazelbuild/rules_foreign_cc/releases/download/0.10.1/rules_foreign_cc-0.10.1.tar.gz",
    )
