# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.skills.python.skill_registry_client."""

from unittest import mock

from absl.testing import absltest
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.skills.proto import skills_pb2


class SkillRegistryTest(absltest.TestCase):
  """Tests all public methods of the SkillRegistry gRPC wrapper class."""

  def setUp(self):
    super().setUp()

    self._skill_registry_stub = mock.MagicMock()
    self._client = skill_registry_client.SkillRegistryClient(
        self._skill_registry_stub
    )

  def test_get_skills_works(self):
    self._skill_registry_stub.GetSkills.return_value = (
        skill_registry_pb2.GetSkillsResponse(
            skills=[
                skills_pb2.Skill(id='ai.intrinsic.throw_ball'),
                skills_pb2.Skill(id='ai.intrinsic.catch_ball'),
            ]
        )
    )

    result = self._client.get_skills()

    self.assertLen(result, 2)
    self.assertEqual(result[0].id, 'ai.intrinsic.throw_ball')
    self.assertEqual(result[1].id, 'ai.intrinsic.catch_ball')

  def test_get_skill_works(self):
    self._skill_registry_stub.GetSkill.return_value = (
        skill_registry_pb2.GetSkillResponse(
            skill=skills_pb2.Skill(id='ai.intrinsic.throw_ball')
        )
    )

    result = self._client.get_skill('ai.intrinsic.throw_ball')

    self.assertEqual(result.id, 'ai.intrinsic.throw_ball')
    self._skill_registry_stub.GetSkill.assert_called_once_with(
        skill_registry_pb2.GetSkillRequest(id='ai.intrinsic.throw_ball')
    )


if __name__ == '__main__':
  absltest.main()
