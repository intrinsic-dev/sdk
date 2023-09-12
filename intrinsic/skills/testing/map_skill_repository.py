# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Implementation of SkillRepository to store skills in a map."""

import threading
from typing import Callable, Dict, List

from intrinsic.assets import id_utils
from intrinsic.skills.internal import runtime_data as rd
from intrinsic.skills.internal import single_skill_factory as skill_factory
from intrinsic.skills.internal import skill_repository as repo
from intrinsic.skills.python import skill_interface as skl
from intrinsic.util.decorators import overrides


class MapSkillRepository(repo.SkillRepository):
  """Implementation of SkillRepository to store skills in a map."""

  def __init__(self):
    self._lock = threading.Lock()
    self._skill_factories: Dict[str, skill_factory.SingleSkillFactory] = {}

  @overrides(repo.SkillRepository)
  def get_skill(self, skill_alias: str) -> skl.Skill:
    """Returns a new skill instance.

    Args:
      skill_alias: The skill alias.

    Raises:
      InvalidSkillAliasError: If the skill does not exist in the repository.
    """
    try:
      factory = self._skill_factories[skill_alias]
    except KeyError as err:
      raise repo.InvalidSkillAliasError(
          f'Skill with alias [{skill_alias}]" not found in the repository'
      ) from err

    return factory.get_skill(skill_alias)

  @overrides(repo.SkillRepository)
  def get_skill_execute(self, skill_alias: str) -> skl.SkillExecuteInterface:
    """Returns a new skill execute instance.

    Args:
      skill_alias: The skill's alias.

    Raises:
      SkillNotFoundError if the skill is not found in the repository.
    """
    try:
      factory = self._skill_factories[skill_alias]
    except KeyError as err:
      raise repo.InvalidSkillAliasError(
          f'Skill with alias [{skill_alias}]" not found in the repository'
      ) from err

    return factory.get_skill_execute(skill_alias)

  @overrides(repo.SkillRepository)
  def get_skill_project(self, skill_alias: str) -> skl.SkillProjectInterface:
    """Returns a new skill project instance.

    Args:
      skill_alias: The skill's alias.

    Raises:
      SkillNotFoundError if the skill is not found in the repository.
    """
    try:
      factory = self._skill_factories[skill_alias]
    except KeyError as err:
      raise repo.InvalidSkillAliasError(
          f'Skill with alias [{skill_alias}]" not found in the repository'
      ) from err

    return factory.get_skill_project(skill_alias)

  @overrides(repo.SkillRepository)
  def get_skill_runtime_data(self, skill_alias: str) -> rd.SkillRuntimeData:
    """Returns runtime data for the skill.

    Args:
      skill_alias: The skill's alias.

    Raises:
      SkillNotFoundError if the skill is not found in the repository.
    """
    try:
      factory = self._skill_factories[skill_alias]
    except KeyError as err:
      raise repo.InvalidSkillAliasError(
          f'Skill with alias [{skill_alias}]" not found in the repository'
      ) from err

    return factory.get_skill_runtime_data(skill_alias)

  @overrides(repo.SkillRepository)
  def get_skill_aliases(self) -> List[str]:
    """Returns the list of aliases of all registered skills."""
    with self._lock:
      return self._skill_factories.keys()
  def insert_or_assign_skill(
      self, skill_alias: str, create_skill: Callable[[], skl.Skill]
  ) -> None:
    """Adds a single skill to the repository.

    If a skill with that alias has been registered before it will be
    overwritten.

    Args:
      skill_alias: The skill's alias.
      create_skill: The function to create a skill instance.
    """
    with self._lock:
      self._skill_factories[skill_alias] = skill_factory.SingleSkillFactory(
          rd.get_runtime_data_from_signature(create_skill()), create_skill
      )

  def insert_or_assign_skill_runtime_data(
      self,
      skill_runtime_data: rd.SkillRuntimeData,
      create_skill: Callable[[], skl.Skill],
  ) -> None:
    """Adds a single skill to the repository.

    If a skill with that alias has been registered before it will be
    overwritten.

    Args:
      skill_runtime_data: The skill runtime data.
      create_skill: The function to create a skill instance.
    """
    with self._lock:
      self._skill_factories[id_utils.name_from(skill_runtime_data.skill_id)] = (
          skill_factory.SingleSkillFactory(skill_runtime_data, create_skill)
      )
