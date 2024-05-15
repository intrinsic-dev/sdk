# Copyright 2023 Intrinsic Innovation LLC

"""Tests for skill_utils."""

from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions.internal import skill_parameters
from intrinsic.solutions.testing import skill_test_utils
from intrinsic.solutions.testing import test_skill_params_pb2

_MESSAGE_WITHOUT_DEFAULTS = test_skill_params_pb2.TestMessage()
_MESSAGE_WITH_DEFAULT_VALUES = test_skill_params_pb2.TestMessage(
    enum_v=test_skill_params_pb2.TestMessage.THREE,
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
    int32_string_map={1: 'foo'},
    non_unique_field_name=test_skill_params_pb2.TestMessage.SomeType(),
)


class SkillParametersTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()

    self._utils = skill_test_utils.SkillTestUtils(
        'testing/test_skill_params_proto_descriptors_transitive_set_sci.proto.bin'
    )

  @parameterized.named_parameters(
      (
          'test_required_field_of_default_message',
          _MESSAGE_WITHOUT_DEFAULTS,
          [
              'sub_message',
              'string_int32_map',
              'int32_string_map',
              'string_message_map',
              'pose',
              'my_required_int32',
              'my_repeated_doubles',
              'repeated_submessages',
              'executive_test_message',
              'non_unique_field_name',
          ],
      ),
      (
          'test_required_field_of_message_with_use_params',
          _MESSAGE_WITH_DEFAULT_VALUES,
          [
              'enum_v',
              'my_double',
              'my_float',
              'my_int32',
              'my_int64',
              'my_uint32',
              'my_uint64',
              'my_bool',
              'my_string',
              'sub_message',
              'string_int32_map',
              'int32_string_map',
              'string_message_map',
              'pose',
              'my_required_int32',
              'my_repeated_doubles',
              'repeated_submessages',
              'executive_test_message',
              'non_unique_field_name',
          ],
      ),
  )
  def test_required_fields(self, test_message, expected_required_fields):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill', parameter_defaults=test_message
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=test_message,
        parameter_description=skill_info.parameter_description,
    )

    self.assertCountEqual(
        skill_params.get_required_field_names(), expected_required_fields
    )

  @parameterized.named_parameters(
      ('double_default', 'my_double'),
      ('float_default', 'my_float'),
      ('int32_default', 'my_int32'),
      ('int64_default', 'my_int64'),
      ('uint32_default', 'my_uint32'),
      ('bool_default', 'my_bool'),
      ('string_default', 'my_string'),
      ('oneof_default', 'my_oneof_double'),
  )
  def test_field_with_defaults(self, field_with_default):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_MESSAGE_WITH_DEFAULT_VALUES,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=_MESSAGE_WITH_DEFAULT_VALUES,
        parameter_description=skill_info.parameter_description,
    )

    self.assertTrue(skill_params.has_default_value(field_with_default))

  @parameterized.named_parameters(
      ('non_opt', 'sub_message'),
      ('non_opt_built_in', 'sub_message'),
      ('no_default', 'optional_sub_message'),
  )
  def test_field_without_defaults(self, field_without_default):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_MESSAGE_WITH_DEFAULT_VALUES,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=_MESSAGE_WITH_DEFAULT_VALUES,
        parameter_description=skill_info.parameter_description,
    )
    self.assertFalse(skill_params.has_default_value(field_without_default))

  def test_is_optional_with_default_raises(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_MESSAGE_WITH_DEFAULT_VALUES,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=_MESSAGE_WITH_DEFAULT_VALUES,
        parameter_description=skill_info.parameter_description,
    )
    with self.assertRaises(NameError):
      skill_params.has_default_value('n/a')

  @parameterized.named_parameters(
      ('my_double_is_missing_in_test_message', 'my_double'),
      ('my_string_missing_in_test_message', 'my_string'),
  )
  def test_missing_fields(self, field_name):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_MESSAGE_WITH_DEFAULT_VALUES,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=_MESSAGE_WITH_DEFAULT_VALUES,
        parameter_description=skill_info.parameter_description,
    )

    self.assertFalse(
        skill_params.message_has_optional_field(
            field_name, _MESSAGE_WITHOUT_DEFAULTS
        )
    )

  @parameterized.named_parameters(
      ('my_double_exists', 'my_double', _MESSAGE_WITH_DEFAULT_VALUES),
      ('my_string_exists', 'my_string', _MESSAGE_WITH_DEFAULT_VALUES),
      ('non_optional_existing', 'sub_message', _MESSAGE_WITH_DEFAULT_VALUES),
      ('non_optional_missing', 'sub_message', _MESSAGE_WITHOUT_DEFAULTS),
  )
  def test_existing_fields(self, field_name, test_message):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_MESSAGE_WITH_DEFAULT_VALUES,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=_MESSAGE_WITH_DEFAULT_VALUES,
        parameter_description=skill_info.parameter_description,
    )

    self.assertTrue(
        skill_params.message_has_optional_field(field_name, test_message)
    )


if __name__ == '__main__':
  absltest.main()
