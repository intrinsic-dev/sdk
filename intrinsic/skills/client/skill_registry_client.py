# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrapper around the skill registry."""

from __future__ import annotations

from typing import List

from google.protobuf import empty_pb2
import grpc
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.skills.proto import skill_registry_pb2_grpc
from intrinsic.skills.proto import skills_pb2
from intrinsic.util.grpc import error_handling


class SkillRegistryClient:
  """Client library for the skill registry gRPC service."""

  def __init__(self, stub: skill_registry_pb2_grpc.SkillRegistryStub):
    """Constructs a new SkillRegistryClient object.

    Args:
      stub: The gRPC stub to be used for communication with the skill registry
        service.
    """
    self._stub: skill_registry_pb2_grpc.SkillRegistryStub = stub

  @classmethod
  def connect(cls, grpc_channel: grpc.Channel) -> SkillRegistryClient:
    """Connect to a running skill registry.

    Args:
      grpc_channel: Channel to the skill registry gRPC service.

    Returns:
      A newly created instance of the SkillRegistryClient class.
    """
    stub = skill_registry_pb2_grpc.SkillRegistryStub(grpc_channel)
    return cls(stub)

  @error_handling.retry_on_grpc_unavailable
  def get_skills(self) -> List[skills_pb2.Skill]:
    """Retrieves the list of skills.

    Returns:
      List of skill infos.
    """
    return self._stub.GetSkills(empty_pb2.Empty()).skills

  @error_handling.retry_on_grpc_unavailable
  def get_skill(self, skill_id: str) -> skills_pb2.Skill:
    """Retrieves a single skill.

    Args:
      skill_id: Fully-qualified id of the skill that should be retrieved.

    Returns:
      The requested skill.
    """
    return self._stub.GetSkill(
        skill_registry_pb2.GetSkillRequest(id=skill_id)
    ).skill
