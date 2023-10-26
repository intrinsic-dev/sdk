# Copyright 2023 Intrinsic Innovation LLC

"""Utility functions for skills related proto conversions."""

import re
from typing import List, Optional

from absl import logging
from google.protobuf import descriptor_pb2
from intrinsic.assets import id_utils
from intrinsic.skills.proto import skill_manifest_pb2
from intrinsic.skills.proto import skill_registry_config_pb2
from intrinsic.skills.proto import skills_pb2
import intrinsic.skills.python.skill_interface as skl
from intrinsic.util.proto import descriptors
from intrinsic.util.proto import source_code_info_view_py
from pybind11_abseil import status


# This is the recommended regex for semver. It is copied from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
_SEMVER_REGEX_PATTERN: str = (
    r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)


def proto_from_skill(
    skill: skl.Skill, version: Optional[str] = None
) -> skills_pb2.Skill:
  """Create Skill descriptor proto from skill implementation.

  Args:
    skill: Skill to create descriptor proto for.
    version: The version of the skill. If unspecified, id_version will equal id.
      Must be in semver format.

  Returns:
    Skill descriptor proto.

  Raises:
    ValueError if version is not a valid semver version.
  """
  proto = skills_pb2.Skill()
  proto.skill_name = skill.name()
  proto.id = skill.package() + '.' + skill.name()
  proto.id_version = proto.id
  if version is not None:
    pattern = re.compile(_SEMVER_REGEX_PATTERN)
    if re.fullmatch(pattern, version) is None:
      raise ValueError(f'version: {version} is not valid semver')
    else:
      proto.id_version += '.' + version

  if skill.__doc__ is not None:
    proto.doc_string = skill.__doc__.rstrip()

  for key, val in skill.required_equipment().items():
    proto.resource_selectors[key].CopyFrom(val)

  proto.parameter_description.parameter_descriptor_fileset.CopyFrom(
      descriptors.gen_file_descriptor_set(skill.get_parameter_descriptor())
  )
  proto.parameter_description.parameter_message_full_name = (
      skill.get_parameter_descriptor().full_name
  )
  if skill.default_parameters() is not None:
    proto.parameter_description.default_value.Pack(skill.default_parameters())

  return_value_descriptor = skill.get_return_value_descriptor()
  if return_value_descriptor is not None:
    proto.return_value_description.descriptor_fileset.CopyFrom(
        descriptors.gen_file_descriptor_set(return_value_descriptor)
    )
    proto.return_value_description.return_value_message_full_name = (
        return_value_descriptor.full_name
    )

  return proto


def proto_from_skill_manifest(
    manifest: skill_manifest_pb2.Manifest,
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    version: str,
) -> skills_pb2.Skill:
  """Create Skill descriptor proto from skill manifest.

  Equivalent to intrinsic/skills/internal/skill_proto_utils.h;l=60-63

  Args:
    manifest: Skill to create descriptor proto for.
    file_descriptor_set: File descriptor set.
    version: The version of the skill. Must be in semver format.

  Returns:
    Skill descriptor proto.

  Raises:
    ValueError if version is not a valid semver version.
  """
  skill = skills_pb2.Skill(
      skill_name=manifest.id.name,
      id=id_utils.id_from(manifest.id.package, manifest.id.name),
      package_name=manifest.id.package,
      doc_string=manifest.documentation.doc_string,
      id_version=id_utils.id_version_from(
          manifest.id.package, manifest.id.name, version
      ),
  )

  for key, val in manifest.dependencies.required_equipment.items():
    skill.resource_selectors[key].CopyFrom(val)

  add_file_descriptor_set_without_source_code_from_manifest(
      manifest, file_descriptor_set, skill
  )

  skill.execution_options.supports_cancellation = (
      manifest.options.supports_cancellation
  )

  if manifest.HasField('parameter'):
    if manifest.parameter.HasField('default_value'):
      skill.parameter_description.default_value.CopyFrom(
          manifest.parameter.default_value
      )

  return skill


