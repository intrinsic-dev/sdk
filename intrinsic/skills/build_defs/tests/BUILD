# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/skills/build_defs:skill.bzl", "cc_skill", "cc_skill_image", "py_skill", "skill_manifest")

package(
    default_testonly = True,
    default_visibility = ["//visibility:private"],
)

cc_skill_image(
    name = "no_op_skill_image",
    package_name = "ai.intrinsic",
    parameter_proto = "//intrinsic/skills/testing:no_op_skill_proto",
    skill = "//intrinsic/skills/testing:no_op_skill",
    skill_name = "no_op",
    # Allow use of this image in lint tests of templates.
    visibility = ["//intrinsic/skills/templates:__subpackages__"],
)

skill_manifest(
    name = "no_op_skill_cc_manifest",
    src = "no_op_skill_manifest_cc.textproto",
    deps = ["//intrinsic/skills/testing:no_op_skill_proto"],
)

cc_skill(
    name = "no_op_skill_cc_new_image",
    manifest = ":no_op_skill_cc_manifest",
    proto = "//intrinsic/skills/testing:no_op_skill_proto",
    # Allow use of this image in tests of skill tooling.
    deps = [
        "//intrinsic/skills/testing:no_op_skill",
        "//intrinsic/skills/testing:no_op_skill_cc_proto",
    ],
)

skill_manifest(
    name = "no_op_skill_py_manifest",
    src = "no_op_skill_manifest_py.textproto",
    deps = ["//intrinsic/skills/testing:no_op_skill_proto"],
)

py_skill(
    name = "no_op_skill_py_new_image",
    manifest = ":no_op_skill_py_manifest",
    proto = "//intrinsic/skills/testing:no_op_skill_proto",
    # Allow use of this image in tests of skill tooling.
    deps = [
        "//intrinsic/skills/testing:no_op_skill_py",
        "//intrinsic/skills/testing:no_op_skill_py_pb2",
    ],
)
