# Copyright 2023 Intrinsic Innovation LLC

"""Tests for skill_utils."""

from unittest import mock

from absl.testing import absltest
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import utils
from intrinsic.solutions import worlds
from intrinsic.solutions.internal import skill_utils
from intrinsic.solutions.testing import compare
from intrinsic.solutions.testing import test_skill_params_pb2
from intrinsic.world.proto import collision_settings_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_resources

_DEFAULT_TEST_MESSAGE = test_skill_params_pb2.TestMessage(
    my_double=2,
    my_float=-1,
    my_int32=5,
    my_int64=9,
    my_uint32=11,
    my_uint64=21,
    my_bool=False,
    my_string='bar',
    sub_message=test_skill_params_pb2.SubMessage(name='baz'),
    my_repeated_doubles=[-5, 10],
    repeated_submessages=[
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ],
    my_oneof_double=1.1,
    pose=math_proto_conversion.pose_to_proto(data_types.Pose3()),
)


class SkillUtilsTest(absltest.TestCase):

  def test_dict_from_proto(self):
    expected = {
        'my_double': (None, 2),
        'my_float': (None, -1),
        'my_int32': (None, 5),
        'my_int64': (None, 9),
        'my_uint32': (None, 11),
        'my_uint64': (None, 21),
        'my_bool': (None, False),
        'my_string': (None, "'bar'"),
        'sub_message': (
            'intrinsic_proto.test_data.SubMessage',
            {'name': (None, "'baz'")},
        ),
        'my_repeated_doubles': (None, [(None, -5), (None, 10)]),
        'repeated_submessages': (
            'intrinsic_proto.test_data.SubMessage',
            [
                (
                    'intrinsic_proto.test_data.SubMessage',
                    {'name': (None, "'foo'")},
                ),
                (
                    'intrinsic_proto.test_data.SubMessage',
                    {'name': (None, "'bar'")},
                ),
            ],
        ),
        'my_oneof_double': (None, 1.1),
        'pose': (
            'intrinsic_proto.Pose',
            {
                'position': ('intrinsic_proto.Point', {}),
                'orientation': (
                    'intrinsic_proto.Quaternion',
                    {'w': (None, 1.0)},
                ),
            },
        ),
    }
    test_params = _DEFAULT_TEST_MESSAGE
    self.assertEqual(skill_utils._dict_from_proto(test_params), expected)

  def test_pythonic_field_to_python_string(self):
    expected = {
        'my_double': '2.0',
        'my_float': '-1.0',
        'my_int32': '5',
        'my_int64': '9',
        'my_uint32': '11',
        'my_uint64': '21',
        'my_bool': 'False',
        'my_string': "'bar'",
        'sub_message': (
            'skills["test"].message_classes'
            '["intrinsic_proto.test_data.SubMessage"]'
            "(name='baz')"
        ),
        'optional_sub_message': 'skills["test"].message_classes["intrinsic_proto.test_data.SubMessage"]()',
        'my_repeated_doubles': '[-5.0, 10.0]',
        'my_oneof_double': '1.1',
        'enum_v': '0',
        'string_int32_map': '{}',
        'int32_string_map': '{}',
        'string_message_map': '{}',
        'repeated_submessages': (
            '[skills["test"].message_classes'
            '["intrinsic_proto.test_data.SubMessage"]'
            "(name='foo'), "
            'skills["test"].message_classes'
            '["intrinsic_proto.test_data.SubMessage"]'
            "(name='bar')]"
        ),
        'my_oneof_sub_message': (
            'skills["test"].message_classes'
            '["intrinsic_proto.test_data.SubMessage"]()'
        ),
        'pose': (
            'skills["test"].message_classes["intrinsic_proto.Pose"]'
            '(position=skills["test"].message_classes["intrinsic_proto.Point"](), '
            'orientation=skills["test"].message_classes["intrinsic_proto.Quaternion"]'
            '(w=1.0))'
        ),
        'my_required_int32': '0',
        'foo': 'skills["test"].message_classes["intrinsic_proto.test_data.TestMessage.Foo"]()',
        'executive_test_message': 'skills["test"].message_classes["intrinsic_proto.executive.TestMessage"]()',
        'non_unique_field_name': 'skills["test"].message_classes["intrinsic_proto.test_data.TestMessage.SomeType"]()',
    }
    parameter_defaults = _DEFAULT_TEST_MESSAGE
    for field in parameter_defaults.DESCRIPTOR.fields:
      python_repr = skill_utils.pythonic_field_to_python_string(
          getattr(parameter_defaults, field.name),
          field,
          utils.PrefixOptions(),
          'test',
      )
      self.assertEqual(expected[field.name], python_repr)
    self.assertEqual(len(expected), len(parameter_defaults.DESCRIPTOR.fields))

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
