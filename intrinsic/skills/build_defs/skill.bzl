# Copyright 2023 Intrinsic Innovation LLC

"""Build rules for creating Skill artifacts."""

load("@rules_python//python:defs.bzl", "py_binary")
load("//bazel:container.bzl", "container_image")
load("//bazel:python_oci_image.bzl", "python_oci_image")
load(
    "//intrinsic/skills/build_defs:manifest.bzl",
    "SkillManifestInfo",
    _skill_manifest = "skill_manifest",
)

skill_manifest = _skill_manifest

def _gen_cc_skill_service_main_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".cc")
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file
    deps_headers = []
    for dep in ctx.attr.deps:
        deps_headers += dep[CcInfo].compilation_context.direct_public_headers
    header_paths = [header.short_path for header in deps_headers]

    args = ctx.actions.args().add(
        "--manifest",
        manifest_pbbin_file,
    ).add(
        "--out",
        output_file,
    ).add_joined(
        "--cc_headers",
        header_paths,
        join_with = ",",
    ).add(
        "--lang",
        "cpp",
    )

    ctx.actions.run(
        outputs = [output_file],
        executable = ctx.executable._skill_service_gen,
        inputs = [manifest_pbbin_file],
        arguments = [args],
    )

    return [
        DefaultInfo(files = depset([output_file])),
    ]

_gen_cc_skill_service_main = rule(
    implementation = _gen_cc_skill_service_main_impl,
    doc = "Generates a file containing a main function for a skill's services.",
    attrs = {
        "manifest": attr.label(
            mandatory = True,
            providers = [SkillManifestInfo],
        ),
        "deps": attr.label_list(
            doc = "The cpp deps for the skill. This is normally the cc_proto_library target for the skill's schema, and the skill cc_library where skill interface is implemented.",
            providers = [CcInfo],
        ),
        "_skill_service_gen": attr.label(
            default = Label("//intrinsic/skills/generator:skill_service_generator"),
            doc = "The skill_service_generator executable to invoke for the code generation action.",
            executable = True,
            cfg = "exec",
        ),
    },
)

def _cc_skill_service(name, deps, manifest, **kwargs):
    """Generate a C++ binary that serves a single skill over gRPC.

    Args:
      name: The name of the target.
      deps: The C++ dependencies of the skill service specific to this skill.
            This is normally the cc_proto_library target for the skill's protobuf
            schema and the cc_library target that declares the skill's create method,
            which is specified in the skill's manifest.
      manifest: The manifest target for the skill. Must provide a SkillManifestInfo.
      **kwargs: Extra arguments passed to the cc_binary target for the skill service.
    """
    gen_main_name = "_%s_main" % name
    _gen_cc_skill_service_main(
        name = gen_main_name,
        manifest = manifest,
        deps = deps,
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    native.cc_binary(
        name = name,
        srcs = [gen_main_name],
        deps = deps + [
            Label("//intrinsic/skills/internal:runtime_data"),
            Label("//intrinsic/skills/internal:single_skill_factory"),
            Label("//intrinsic/skills/internal:skill_init"),
            Label("//intrinsic/skills/internal:skill_service_config_utils"),
            Label("//intrinsic/icon/release/portable:init_xfa_absl"),
            Label("//intrinsic/util/grpc"),
            Label("@com_google_absl//absl/flags:flag"),
            Label("@com_google_absl//absl/log:check"),
            Label("@com_google_absl//absl/time"),
            # This is needed when using grpc_cli.
            Label("@com_github_grpc_grpc//:grpc++_reflection"),
        ],
        **kwargs
    )

def _gen_py_skill_service_main_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".py")
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file

    args = ctx.actions.args().add(
        "--manifest",
        manifest_pbbin_file,
    ).add(
        "--out",
        output_file,
    ).add(
        "--lang",
        "python",
    )

    ctx.actions.run(
        outputs = [output_file],
        executable = ctx.executable._skill_service_gen,
        inputs = [manifest_pbbin_file],
        arguments = [args],
    )

    return [
        DefaultInfo(files = depset([output_file])),
    ]

