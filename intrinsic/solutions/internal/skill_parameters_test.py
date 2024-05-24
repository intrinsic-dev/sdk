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
    optional_sub_message=test_skill_params_pb2.SubMessage(name='quz'),
    my_repeated_doubles=[-5, 10],
    repeated_submessages=[
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ],
    my_required_int32=42,
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
          'primitive_field',
          'my_required_int32',
          _MESSAGE_WITHOUT_DEFAULTS,
          False,
      ),
      (
          'optional_primitive_field',
          'my_double',
          _MESSAGE_WITHOUT_DEFAULTS,
          True,
      ),
      (
          'primitive_field_with_default_value',
          'my_required_int32',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
      (
          'optional_primitive_field_with_default_value',
          'my_double',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
      (
          'message_field',
          'sub_message',
          _MESSAGE_WITHOUT_DEFAULTS,
          False,
      ),
      (
          'optional_message_field',
          'optional_sub_message',
          _MESSAGE_WITHOUT_DEFAULTS,
          True,
      ),
      (
          'message_field_with_default_value',
          'sub_message',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
      (
          'optional_message_field_with_default_value',
          'optional_sub_message',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
      (
          'oneof_field',
          'my_oneof_double',
          _MESSAGE_WITHOUT_DEFAULTS,
          True,
      ),
      (
          'oneof_field_with_default_value',
          'my_oneof_double',
          _MESSAGE_WITH_DEFAULT_VALUES,
          True,
      ),
      (
          'repeated_field',
          'my_repeated_doubles',
          _MESSAGE_WITHOUT_DEFAULTS,
          False,
      ),
      (
          'repeated_field_with_default_value',
          'my_repeated_doubles',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
      (
          'map_field',
          'int32_string_map',
          _MESSAGE_WITHOUT_DEFAULTS,
          False,
      ),
      (
          'map_field_with_default_value',
          'int32_string_map',
          _MESSAGE_WITH_DEFAULT_VALUES,
          False,
      ),
  )
  def test_is_optional_in_python_signature(
      self, field_name, test_message, expected_result
  ):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_message,
    )
    skill_params = skill_parameters.SkillParameters(
        default_message=test_message,
        parameter_description=skill_info.parameter_description,
    )

    self.assertEqual(
        skill_params.is_optional_in_python_signature(field_name),
        expected_result,
    )


if __name__ == '__main__':
  absltest.main()
