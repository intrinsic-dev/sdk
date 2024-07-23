# Copyright 2023 Intrinsic Innovation LLC

"""Utils for working with the SkillServiceConfig proto."""

from absl import logging
from intrinsic.skills.proto import skill_service_config_pb2


def get_skill_service_config(
    filename: str,
) -> skill_service_config_pb2.SkillServiceConfig:
  """Returns the SkillServiceConfig at `skill_service_config_filename`.

  Reads the proto binary file at `skill_service_config_filename` and returns
  the contents. This file must contain a proto binary
  intrinsic_proto.skills.SkillServiceConfig message.

  Args:
    filename: the filename of the binary proto file

  Returns:
    A skill_service_config_pb2.SkillServiceConfig message
  """
  logging.info(
      "Reading skill configuration proto from: %s",
      filename,
  )
  service_config = skill_service_config_pb2.SkillServiceConfig()
  logging.info("\nImporting service_config from file.")
  with open(filename, "rb") as f:
    service_config.ParseFromString(f.read())
  logging.info("\nUsing skill configuration proto:\n%s", service_config)
  return service_config
