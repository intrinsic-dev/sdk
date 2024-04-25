# Copyright 2023 Intrinsic Innovation LLC

"""Tests for skill_utils."""

from unittest import mock

from absl.testing import absltest
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.solutions import worlds
from intrinsic.solutions.internal import skill_utils
from intrinsic.solutions.testing import compare
from intrinsic.solutions.testing import test_skill_params_pb2
from intrinsic.world.proto import collision_settings_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_resources


class SkillUtilsTest(absltest.TestCase):

  def test_object_world_collision_seetings(self):
    skill_proto = test_skill_params_pb2.CollisionSettingsSkill()

    skill_utils.set_fields_in_msg(
        skill_proto,
        {
            'param_collision_settings': worlds.CollisionSettings(
                disable_collision_checking=True
            )
        },
    )

    compare.assertProto2Equal(
        self,
        skill_proto.param_collision_settings,
        collision_settings_pb2.CollisionSettings(
            disable_collision_checking=True
        ),
    )

  def test_joint_motion_target(self):
    skill_proto = test_skill_params_pb2.JointMotionTargetSkill()

    skill_utils.set_fields_in_msg(
        skill_proto,
        {
            'param_joint_motion_target': (
                object_world_resources.JointConfiguration(
                    joint_position=[1.0, 2.0, 3.0]
                )
            )
        },
    )

    compare.assertProto2Equal(
        self,
        skill_proto.param_joint_motion_target,
        joint_space_pb2.JointVec(joints=[1.0, 2.0, 3.0]),
    )

  def test_world_object_to_object_reference_by_name_smoke(self):
    skill_proto = test_skill_params_pb2.ObjectReferenceSkill()
    my_object = object_world_resources.WorldObject(
        object_world_service_pb2.Object(
            name='my_object',
            object_component=object_world_service_pb2.ObjectComponent(),
        ),
        mock.MagicMock(),
    )

    skill_utils.set_fields_in_msg(skill_proto, {'param_object': my_object})

  def test_frame_to_frame_reference_by_name_smoke(self):
    skill_proto = test_skill_params_pb2.ObjectReferenceSkill()
    my_frame = object_world_resources.Frame(
        object_world_service_pb2.Frame(name='my_frame'), mock.MagicMock()
    )

    skill_utils.set_fields_in_msg(skill_proto, {'param_frame': my_frame})


if __name__ == '__main__':
  absltest.main()
