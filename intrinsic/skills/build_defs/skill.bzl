# Copyright 2023 Intrinsic Innovation LLC

"""Build rules for creating Skill artifacts."""

load("@rules_python//python:defs.bzl", "py_binary")
load(
    "//intrinsic/skills/build_defs:manifest.bzl",
    "SkillManifestInfo",
    _skill_manifest = "skill_manifest",
)
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")
load("@io_bazel_rules_docker//container:container.bzl", _container = "container")
load("@io_bazel_rules_docker//lang:image.bzl", "app_layer")
load("@bazel_skylib//lib:dicts.bzl", "dicts")

skill_manifest = _skill_manifest

# This is the container_pull (rules_docker) base image externally.
base_image = "@distroless_base_amd64//image"

def _gen_cc_skill_service_main_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".cc")
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file
    deps_headers = []
    for dep in ctx.attr.deps:
        deps_headers += dep[CcInfo].compilation_context.direct_public_headers
    header_paths = [header.short_path for header in deps_headers]

    args = ctx.actions.args().add(
        "--manifest",
        manifest_pbbin_file.path,
    ).add(
        "--out",
        output_file.path,
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
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    native.cc_binary(
        name = name,
        srcs = [gen_main_name],
        deps = deps + [
            Label("//intrinsic/skills/internal:runtime_data"),
            Label("//intrinsic/skills/internal:single_skill_factory"),
            Label("//intrinsic/skills/internal:skill_init"),
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
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    py_binary(
        name = name,
        srcs = [gen_main_name],
        main = gen_main_name + ".py",
        deps = deps + [
            Label("//intrinsic/skills/internal:runtime_data_py"),
            Label("//intrinsic/skills/internal:single_skill_factory_py"),
            Label("//intrinsic/skills/internal:skill_init_py"),
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
        manifest_pbbin_file.path,
    ).add(
        "--proto_descriptor_filename",
        proto_desc_fileset_file.path,
    ).add(
        "--output_config_filename",
        outputfile.path,
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

def _skill_id_impl(ctx):
    manifest_pbbin_file = ctx.attr.manifest[SkillManifestInfo].manifest_binary_file
    outputfile = ctx.actions.declare_file(ctx.label.name + ".pbbin")

    arguments = ctx.actions.args().add(
        "--manifest_pbbin_filename",
        manifest_pbbin_file.path,
    ).add(
        "--output_pbbin_filename",
        outputfile.path,
    )

    ctx.actions.run(
        outputs = [outputfile],
        inputs = [manifest_pbbin_file],
        executable = ctx.executable._skill_id_gen,
        arguments = [arguments],
    )

    return DefaultInfo(
        files = depset([outputfile]),
        runfiles = ctx.runfiles(files = [outputfile]),
    )

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
    },
)

def _skill_impl(ctx):
    skill_service_config_file = ctx.attr.skill_service_config[DefaultInfo].files.to_list()[0]
    skill_id_file = ctx.attr.skill_id[DefaultInfo].files.to_list()[0]
    skill_service_binary_file = ctx.executable.skill_service_binary
    image_name = ctx.attr.name

    files = [
        skill_service_config_file,
    ]
    if ctx.attr.include_binary_in_final_layer:
        files.append(skill_service_binary_file)

    symlinks = {
        "/skills/skill_service_config.proto.bin": skill_service_config_file.short_path,
        "/skills/skill_service": skill_service_binary_file.short_path,
    }

    labels = {
        "ai.intrinsic.skill-id": "@" + skill_id_file.path,
        "ai.intrinsic.skill-image-name": image_name,
    }

    return _container.image.implementation(
        ctx,
        compression_options = ["--fast"],
        experimental_tarball_format = "compressed",
        directory = "/skills",
        files = files,
        symlinks = symlinks,
        # container.image.implementation utilizes three related args for labels:
        # `labels`, `label_files`, and `label_file_strings`. For any label where
        # the value of the label will be the content of a file, the label value
        # must be the filepath pre-pended with `@`, and the file dependency must
        # be passed via `label_files`, furthermore the string file path must be
        # passing in `label_file_strings`. See _container.image.implementation()
        # for further documentation.
        labels = labels,
        label_files = [skill_id_file],
        label_file_strings = [skill_id_file.path],
    )

_skill = rule(
    implementation = _skill_impl,
    attrs = dicts.add(_container.image.attrs.items(), {
        "skill_service_binary": attr.label(
            executable = True,
            mandatory = True,
            cfg = "target",
        ),
        "skill_id": attr.label(
            mandatory = True,
        ),
        "skill_service_config": attr.label(
            mandatory = True,
        ),
        "include_binary_in_final_layer": attr.bool(
            doc = "If set to true, will copy the file specified by the 'skill_service_binary' attribute into the final layer. This is a mitigation for b/320446636.",
            mandatory = True,
        ),
    }.items()),
    executable = True,
    outputs = _container.image.outputs,
    toolchains = ["@io_bazel_rules_docker//toolchains/docker:toolchain_type"],
    cfg = _container.image.cfg,
)

def cc_skill(
        name,
        deps,
        manifest,
        proto = None,
        **kwargs):
    """Creates cpp skill targets.

    Generates the following targets:
    * a skill container image target named 'name'.
    * a proto_source_code_info_transitive_descriptor_set() target, with the 'image' suffix of the
      name replaced with 'filedescriptor'.

    Args:
      name: The name of the skill image to build, must end in "_image".
      deps: The C++ dependencies of the skill service specific to this skill.
            This is normally the cc_proto_library target for the skill's protobuf
            schema and the cc_library target that declares the skill's create method,
            which is specified in the skill's manifest.
      manifest: A target that provides a SkillManifestInfo provider for the skill. This is normally
                a skill_manifest() target.
      proto: (deprecated) The proto_library target that the skill uses to define
             its parameter type and return type.  This should be provided to the
             skill_manifest rule.  The proto argument will be removed soon.
      **kwargs: additional arguments passed to the container_image rule, such as visibility.
    """
    if not name.endswith("_image"):
        fail("cc_skill name must end in _image")

    # NB. Implemented using a macro that creates private targets because these
    # targets are an implementation detail of the image we generate, and
    # shouldn't be directly used by end-users. We should consider whether it
    # makes sense to implement this as a single rule when we implement the
    # corresponding python version of this and look into how we'll bundle data
    # needed for runtime + catalog. For now we consider the macro the public API
    # for this rule.
    if proto:
        proto_descriptor_name = "%s_filedescriptor" % name[:-6]
        proto_source_code_info_transitive_descriptor_set(
            name = proto_descriptor_name,
            deps = [proto],
            visibility = kwargs.get("visibility"),
            testonly = kwargs.get("testonly"),
            deprecation = """This file is generated by the skill_manifest rule.
            That target should be used instead.  This and the proto argument
            will be removed soon""",
        )
    skill_service_config_name = "_%s_skill_service_config" % name
    _skill_service_config_manifest(
        name = skill_service_config_name,
        manifest = manifest,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    skill_id_name = "_%s_id" % name
    _skill_id(
        name = skill_id_name,
        manifest = manifest,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    skill_service_name = "_%s_service" % name
    _cc_skill_service(
        name = skill_service_name,
        deps = deps,
        manifest = manifest,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    _skill(
        name = name,
        base = Label(base_image),
        skill_service_binary = skill_service_name,
        include_binary_in_final_layer = True,
        skill_service_config = skill_service_config_name,
        skill_id = skill_id_name,
        data_path = "/",  # NB. We set data_path here because there is no override for the container_image attr.
        **kwargs
    )

def py_skill(
        name,
        manifest,
        deps,
        proto = None,
        **kwargs):
    """Creates python skill targets.

    Generates the following targets:
    * a skill container image target named 'name'.
    * a proto_source_code_info_transitive_descriptor_set() target, with the 'image' suffix of the
      name replaced with 'filedescriptor'.

    Args:
      name: The name of the skill image to build, must end in "_image".
      manifest: A target that provides a SkillManifestInfo provider for the skill. This is normally
                a skill_manifest() target.
      deps: The Python library dependencies of the skill. This is normally at least the python
            proto library for the skill and the skill implementation.
      proto: (deprecated) The proto_library target that the skill uses to define
             its parameter type and return type.  This should be provided to the
             skill_manifest rule.  The proto argument will be removed soon.
      **kwargs: additional arguments passed to the container_image rule, such as visibility.
    """
    if not name.endswith("_image"):
        fail("py_skill name must end in _image")

    # NB. Implemented using a macro that creates private targets because these
    # targets are an implementation detail of the image we generate, and
    # shouldn't be directly used by end-users. We should consider whether it
    # makes sense to implement this as a single rule when we implement the
    # corresponding python version of this and look into how we'll bundle data
    # needed for runtime + catalog. For now we consider the macro the public API
    # for this rule.
    if proto:
        proto_descriptor_name = "%s_proto_descriptor_fileset" % name[:-6]
        proto_source_code_info_transitive_descriptor_set(
            name = proto_descriptor_name,
            deps = [proto],
            visibility = kwargs.get("visibility"),
            testonly = kwargs.get("testonly"),
            deprecation = """This file is generated by the skill_manifest rule.
            That target should be used instead.  This and the proto argument
            will be removed soon""",
        )
    skill_service_config_name = "_%s_skill_service_config" % name
    _skill_service_config_manifest(
        name = skill_service_config_name,
        manifest = manifest,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    skill_id_name = "_%s_id" % name
    _skill_id(
        name = skill_id_name,
        manifest = manifest,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    binary_name = "_%s_binary" % name
    _py_skill_service(
        name = binary_name,
        deps = deps,
        manifest = manifest,
        python_version = "PY3",
        exec_compatible_with = ["@io_bazel_rules_docker//platforms:run_in_container"],
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    skill_layer_name = "_%s_intrinsic_skill_layer" % name
    app_layer(
        name = skill_layer_name,
        base = Label("@py3_image_base//image"),
        entrypoint = ["/usr/bin/python"],
        binary = binary_name,
        data_path = "/",
        directory = "/skills",
        # The targets of the symlinks in the symlink layers are relative to the
        # workspace directory under the app directory. Thus, create an empty
        # workspace directory to ensure the symlinks are valid. See
        # https://github.com/bazelbuild/rules_docker/issues/161 for details.
        create_empty_workspace_dir = True,
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    _skill(
        name = name,
        base = skill_layer_name,
        skill_service_binary = binary_name,
        # In contrast to the C++ skill rule, we use the "skill_layer_name" app_layer as a base image
        # here. To prevent copying a (potentially) large binary twice into a container image, set
        # this attribute to false. See the detailed analysis in b/320446636.
        include_binary_in_final_layer = False,
        skill_service_config = skill_service_config_name,
        skill_id = skill_id_name,
        data_path = "/",  # NB. We set data_path here because there is no override for the container_image attr.
        **kwargs
    )
