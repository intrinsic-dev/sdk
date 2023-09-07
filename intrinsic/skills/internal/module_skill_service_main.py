# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Binary to run Project and Execute skill services.

Initializes a server with SkillProjectorServicer and SkillExecutorServicer
servicers. Skills provided by these servicers are from a given module.
"""

from absl import app
from intrinsic.skills.internal import module_skill_service

if __name__ == '__main__':
  app.run(module_skill_service.main)
