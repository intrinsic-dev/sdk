# Copyright 2023 Intrinsic Innovation LLC

"""
Blaze rules for service types.
"""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")

ServiceTypeInfo = provider(
    "provided by intrinsic_service() rule",
    fields = ["bundle_tar"],
)

def _intrinsic_service_impl(ctx):
    bundle_output = ctx.outputs.bundle_out

    inputs = []
    transitive_inputs = []
    runfiles = []
    transitive_runfiles = []

    image_tars = []
    basenames = {}
    for target in ctx.attr.images:
        transitive_inputs.extend([target.files])
        transitive_runfiles.extend([target.files])
        if len(target.files.to_list()) > 1:
            fail("Image targets must have exactly one file")
        file = target.files.to_list()[0]
        image_tars.append(file.path)
        if file.basename in basenames:
            # This is a requirement based on how we place the files into the tar
            # archive.  The files are placed into the root of the tar file
            # currently, so having ones with the same base name would cause them
            # to conflict or potentially silently overwrite.
            fail("Basenames of images must be unique; got multiple {}".format(file.basename))
        basenames[file.basename] = None

    transitive_descriptor_sets = depset(transitive = [
        f[ProtoInfo].transitive_descriptor_sets
        for f in ctx.attr.deps
    ])
    transitive_inputs.append(transitive_descriptor_sets)

    inputs.append(ctx.file.manifest)

    args = ctx.actions.args().add(
        "--manifest",
        ctx.file.manifest,
    ).add(
        "--output_bundle",
        bundle_output,
    ).add_joined(
        "--image_tars",
        image_tars,
        join_with = ",",
    ).add_joined(
        "--file_descriptor_sets",
        transitive_descriptor_sets,
        join_with = ",",
    )
    if ctx.file.default_config:
        inputs.append(ctx.file.default_config)
        args.add("--default_config", ctx.file.default_config.path)

    ctx.actions.run(
        inputs = depset(inputs, transitive = transitive_inputs),
        outputs = [bundle_output],
        executable = ctx.executable._servicegen,
        arguments = [args],
        mnemonic = "Servicebundle",
        progress_message = "Service bundle %s" % bundle_output.short_path,
    )

    return [
        DefaultInfo(
            executable = bundle_output,
            runfiles = ctx.runfiles(
                transitive_files = depset(runfiles, transitive = transitive_runfiles),
            ),
        ),
        ServiceTypeInfo(
            bundle_tar = bundle_output,
        ),
    ]

intrinsic_service = rule(
    implementation = _intrinsic_service_impl,
    attrs = {
        "default_config": attr.label(
            allow_single_file = [".pbtxt", ".textproto"],
        ),
        "images": attr.label_list(
            allow_empty = True,
            allow_files = [".tar"],
            doc = "Image tarballs referenced by the service type.",
        ),
        "manifest": attr.label(
            allow_single_file = [".textproto"],
            mandatory = True,
            doc = (
                "A manifest that can be used to provide the service definition and metadata."
            ),
        ),
        "deps": attr.label_list(
            providers = [ProtoInfo],
        ),
        "_servicegen": attr.label(
            default = Label("//intrinsic/assets/services/build_defs:servicegen_main"),
            cfg = "exec",
            executable = True,
        ),
    },
    outputs = {
        "bundle_out": "%{name}.bundle.tar",
    },
)
