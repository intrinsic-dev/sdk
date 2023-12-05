# Copyright 2023 Intrinsic Innovation LLC

"""Shared skill macros for use in other workspaces. """

load(
    "//intrinsic/skills/build_defs:skill.bzl",
    _cc_skill = "cc_skill",
    _py_skill = "py_skill",
    _py_skill_image = "py_skill_image",
    _skill_manifest = "skill_manifest",
)

cc_skill = _cc_skill
py_skill = _py_skill
py_skill_image = _py_skill_image
skill_manifest = _skill_manifest
