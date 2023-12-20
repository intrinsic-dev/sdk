# Copyright 2023 Intrinsic Innovation LLC

"""Build rule for creating a Skill Manifest."""

load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "ProtoSourceCodeInfo", "gen_source_code_info_descriptor_set")

SkillManifestInfo = provider(
    "Info about a binary skill manifest",
    fields = {
        "manifest_binary_file": "The binary manifest File.",
    },
)

def _skill_manifest_impl(ctx):
    outputfile = ctx.actions.declare_file(ctx.label.name + ".pbbin")
    pbtxt = ctx.file.src

    transitive_descriptor_sets = depset(
        transitive = [
            dep[ProtoSourceCodeInfo].transitive_descriptor_sets
            for dep in ctx.attr.deps
        ],
    )

    args = ctx.actions.args().add(
        "--manifest",
        pbtxt,
    ).add(
        "--output",
        outputfile,
    ).add_joined(
        "--file_descriptor_sets",
        transitive_descriptor_sets,
        join_with = ",",
    )

    ctx.actions.run(
        outputs = [outputfile],
        inputs = depset([pbtxt], transitive = [transitive_descriptor_sets]),
        executable = ctx.executable._skillmanifestgen,
        arguments = [args],
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
            aspects = [gen_source_code_info_descriptor_set],
        ),
        "_skillmanifestgen": attr.label(
            default = Label("//intrinsic/skills/build_defs:skillmanifestgen"),
            executable = True,
            cfg = "exec",
        ),
    },
)