def proto_from_skill_registration(
    skill: skl.Skill,
    project_handle: str,
    execute_handle: str,
    skill_info_handle: str,
) -> skill_registry_config_pb2.SkillRegistration:
  """Generates a single skill registration proto using the given handles.

  Args:
    skill: A skill.
    project_handle: string for projecting.
    execute_handle: string for execution.
    skill_info_handle: string for skill information.

  Returns:
    proto of type SkillRegistration.
  """

  proto = skill_registry_config_pb2.SkillRegistration()
  proto.skill.CopyFrom(proto_from_skill(skill))
  proto.project_handle.grpc_target = project_handle
  proto.execute_handle.grpc_target = execute_handle
  if skill_info_handle:
    proto.skill_info_handle.grpc_target = skill_info_handle
  return proto


def proto_from_skill_registry_config(
    skills: List[skl.Skill],
    project_handle: str,
    execute_handle: str,
    skill_info_handle: str,
) -> skill_registry_config_pb2.SkillRegistryConfig:
  """Converts a list of skills and their common handle fields to proto.

  Args:
    skills: A list of skill.
    project_handle: string for projecting.
    execute_handle: string for execution.
    skill_info_handle: string for skill information.

  Returns:
    proto of type SkillRegistryConfig.
  """
  proto = skill_registry_config_pb2.SkillRegistryConfig()
  for skill in skills:
    skill_proto = proto.skills.add()
    skill_proto.CopyFrom(
        proto_from_skill_registration(
            skill, project_handle, execute_handle, skill_info_handle
        )
    )
  return proto


def add_file_descriptor_set_without_source_code_from_manifest(
    manifest: skill_manifest_pb2.Manifest,
    parameter_file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    skill_proto: skills_pb2.Skill,
):
  """Adds (or overwrites) the skill's parameter descriptor fileset.

  This also populates the parameter field comments. We remove source_code_info
  as it is no longer needed after the parameter field comments are populated.

  Args:
    manifest: A skill manifest
    parameter_file_descriptor_set: A file descriptor set for the skill's
      parameters.
    skill_proto: A skill proto to which this function will add file descriptors.
  """
  parameter_description = skill_proto.parameter_description
  parameter_description.parameter_descriptor_fileset.CopyFrom(
      parameter_file_descriptor_set
  )
  parameter_description.parameter_message_full_name = (
      manifest.parameter.message_full_name
  )
  sci_view = source_code_info_view_py.SourceCodeInfoView()
  sci_view.Init(parameter_description.parameter_descriptor_fileset)
  parameter_description.parameter_field_comments.update(
      sci_view.GetNestedFieldCommentMap(
          parameter_description.parameter_message_full_name
      )
  )

  for file in parameter_description.parameter_descriptor_fileset.file:
    file.ClearField('source_code_info')

  _add_pub_topic_description_from_manifest(
      manifest, parameter_file_descriptor_set, skill_proto
  )


def add_file_descriptor_set_without_source_code_info(
    skill: skl.Skill,
    parameter_file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    skill_proto: skills_pb2.Skill,
):
  """Adds (or overwrites) the skill's parameter descriptor fileset.

  This also populates the parameter field comments. We remove source_code_info
  as it is no longer needed after the parameter field comments are populated.

  Args:
    skill: A skill.
    parameter_file_descriptor_set: A file descriptor set for the skill's
      parameters.
    skill_proto: A skill proto.

  Returns:
    Skill proto with file descriptors.
  """
  parameter_description = skill_proto.parameter_description
  parameter_description.parameter_descriptor_fileset.CopyFrom(
      parameter_file_descriptor_set
  )
  sci_view = source_code_info_view_py.SourceCodeInfoView()
  sci_view.Init(parameter_description.parameter_descriptor_fileset)
  parameter_description.parameter_field_comments.update(
      sci_view.GetNestedFieldCommentMap(
          parameter_description.parameter_message_full_name
      )
  )
  for file in parameter_description.parameter_descriptor_fileset.file:
    file.ClearField('source_code_info')
