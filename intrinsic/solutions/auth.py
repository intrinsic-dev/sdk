# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides methods to handle API keys for authentication.

This file implements a subset of the
`//intrinsic/tools/inctl/auth/auth.go` authorization library.
The implementation only contains methods to read the keys in Python.
Login etc. is handled by the inctl CLI.
"""

import dataclasses
import datetime
import json
import os.path
from typing import Dict, Optional, Tuple
from intrinsic.solutions import userconfig
ALIAS_DEFAULT_TOKEN = "default"
AUTH_CONFIG_EXTENSION = ".user-token"
STORE_DIRECTORY = "intrinsic/projects"


@dataclasses.dataclass()
class ProjectToken:
  """Contains an API key and corresponding helpers."""

  api_key: str
  valid_until: Optional[datetime.datetime] = None

  def validate(self) -> None:
    if self.valid_until is not None:
      if datetime.datetime.now() > self.valid_until:
        raise AttributeError(f"project token expired: {self.valid_until}")

  def get_request_metadata(self) -> Tuple[Tuple[str, str], ...]:
    self.validate()
    return (("authorization", "Bearer " + self.api_key),)


@dataclasses.dataclass()
class ProjectConfiguration:
  """Contains a list of API keys for a given project."""

  name: str
  tokens: Dict[str, ProjectToken]

  def has_credentials(self, alias: str) -> bool:
    return alias in self.tokens

  def get_credentials(self, alias: str) -> ProjectToken:
    if not self.has_credentials(alias):
      raise KeyError(f"token with alias '{alias}' not found")

    return self.tokens[alias]

  def get_default_credentials(self) -> ProjectToken:
    return self.get_credentials(ALIAS_DEFAULT_TOKEN)


class CredentialsNotFoundError(ValueError):
  """Thrown in case the lookup for a given credential name failed.

  Attributes:
    message: the error message
    project_name: GCP project name for which the credentials were not found.
  """

  def __init__(self, message: str, project_name: str) -> None:
    super().__init__(message)
    self.project_name = project_name

  def __str__(self) -> str:
    return f"Credentials for project '{self.project_name}' could not be found!"


def get_configuration(name: str) -> ProjectConfiguration:
  """Reads the local project configuration for the provided project name.

  Args:
    name: name of the GCP project

  Raises:
    CredentialsNotFoundError: if configuration for the project could not be
    found.

  Returns:
    configuration for the project.
  """
  file_name = os.path.join(
      userconfig.get_user_config_dir(),
      STORE_DIRECTORY,
      name + AUTH_CONFIG_EXTENSION,
  )

  try:
    with open(file_name, "r") as f:
      config = json.load(f)
      tokens = {}
      for alias, token in config["tokens"].items():
        tokens[alias] = ProjectToken(
            api_key=token["apiKey"],
            valid_until=(
                datetime.datetime.fromisoformat(token["validUntil"])
                if "validUntil" in token
                else None
            ),
        )
      return ProjectConfiguration(name=name, tokens=tokens)
  except FileNotFoundError as e:
    raise CredentialsNotFoundError(message=e.strerror, project_name=name) from e
