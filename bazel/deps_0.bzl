# Copyright 2023 Intrinsic Innovation LLC

"""Workspace dependencies needed for the Intrinsic SDKs as a 3rd-party consumer (part 0)."""

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
        sha256 = "80a98277ad1311dacd837f9b16db62887702e9f1d1c4c9f796d0121a46c8e184",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.46.0/rules_go-v0.46.0.zip",
            "https://github.com/bazelbuild/rules_go/releases/download/v0.46.0/rules_go-v0.46.0.zip",
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
        url = "https://github.com/bazel-contrib/toolchains_llvm/releases/download/0.10.3/toolchains_llvm-0.10.3.tar.gz",
    )

    # Python rules, toolchain and pip dependencies
    maybe(
        http_archive,
        name = "rules_python",
        strip_prefix = "rules_python-0.31.0",
        url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.31.0.zip",
        sha256 = "9110e83a233c9edce177241f3ae95eae4e4cc3b602d845878d76ad4e3bab7c60",
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
            "https://mirror.bazel.build/github.com/bazelbuild/rules_pkg/releases/download/0.9.1/rules_pkg-0.9.1.tar.gz",
            "https://github.com/bazelbuild/rules_pkg/releases/download/0.9.1/rules_pkg-0.9.1.tar.gz",
        ],
        sha256 = "8f9ee2dc10c1ae514ee599a8b42ed99fa262b757058f65ad3c384289ff70c4b8",
    )

    maybe(
        http_archive,
        name = "aspect_bazel_lib",
        sha256 = "357dad9d212327c35d9244190ef010aad315e73ffa1bed1a29e20c372f9ca346",
        strip_prefix = "bazel-lib-2.7.0",
        url = "https://github.com/aspect-build/bazel-lib/releases/download/v2.7.0/bazel-lib-v2.7.0.tar.gz",
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
        http_archive,
        name = "com_googlesource_code_re2",
        sha256 = "47c5b6f31745cb0507dd6a4e8ed1d531ba871d0d8fc9f359c16386615018c2c0",
        strip_prefix = "re2-" + RE2_COMMIT,
        urls = ["https://github.com/google/re2/archive/" + RE2_COMMIT + ".tar.gz"],
    )

    # Another alias for RE2
    maybe(
        http_archive,
        name = "com_github_google_re2",
        sha256 = "47c5b6f31745cb0507dd6a4e8ed1d531ba871d0d8fc9f359c16386615018c2c0",
        strip_prefix = "re2-" + RE2_COMMIT,
        urls = ["https://github.com/google/re2/archive/" + RE2_COMMIT + ".tar.gz"],
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
        sha256 = "8ad598c73ad796e0d8280b082cebd82a630d73e73cd3c70057938a6501bba5d7",
        strip_prefix = "googletest-1.14.0",
        urls = ["https://github.com/google/googletest/archive/refs/tags/v1.14.0.tar.gz"],
    )

    # Google benchmark.
    maybe(
        http_archive,
        name = "com_github_google_benchmark",
        sha256 = "6bc180a57d23d4d9515519f92b0c83d61b05b5bab188961f36ac7b06b0d9e9ce",
        strip_prefix = "benchmark-1.8.3",
        urls = ["https://github.com/google/benchmark/archive/refs/tags/v1.8.3.tar.gz"],
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
            "https://mirror.bazel.build/github.com/bazelbuild/rules_cc/releases/download/0.0.9/rules_cc-0.0.9.tar.gz",
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
        sha256 = "0fb3a4916a157eb48124ef309231cecdfdd96ff54adf1660b39c0d4a9790a2c0",
        strip_prefix = "abseil-py-1.4.0",
        urls = [
            "https://github.com/abseil/abseil-py/archive/refs/tags/v1.4.0.tar.gz",
        ],
    )

    maybe(
        http_archive,
        name = "com_google_absl",
        sha256 = "59d2976af9d6ecf001a81a35749a6e551a335b949d34918cfade07737b9d93c5",
        strip_prefix = "abseil-cpp-20230802.0",
        urls = [
            "https://github.com/abseil/abseil-cpp/archive/refs/tags/20230802.0.tar.gz",
        ],
    )

    # C++ rules for pybind11
    maybe(
        http_archive,
        name = "pybind11_abseil",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        sha256 = "1496b112e86416e2dcf288569a3e7b64f3537f0b18132224f492266e9ff76c44",
        strip_prefix = "pybind11_abseil-202402.0",
        urls = ["https://github.com/pybind/pybind11_abseil/archive/refs/tags/v202402.0.tar.gz"],
    )

    maybe(
        http_archive,
        name = "pybind11_bazel",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        sha256 = "e2ba5f81f3bf6a3fc0417448d49389cc7950bebe48c42c33dfeb4dd59859b9a4",
        strip_prefix = "pybind11_bazel-2.11.1.bzl.2",
        urls = ["https://github.com/pybind/pybind11_bazel/archive/refs/tags/v2.11.1.bzl.2.tar.gz"],
    )

    maybe(
        http_archive,
        name = "pybind11_protobuf",
        repo_mapping = {"@local_config_python": "@local_config_python"},
        sha256 = "abf2d5704d9fb2c5e66e6333667bf5f92aaaac74c05d704a84a7478d91dc6663",
        strip_prefix = "pybind11_protobuf-5baa2dc9d93e3b608cde86dfa4b8c63aeab4ac78",
        urls = ["https://github.com/pybind/pybind11_protobuf/archive/5baa2dc9d93e3b608cde86dfa4b8c63aeab4ac78.tar.gz"],  #  Jun 19, 2023
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
        sha256 = "cd55a062e763b9349921f0f5db8c3933288dc8ba4f76dd9416aac68acee3cb94",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.5.0/bazel-skylib-1.5.0.tar.gz",
            "https://github.com/bazelbuild/bazel-skylib/releases/download/1.5.0/bazel-skylib-1.5.0.tar.gz",
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
