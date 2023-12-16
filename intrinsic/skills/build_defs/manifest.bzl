# Copyright 2023 Intrinsic Innovation LLC

"""Build rule for creating a Skill Manifest."""

load("@bazel_skylib//lib:new_sets.bzl", "sets")

SkillManifestInfo = provider(
    "Info about a binary skill manifest",
    fields = {
        "manifest_binary_file": "The binary manifest File.",
    },
)

def _skill_manifest_impl(ctx):
    outputfile = ctx.actions.declare_file(ctx.label.name + ".pbbin")
    pbtxt = ctx.file.src

    descriptor_set_set = sets.make()
    deps = ctx.attr.deps + [ctx.attr._skill_manifest_proto]
    for dep in deps:
        if ProtoInfo in dep:
            for descriptor_set in dep[ProtoInfo].transitive_descriptor_sets.to_list():
                sets.insert(descriptor_set_set, descriptor_set)
    descriptor_sets = sets.to_list(descriptor_set_set)

    ctx.actions.run(
        outputs = [outputfile],
        inputs = [pbtxt] + descriptor_sets,
        executable = ctx.executable._skillmanifestgen,
        arguments = [
            "-manifest=%s" % pbtxt.path,
            "-output=%s" % outputfile.path,
            "-file_descriptor_sets=%s" % ",".join([file.path for file in descriptor_sets]),
        ],
        mnemonic = "SkillManifest",
    )

    return [
        DefaultInfo(
            files = depset([outputfile]),
            runfiles = ctx.runfiles([outputfile]),
        ),
        SkillManifestInfo(
            manifest_binary_file = outputfile,
        ),
    ]

skill_manifest = rule(
    doc = """Compiles a binary proto message for the given intrinsic_proto.skills.Manifest textproto
           and writes it to file.
           
           Example:
            skill_manifest(
              name = "foo_manifest",
              src = ["foo_manifest.textproto"],
              deps = [":foo_proto"],
            )

            creates the file foo_manifest.pbbin.
            
           Provides SkillManifestInfo.
           """,
    implementation = _skill_manifest_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            doc = "textproto specifying an intrinsic_proto.skills.Manifest",
        ),
        "deps": attr.label_list(
            doc = "proto deps of the manifest textproto for this skill. " +
                  "This is normally the proto message declaring the skill's return type and parameter " +
                  "type messages.",
            providers = [ProtoInfo],
        ),
        "_skillmanifestgen": attr.label(
            default = Label("//intrinsic/skills/build_defs:skillmanifestgen"),
            executable = True,
            cfg = "exec",
        ),
        "_skill_manifest_proto": attr.label(
            default = Label("//intrinsic/skills/proto:skill_manifest_proto"),
            doc = "the skill manifest proto schema",
        ),
    },
)
