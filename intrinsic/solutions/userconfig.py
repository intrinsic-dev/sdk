# Copyright 2023 Intrinsic Innovation LLC

"""Provides methods to handle user configuration files."""

import json
import os
import platform
from typing import Dict

_CONFIG_FOLDER = "intrinsic"
_CONFIG_FILE = "user.config"

SELECTED_SOLUTION_TYPE = "selectedSolutionType"
SELECTED_PROJECT = "selectedProject"
SELECTED_SOLUTION = "selectedSolution"

# Allowed values for SELECTED_SOLUTION_TYPE
SELECTED_SOLUTION_TYPE_LOCAL = "local"
SELECTED_SOLUTION_TYPE_REMOTE = "remote"


def get_user_config_dir() -> str:
  """Returns the users config directory.

  Depends on the underlying OS (e.g. $HOME/.config) for Linux.

  TODO(bschimke): Add Windows and Mac support once required.

  Raises:
    NotImplementedError: if OS is unknown
    RuntimeError: if required env variables are missing.
  """
  if platform.system() != "Linux":
    raise NotImplementedError(f"OS '{platform.system()}' is not supported!")

  home_dir = os.environ.get("XDG_CONFIG_HOME") or os.environ.get("HOME")
  if not home_dir:
    raise RuntimeError("Neither $XDG_CONFIG_HOME nor $HOME are defined!")

  return os.path.join(home_dir, ".config")


def read() -> Dict[str, str]:
  """Returns the user config.

  Used to persist configuration across sessions, tools etc.

  Raises:
    ValueError: if config not found
  """
  env_path = os.path.join(get_user_config_dir(), _CONFIG_FOLDER, _CONFIG_FILE)
  try:
    with open(env_path, "r") as env_file:
      return json.load(env_file)
  except FileNotFoundError as e:
    raise ValueError(f"User config file ({env_path}) not found!") from e
