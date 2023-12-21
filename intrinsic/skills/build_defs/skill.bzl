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
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("//bazel:python_oci_image.bzl", "python_oci_image")

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

def _add_file_descriptors(name, kind, deps, files, symlinks):
    proto_descriptor_set_name = "%s_%s_descriptors" % (name, kind)
    proto_source_code_info_transitive_descriptor_set(
        name = proto_descriptor_set_name,
        deps = deps,
    )
    descriptors_path = "%s_%s" % (
        paths.join(native.package_name(), proto_descriptor_set_name),
        "transitive_set_sci.proto.bin",
    )
    files.append(":%s" % proto_descriptor_set_name)
    actual_path = "../google3/" + descriptors_path
    symlink_file_location = "/skills/%s_descriptors.proto.bin" % kind
    symlinks[symlink_file_location] = actual_path
    return symlink_file_location

def _invoke_config_impl(ctx):
    config_output_file = ctx.actions.declare_file(ctx.label.name + ".proto.bin")

    arguments = ctx.actions.args()
    arguments.add(
        "--skill_name",
        ctx.attr.skill_name,
    )
    arguments.add(
        "--parameter_descriptor_filename",
        ctx.attr.parameter_descriptor_filename,
    )
    arguments.add(
        "--return_value_descriptor_filename",
        ctx.attr.return_value_descriptor_filename,
    )

    if ctx.attr.skill_module:
        arguments.add(
            "--python_skill_modules",
            ctx.attr.skill_module,
        )
    arguments.add(
        "--output_config_filename",
        config_output_file.path,
    )
    ctx.actions.run(
        outputs = [config_output_file],
        executable = ctx.executable.config_binary,
        arguments = [arguments],
    )

    return DefaultInfo(
        files = depset([config_output_file]),
        runfiles = ctx.runfiles(files = [
            config_output_file,
        ]),
    )

_invoke_config = rule(
    implementation = _invoke_config_impl,
    attrs = {
        "config_binary": attr.label(
            mandatory = True,
            executable = True,
            cfg = "exec",
        ),
        "skill_name": attr.string(
            mandatory = True,
        ),
        "parameter_descriptor_filename": attr.string(
            mandatory = True,
        ),
        "return_value_descriptor_filename": attr.string(
            mandatory = True,
        ),
        "skill_module": attr.string(
            mandatory = False,
        ),
    },
)

def _skill_service_config(
        name,
        skill_name,
        parameter_descriptor_filename,
        return_value_descriptor_filename,
        skill_module,
        files,
        symlinks):
    _invoke_config(
        name = name,
        skill_name = skill_name,
        config_binary = Label("//intrinsic/skills/internal:skill_service_config_main"),
        parameter_descriptor_filename = parameter_descriptor_filename,
        return_value_descriptor_filename = return_value_descriptor_filename,
        skill_module = skill_module,
    )
    config_path = "%s.proto.bin" % paths.join(native.package_name(), name)
    files.append(":%s" % name)
    symlink_path = "../google3/" + config_path
    symlinks["skills/skill_service_config.proto.bin"] = symlink_path

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
        skill_service_binary_file,
    ]

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
        skill_service_config = skill_service_config_name,
        skill_id = skill_id_name,
        data_path = "/",  # NB. We set data_path here because there is no override for the container_image attr.
        **kwargs
    )

def py_skill_service(name, deps, data = None, **kwargs):
    """Generate a Python binary that serves skills over gRPC.

    Args:
      name: Name of the target.
      deps: Skills to be served by the binary. List of `py_library`
        or `py_library` targets.
      data: Any additional data needed by the binary. Optional.
    """

    # Copy the service source to a local directory to prevent build warnings.
    service_filename = name + "_main.py"
    service_copy_name = paths.join(native.package_name(), service_filename)
    native.genrule(
        name = name + "_main",
        srcs = [Label("//intrinsic/skills/internal:module_skill_service_main.py")],
        outs = [service_copy_name],
        cmd = "cp $< $@",
        visibility = ["//visibility:private"],
        tags = ["manual"],
    )

    py_binary(
        name = name,
        main = service_copy_name,
        srcs = [service_copy_name],
        python_version = "PY3",
        srcs_version = "PY3",
        data = data,
        deps = [
            Label("//intrinsic/skills/internal:module_skill_service"),
            Label("@com_google_absl_py//absl:app"),
        ] + deps,
        **kwargs
    )

