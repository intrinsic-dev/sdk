# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/skills/build_defs:skill.bzl", "cc_skill", "py_skill", "skill_manifest")

package(
    default_testonly = True,
    default_visibility = ["//visibility:private"],
)

skill_manifest(
    name = "no_op_skill_cc_manifest",
    src = "no_op_skill_manifest_cc.textproto",
    # Allow use of this image in tests of skill tooling.
    visibility = ["//intrinsic/skills:__subpackages__"],
    deps = ["//intrinsic/skills/testing:no_op_skill_proto"],
)

cc_skill(
    name = "no_op_skill_cc",
    manifest = ":no_op_skill_cc_manifest",
    # Allow use of this image in tests of asset and skill tooling.
    visibility = [
        "//intrinsic/assets:__subpackages__",
        "//intrinsic/skills:__subpackages__",
    ],
    deps = [
        "//intrinsic/skills/testing:no_op_skill_cc",
        "//intrinsic/skills/testing:no_op_skill_cc_proto",
    ],
)

skill_manifest(
    name = "no_op_skill_py_manifest",
    src = "no_op_skill_manifest_py.textproto",
    visibility = ["//intrinsic/skills:__subpackages__"],
    deps = ["//intrinsic/skills/testing:no_op_skill_proto"],
)

py_skill(
    name = "no_op_skill_py_new",
    manifest = ":no_op_skill_py_manifest",
    # Allow use of this image in tests of skill tooling.
    deps = [
        "//intrinsic/skills/testing:no_op_skill_py",
        "//intrinsic/skills/testing:no_op_skill_py_pb2",
    ],
)
