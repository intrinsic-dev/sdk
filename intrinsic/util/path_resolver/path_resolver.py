# Copyright 2023 Intrinsic Innovation LLC

"""Generic resolver that will attempt to resolve runfiles or external directories if available."""

import os

from python.runfiles import runfiles


def resolve_runfiles_path(path: str) -> str:
  """Returns the runfiles path for the given path."""
  return os.path.normpath(
      runfiles.Create().Rlocation(os.path.join('ai_intrinsic_sdks', path))
  )