def _py3_skill_binary_image(name, deps, data = None, base = None):
    """Generate a Python binary that serves skills over gRPC.

    Args:
      name: Name of the target.
      deps: Skills to be served by the binary. List of `py_library`
        or `py_library` targets.
      data: Any additional data needed by the binary. Optional.
      base: Base image to use. If none, uses a default.
    """

    # Copy the service source to a local directory to prevent build warnings.
    entrypoint = paths.join(native.package_name(), name + "_main")
    service_filename = entrypoint + ".py"
    native.genrule(
        name = name + "_gen_main",
        srcs = [Label("//intrinsic/skills/internal:module_skill_service_main.py")],
        outs = [service_filename],
        cmd = "cp $< $@",
    )

    py_binary(
        name = name + "_main",
        srcs = [service_filename],
        srcs_version = "PY3",
        data = data,
        deps = [
            Label("//intrinsic/skills/internal:module_skill_service"),
            "@com_google_absl_py//absl:app",
        ] + deps,
    )

    if not base:
        base = "@distroless_python3"

    python_oci_image(
        name = name,
        base = base,
        binary = name + "_main",
        entrypoint = ["python3", entrypoint],
    )

def py_skill_image(
        name,
        skill,
        skill_name,
        package_name,
        skill_module,
        parameter_proto,
        return_value_proto = None,
        base_image = None,
        **kwargs):
    """Generates a Skill image.

   The skill_name and package_name are used to form a unique identifier for the skill. The skill's
   id, as presented in the skill registry and catalog, is of the form:
   '<package_name>.<skill_name>'.
   Where you see a version-ed id, it is of the form: '<package_name>.<skill_name>.<version>'.

    Args:
     name: The name of the skill image to build, must end in "_image".
     skill: The Python library that defines the skill to generate an image for.
     skill_name: The name of the skill. This should match the skill name given
       by the implementation.
     package_name: The name of the package for the skill
     skill_module: The python module containing the skill.
     parameter_proto: The proto_library dep that the Skill uses for its
       parameters.
     return_value_proto: The proto_library dep that the Skill uses for its
       return value.
     base_image: The base image to use for the oci_image 'base'.
     **kwargs: additional arguments passed to the oci_image target, such
       as visibility or tags.
    """
    if not name.endswith("_image"):
        fail("py_skill_image name must end in _image")

    # replace 'image' suffix with 'service'
    skill_service_name = "%sservice" % name[:-5]

    _py3_skill_binary_image(
        name = skill_service_name,
        deps = [
            skill,
        ],
        base = base_image,
    )

    skill_image = ":%s.tar" % skill_service_name
    files = []
    symlinks = {}

    parameter_path = _add_file_descriptors(name, "parameter", [parameter_proto], files, symlinks)
    return_value_path = _add_file_descriptors(
        name,
        "return",
        [return_value_proto] if return_value_proto else [],
        files,
        symlinks,
    )

    service_config_name = "%sservice_config" % name[:-5]

    _skill_service_config(
        name = service_config_name,
        skill_name = skill_name,
        parameter_descriptor_filename = parameter_path,
        return_value_descriptor_filename = return_value_path,
        skill_module = skill_module,
        files = files,
        symlinks = symlinks,
    )

    pkg_tar(
        name = name + "_files_layer",
        srcs = files,
        package_dir = "/google3",
        strip_prefix = "/",
        compressor_args = "--fast",
    )

    pkg_tar(
        name = name + "_symlinks_layer",
        strip_prefix = "/",
        compressor_args = "--fast",
        symlinks = symlinks,
    )

    oci_image(
        name = name,
        base = skill_image,
        tars = [
            name + "_files_layer",
            name + "_symlinks_layer",
        ],
        labels = {
            "ai.intrinsic.skill-name": skill_name,
            "ai.intrinsic.skill-image-name": name,
            "ai.intrinsic.package-name": package_name,
        },
        **kwargs
    )

    oci_tarball(
        name = name + ".tar",
        image = name,
        repo_tags = ["%s/%s:latest" % (native.package_name(), name)],
        **kwargs
    )
