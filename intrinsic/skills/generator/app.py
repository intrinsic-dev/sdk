# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""app wrapper for python.

NB. We need this to avoid copybara statements in our template file.
"""

from absl import app


def run(*args, **kwargs):
  app.run(*args, **kwargs)