_gen_py_skill_service_main = rule(
    implementation = _gen_py_skill_service_main_impl,
    doc = "Generates a file containing a main function for a skill's services.",
    attrs = {
        "manifest": attr.label(
            mandatory = True,
            providers = [SkillManifestInfo],
        ),
        "deps": attr.label_list(
            doc = "The python deps for the skill. This is normally the py_proto_library target for the skill's schema, and the skill py_library where skill interface is implemented.",
            providers = [PyInfo],
        ),
        "_skill_service_gen": attr.label(
            default = Label("//intrinsic/skills/generator:skill_service_generator"),
            doc = "The skill_service_generator executable to invoke for the code generation action.",
            executable = True,
            cfg = "exec",
        ),
    },
)

def _py_skill_service(name, deps, manifest, **kwargs):
    """Generate a Python binary that serves a single skill over gRPC.

    Args:
      name: The name of the target.
      deps: The Python dependencies of the skill service specific to this skill.
            This is normally the py_proto_library target for the skill's protobuf
            schema and the py_library target that declares the skill's create method.
      manifest: The manifest target for the skill. Must provide a SkillManifestInfo.
      **kwargs: Extra arguments passed to the py_binary target for the skill service.
    """
    gen_main_name = "_%s_main" % name
    _gen_py_skill_service_main(
        name = gen_main_name,
        manifest = manifest,
        deps = deps,
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    py_binary(
        name = name,
        srcs = [gen_main_name],
        main = gen_main_name + ".py",
        deps = deps + [
            Label("//intrinsic/skills/internal:runtime_data_py"),
            Label("//intrinsic/skills/internal:single_skill_factory_py"),
            Label("//intrinsic/skills/internal:skill_init_py"),
            Label("//intrinsic/skills/internal:skill_service_config_utils_py"),
            Label("//intrinsic/skills/generator:app"),
            Label("@com_google_absl_py//absl/flags"),
            Label("//intrinsic/skills/proto:skill_service_config_py_pb2"),
        ],
        **kwargs
    )

def _skill_service_config_manifest_impl(ctx):
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file
    proto_desc_fileset_file = ctx.attr.manifest[SkillManifestInfo].file_descriptor_set
    outputfile = ctx.actions.declare_file(ctx.label.name + ".pbbin")

    arguments = ctx.actions.args().add(
        "--manifest_pbbin_filename",
        manifest_pbbin_file,
    ).add(
        "--proto_descriptor_filename",
        proto_desc_fileset_file,
    ).add(
        "--output_config_filename",
        outputfile,
    )
    ctx.actions.run(
        outputs = [outputfile],
        executable = ctx.executable._skill_service_config_gen,
        inputs = [manifest_pbbin_file, proto_desc_fileset_file],
        arguments = [arguments],
    )

    return DefaultInfo(
        files = depset([outputfile]),
        runfiles = ctx.runfiles(files = [outputfile]),
    )

_skill_service_config_manifest = rule(
    implementation = _skill_service_config_manifest_impl,
    attrs = {
        "_skill_service_config_gen": attr.label(
            executable = True,
            default = Label("//intrinsic/skills/internal:skill_service_config_main"),
            cfg = "exec",
        ),
        "manifest": attr.label(
            mandatory = True,
            providers = [SkillManifestInfo],
        ),
    },
)

SkillIdInfo = provider(
    "Id for a skill",
    fields = {
        "id_filename": "The path to the file containing the skill ID.",
    },
)

def _skill_id_impl(ctx):
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file

    arguments = ctx.actions.args().add(
        "--manifest_pbbin_filename",
        manifest_pbbin_file,
    ).add(
        "--out_id_filename",
        ctx.outputs.id_filename,
    )

    ctx.actions.run(
        outputs = [ctx.outputs.id_filename],
        inputs = [manifest_pbbin_file],
        executable = ctx.executable._skill_id_gen,
        arguments = [arguments],
    )

    return SkillIdInfo(id_filename = ctx.outputs.id_filename)

_skill_id = rule(
    implementation = _skill_id_impl,
    attrs = {
        "_skill_id_gen": attr.label(
            default = Label("//intrinsic/skills/build_defs:gen_skill_id"),
            executable = True,
            cfg = "exec",
        ),
        "manifest": attr.label(
            mandatory = True,
            providers = [SkillManifestInfo],
        ),
        "id_filename": attr.output(
            mandatory = True,
            doc = "The path to the file containing the skill ID.",
        ),
    },
    provides = [SkillIdInfo],
)

def _skill_labels_impl(ctx):
    skill_id = ctx.attr.skill_id[SkillIdInfo]
    outputfile = ctx.actions.declare_file(ctx.label.name + ".labels")
    cmd = """
    echo "ai.intrinsic.asset-id=$(cat {id_filename})" > {output}""".format(
        id_filename = skill_id.id_filename.path,
        output = outputfile.path,
    )
    ctx.actions.run_shell(
        inputs = [skill_id.id_filename],
        outputs = [outputfile],
        command = cmd,
    )
    return DefaultInfo(files = depset([outputfile]))

_skill_labels = rule(
    implementation = _skill_labels_impl,
    attrs = {
        "skill_id": attr.label(
            mandatory = True,
            providers = [SkillIdInfo],
        ),
    },
)

SkillInfo = provider(
    "provided by intrinsic_skill() rule",
    fields = ["bundle_tar"],
)

def _intrinsic_skill_rule_impl(ctx):
    image_files = ctx.attr.image.files.to_list()
    if len(image_files) != 1:
        fail("image does not contain exactly 1 tar file")
    manifest = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file
    fds = ctx.attr.manifest[SkillManifestInfo].file_descriptor_set

    inputs = depset([manifest, fds], transitive = [ctx.attr.image.files])
    bundle_output = ctx.outputs.bundle_out

    args = ctx.actions.args().add(
        "--manifest",
        manifest,
    ).add(
        "--image_tar",
        image_files[0],
    ).add(
        "--file_descriptor_set",
        fds,
    ).add(
        "--output_bundle",
        bundle_output,
    )

    ctx.actions.run(
        inputs = inputs,
        outputs = [bundle_output],
        executable = ctx.executable._skillbundlegen,
        arguments = [args],
        mnemonic = "Skillbundle",
        progress_message = "Skill bundle %s" % bundle_output.short_path,
    )

    return [
        DefaultInfo(
            executable = bundle_output,
            runfiles = ctx.runfiles(
                transitive_files = inputs,
            ),
        ),
        SkillInfo(
            bundle_tar = bundle_output,
        ),
    ]

_intrinsic_skill_rule = rule(
    implementation = _intrinsic_skill_rule_impl,
    attrs = {
        "image": attr.label(
            mandatory = True,
            allow_single_file = [".tar"],
            doc = "The image tarball of the skill.",
        ),
        "manifest": attr.label(
            mandatory = True,
            providers = [SkillManifestInfo],
        ),
        "_skillbundlegen": attr.label(
            default = Label("//intrinsic/skills/build_defs:skillbundlegen"),
            cfg = "exec",
            executable = True,
        ),
    },
    outputs = {
        "bundle_out": "%{name}.bundle.tar",
    },
)

def _intrinsic_skill(name, image, manifest, **kwargs):
    """Creates cpp skill targets.

    Generates the following targets:
    * a skill container image target named 'name'.

    Args:
      name: The name of the skill to build
      image: Skill service image.
      manifest: A target that provides a SkillManifestInfo provider for the skill. This is normally
                a skill_manifest() target.
      **kwargs: additional arguments passed to the container_image rule, such as visibility.
    """
    skill_service_config_name = "_%s_skill_service_config" % name
    _skill_service_config_manifest(
        name = skill_service_config_name,
        manifest = manifest,
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    skill_id_name = "_%s_id" % name
    _skill_id(
        name = skill_id_name,
        manifest = manifest,
        id_filename = skill_id_name + ".id.txt",
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    labels = "_%s_labels" % name
    _skill_labels(
        name = labels,
        skill_id = skill_id_name,
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    image_name = "%s_image" % name
    package_path = native.package_name() + "/" if native.package_name() else ""
    container_image(
        name = image_name,
        base = image,
        directory = "/skills",
        files = [
            skill_service_config_name,
        ],
        data_path = "/",
        labels = labels,
        symlinks = {
            "/skills/skill_service_config.proto.bin": package_path + skill_service_config_name + ".pbbin",
        },
        **kwargs
    )

    _intrinsic_skill_rule(
        name = name,
        image = image_name + ".tar",
        manifest = manifest,
        visibility = kwargs.get("visibility"),
        testonly = kwargs.get("testonly"),
    )

def build_symlinks(skill_service_name):
    package_path = native.package_name() + "/" if native.package_name() else ""
    return {
        "/skills/skill_service": package_path + skill_service_name,
    }

def cc_skill(
        name,
        deps,
        manifest,
        **kwargs):
    """Creates cpp skill targets.

    Generates the following targets:
    * a skill container image target named 'name'.

    Args:
      name: The name of the skill to build
      deps: The C++ dependencies of the skill service specific to this skill.
            This is normally the cc_proto_library target for the skill's protobuf
            schema and the cc_library target that declares the skill's create method,
            which is specified in the skill's manifest.
      manifest: A target that provides a SkillManifestInfo provider for the skill. This is normally
                a skill_manifest() target.
      **kwargs: additional arguments passed to the container_image rule, such as visibility.
    """
    skill_service_name = "_%s_service" % name
    _cc_skill_service(
        name = skill_service_name,
        deps = deps,
        manifest = manifest,
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    service_image_name = "_%s_service_image" % name
    container_image(
        name = service_image_name,
        base = Label("@distroless_base"),
        directory = "/skills",
        files = [
            skill_service_name,
        ],
        data_path = "/",
        symlinks = build_symlinks(skill_service_name),
        compatible_with = kwargs.get("compatible_with"),
        visibility = ["//visibility:private"],
        testonly = kwargs.get("testonly"),
    )

    _intrinsic_skill(
        name = name,
        image = service_image_name,
        manifest = manifest,
        **kwargs
    )

def py_skill(
        name,
        manifest,
        deps,
        **kwargs):
    """Creates python skill targets.

    Generates the following targets:
    * a skill container image target named 'name'.

    Args:
      name: The name of the skill to build
      manifest: A target that provides a SkillManifestInfo provider for the skill. This is normally
                a skill_manifest() target.
      deps: The Python library dependencies of the skill. This is normally at least the python
            proto library for the skill and the skill implementation.
      **kwargs: additional arguments passed to the container_image rule, such as visibility.
    """
    binary_name = "_%s_binary" % name
    _py_skill_service(
        name = binary_name,
        deps = deps,
        manifest = manifest,
        python_version = "PY3",
        testonly = kwargs.get("testonly"),
        visibility = ["//visibility:private"],
        tags = ["manual", "avoid_dep"],
    )

    service_image_name = "_%s_service_image" % name
    python_oci_image(
        name = service_image_name,
        base = "@distroless_python3",
        binary = binary_name,
        directory = "/skills",
        data_path = "/",
        symlinks = build_symlinks(binary_name),
        workdir = "/",
        compatible_with = kwargs.get("compatible_with"),
        visibility = ["//visibility:private"],
        testonly = kwargs.get("testonly"),
    )

    _intrinsic_skill(
        name = name,
        image = service_image_name,
        manifest = manifest,
        **kwargs
    )
