# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.executive.workcell.public.workcell."""

import datetime
import enum
import inspect
import textwrap
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2
from google.protobuf import empty_pb2
from google.protobuf import text_format
from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.executive.proto import test_message_pb2
from intrinsic.math.proto import point_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.proto import quaternion_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import cel
from intrinsic.solutions import provided
from intrinsic.solutions.internal import skill_generation
from intrinsic.solutions.internal import skill_providing
from intrinsic.solutions.internal import skill_utils
from intrinsic.solutions.testing import compare
from intrinsic.solutions.testing import skill_test_utils
from intrinsic.solutions.testing import test_skill_params_pb2


_SKILL_PARAMETER_DICT = {
    'my_double': 2.2,
    'my_float': -1.1,
    'my_int32': -5,
    'my_int64': -9,
    'my_uint32': 11,
    'my_uint64': 21,
    'my_bool': False,
    'my_string': 'bar',
    'sub_message': test_skill_params_pb2.SubMessage(name='baz'),
    'my_repeated_doubles': [-5.0, 10.0],
    'repeated_submessages': [
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ],
    'my_oneof_double': 1.1,
    'pose': data_types.Pose3.from_vec7([4, 5, 6, 0, 1, 0, 0]),
}

_DEFAULT_TEST_MESSAGE = test_skill_params_pb2.TestMessage(
    my_double=2.5,
    my_float=-1.5,
    my_int32=5,
    my_int64=9,
    my_uint32=11,
    my_uint64=21,
    my_bool=False,
    my_string='bar',
    sub_message=test_skill_params_pb2.SubMessage(name='baz'),
    optional_sub_message=test_skill_params_pb2.SubMessage(name='quz'),
    my_repeated_doubles=[-5.5, 10.5],
    repeated_submessages=[
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ],
    my_required_int32=42,
    my_oneof_double=1.5,
    pose=pose_pb2.Pose(
        position=point_pb2.Point(),
        orientation=quaternion_pb2.Quaternion(x=0.5, y=0.5, z=0.5, w=0.5),
    ),
    foo=test_skill_params_pb2.TestMessage.Foo(
        bar=test_skill_params_pb2.TestMessage.Foo.Bar(test='test')
    ),
    enum_v=test_skill_params_pb2.TestMessage.THREE,
    string_int32_map={'foo': 1},
    int32_string_map={3: 'foobar'},
    string_message_map={
        'bar': test_skill_params_pb2.TestMessage.MessageMapValue(value='baz')
    },
    executive_test_message=test_message_pb2.TestMessage(int32_value=123),
    non_unique_field_name=test_skill_params_pb2.TestMessage.SomeType(
        non_unique_field_name=test_skill_params_pb2.TestMessage.AnotherType()
    ),
)


def _create_skill_registry_with_mock_stub():
  skill_registry_stub = mock.MagicMock()
  skill_registry = skill_registry_client.SkillRegistryClient(
      skill_registry_stub
  )

  return (skill_registry, skill_registry_stub)


class SkillsTest(parameterized.TestCase):
  """Tests public methods of the skills wrapper class."""

  def setUp(self):
    super().setUp()

    self._utils = skill_test_utils.SkillTestUtils(
        'testing/test_skill_params_proto_descriptors_transitive_set_sci.proto.bin'
    )

  def assertSignature(self, actual, expected):
    actual = str(actual)
    # Insert newlines after commas, else the diff printed by assertEqual is
    # unreadable. We don't need to assert on newlines in the signature exactly.
    actual_with_newlines = actual.replace(',', ',\n')
    expected_with_newlines = expected.replace(',', ',\n')
    self.assertEqual(
        actual_with_newlines,
        expected_with_newlines,
        # In case of failure print code for updating the test. Not a great
        # solution, but our signatures can be very long and this can save
        # **a lot** of time when making signature changes.
        'Signature not as expected. If you made changes and want to update the '
        "test expectation you can use the following code:\n\n'"
        + actual.replace('\n', '\\n').replace(', ', ", '\n'")
        + "'\n\nSignature not as expected. Diff with inserted newlines:\n\n",
    )

  @parameterized.parameters(
      {'parameter': {'my_double': 2}},
      {'parameter': {'my_float': 1}},
      {'parameter': {'my_int32': 1.0}},
      {'parameter': {'my_int64': 2.0}},
      {'parameter': {'my_uint32': 1.1}},
      {'parameter': {'my_uint64': 2.1}},
      {'parameter': {'my_bool': 'foo'}},
      {'parameter': {'my_string': -1}},
      {'parameter': {'sub_message': data_types.Pose3()}},
      {'parameter': {'pose': test_skill_params_pb2.SubMessage()}},
      {'parameter': {'my_repeated_doubles': 0.0}},
      {
          'parameter': {
              'my_repeated_doubles': [test_skill_params_pb2.SubMessage()]
          }
      },
      {'parameter': {'my_repeated_doubles': [data_types.Pose3()]}},
      {'parameter': {'my_repeated_doubles': [True, False]}},
      {'parameter': {'my_repeated_doubles': [1.0, False]}},
      {'parameter': {'repeated_submessages': [1.0, False]}},
      {
          'parameter': {
              'repeated_submessages': [data_types.Pose3(), data_types.Pose3()]
          }
      },
      {'parameter': {'repeated_submessages': {'foo': 1}}},
      {'parameter': {'my_double': [1, 2]}},
  )
  def test_gen_skill_param_message_type_mismatch(self, parameter):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )
    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            'my_skill', parameter_defaults=_DEFAULT_TEST_MESSAGE
        )
    )

    skills = skill_providing.Skills(
        skill_registry, self._utils.create_empty_resource_registry()
    )

    with self.assertRaises(TypeError):
      skills.my_skill(**parameter)

  def test_list_skills(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.intr_skill_one'),
        self._utils.create_parameterless_skill_info('ai.intr.intr_skill_two'),
        self._utils.create_parameterless_skill_info('ai.ai_skill'),
        self._utils.create_parameterless_skill_info('foo.foo_skill'),
        self._utils.create_parameterless_skill_info('foo.foo'),
        self._utils.create_parameterless_skill_info('foo.bar.bar_skill'),
        self._utils.create_parameterless_skill_info('foo.bar.bar'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    self.assertEqual(
        dir(skills),
        [
            'ai',
            'ai_skill',
            'bar',
            'bar_skill',
            'foo',
            'foo_skill',
            'global_skill',
            'intr_skill_one',
            'intr_skill_two',
        ],
    )
    self.assertEqual(dir(skills.ai), ['ai_skill', 'intr'])
    self.assertEqual(dir(skills.foo), ['bar', 'foo', 'foo_skill'])
    self.assertEqual(dir(skills.foo.bar), ['bar', 'bar_skill'])

  def test_skills_attribute_access(self):
    """Tests attribute-based access (skills.<skill_id>)."""
    ai_intr_intr_skill_two = self._utils.create_parameterless_skill_info(
        'ai.intr.intr_skill_two'
    )
    # Some skill protos may only have the skill id but not the skill_name or
    # package_name set.
    ai_intr_intr_skill_two.skill_name = ''
    ai_intr_intr_skill_two.package_name = ''
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.intr_skill_one'),
        ai_intr_intr_skill_two,
        self._utils.create_parameterless_skill_info('ai.ai_skill'),
        self._utils.create_parameterless_skill_info('foo.foo_skill'),
        self._utils.create_parameterless_skill_info('foo.foo'),
        self._utils.create_parameterless_skill_info('foo.bar.bar_skill'),
        self._utils.create_parameterless_skill_info('foo.bar.bar'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    # Shortcut notation: skills.<skill_name>
    self.assertIsInstance(
        skills.intr_skill_one(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(
        skills.intr_skill_two(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(skills.ai_skill(), skill_generation.GeneratedSkill)
    self.assertIsInstance(skills.foo_skill(), skill_generation.GeneratedSkill)

    # Id notation: skills.<skill_id>
    self.assertIsInstance(skills.ai, provided.SkillPackage)
    self.assertIsInstance(skills.ai.intr, provided.SkillPackage)
    self.assertIsInstance(skills.foo, provided.SkillPackage)
    self.assertIsInstance(skills.foo.bar, provided.SkillPackage)

    self.assertIsInstance(
        skills.ai.intr.intr_skill_one(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(
        skills.ai.intr.intr_skill_two(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(skills.ai.ai_skill(), skill_generation.GeneratedSkill)
    self.assertIsInstance(
        skills.foo.foo_skill(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(skills.foo.foo(), skill_generation.GeneratedSkill)
    self.assertIsInstance(
        skills.foo.bar.bar_skill(), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(skills.foo.bar.bar(), skill_generation.GeneratedSkill)
    self.assertIsInstance(
        skills.global_skill(), skill_generation.GeneratedSkill
    )

    with self.assertRaises(AttributeError):
      _ = skills.skill5

    with self.assertRaises(AttributeError):
      _ = skills.foo.skill5

  def test_skills_dict_access(self):
    """Tests id-string-based access via __getitem__ (skills['<skill_id>'])."""
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.skill_one'),
        self._utils.create_parameterless_skill_info('ai.intr.skill_two'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    self.assertIsInstance(
        skills['ai.intr.skill_one'](), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(
        skills['ai.intr.skill_two'](), skill_generation.GeneratedSkill
    )
    self.assertIsInstance(
        skills['global_skill'](), skill_generation.GeneratedSkill
    )

    with self.assertRaises(KeyError):
      _ = skills['skill5']

  def test_skills_get_skill_ids(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.skill_one'),
        self._utils.create_parameterless_skill_info('ai.intr.skill_two'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    skill_ids = skills.get_skill_ids()

    self.assertCountEqual(
        list(skill_ids),
        ['ai.intr.skill_one', 'ai.intr.skill_two', 'global_skill'],
    )

  def test_skills_get_skill_classes(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.skill_one'),
        self._utils.create_parameterless_skill_info('ai.intr.skill_two'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    skill_classes = skills.get_skill_classes()

    self.assertLen(skill_classes, 3)
    for skill_class in skill_classes:
      self.assertIsInstance(skill_class(), skill_generation.GeneratedSkill)

  def test_skills_get_skill_ids_and_classes(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intr.skill_one'),
        self._utils.create_parameterless_skill_info('ai.intr.skill_two'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    ids_and_classes = skills.get_skill_ids_and_classes()

    self.assertCountEqual(
        [skill_id for skill_id, _ in ids_and_classes],
        ['ai.intr.skill_one', 'ai.intr.skill_two', 'global_skill'],
    )
    for _, skill_class in ids_and_classes:
      self.assertIsInstance(skill_class(), skill_generation.GeneratedSkill)

  def test_gen_skill(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    # No default parameters
    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    expected_repeated_doubles = [2.1, 3.1]
    expected_repeated_submessages = [
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ]

    parameters = test_skill_params_pb2.TestMessage(
        my_double=1.1,
        my_float=2.0,
        my_int32=1,
        my_int64=2,
        my_string='foo',
        my_uint32=10,
        my_uint64=20,
        my_bool=True,
        sub_message=test_skill_params_pb2.SubMessage(name='bar'),
        pose=math_proto_conversion.pose_to_proto(data_types.Pose3()),
        my_repeated_doubles=expected_repeated_doubles,
        repeated_submessages=expected_repeated_submessages,
        my_oneof_double=2.0,
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())
    skill = skills.ai.intrinsic.my_skill(
        my_double=parameters.my_double,
        my_float=parameters.my_float,
        my_int32=parameters.my_int32,
        my_int64=parameters.my_int64,
        my_string=parameters.my_string,
        my_uint32=parameters.my_uint32,
        my_uint64=parameters.my_uint64,
        my_bool=parameters.my_bool,
        sub_message=parameters.sub_message,
        pose=data_types.Pose3(),
        my_repeated_doubles=expected_repeated_doubles,
        repeated_submessages=expected_repeated_submessages,
        my_oneof_double=parameters.my_oneof_double,
        a=provided.ResourceHandle.create(resource_name, [resource_capability]),
    )

    expected_proto = behavior_call_pb2.BehaviorCall(
        skill_id=skill_id, return_value_name=skill.proto.return_value_name
    )
    expected_proto.resources[resource_slot].handle = resource_name
    expected_proto.parameters.Pack(parameters)

    compare.assertProto2Equal(self, expected_proto, skill.proto)

    skill_str = (
        'skills.my_skill('
        'my_double=1.1, '
        'my_float=2.0, '
        'my_int32=1, '
        'my_int64=2, '
        'my_uint32=10, '
        'my_uint64=20, '
        'my_bool=True, '
        "my_string='foo', "
        'sub_message=name: "bar"\n, '
        'my_repeated_doubles=[2.1, 3.1], '
        'repeated_submessages=[name: "foo"\n, name: "bar"\n], '
        'my_oneof_double=2.0, '
        'pose=position {\n}\norientation {\n  w: 1.0\n}\n, '
        'a={handle: "some-name"})'
    )
    self.assertEqual(str(skill), skill_str)

  def test_gen_skill_uses_defaults(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    parameter_defaults = _DEFAULT_TEST_MESSAGE

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=parameter_defaults,
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    skill = skills.ai.intrinsic.my_skill(
        a=provided.ResourceHandle.create(resource_name, [resource_capability])
    )

    expected_proto = behavior_call_pb2.BehaviorCall(
        skill_id=skill_id, return_value_name=skill.proto.return_value_name
    )
    expected_proto.resources[resource_slot].handle = resource_name
    expected_proto.parameters.Pack(parameter_defaults)

    compare.assertProto2Equal(self, expected_proto, skill.proto)

    skill_str = (
        'skills.my_skill('
        'my_double=2.5, '
        'my_float=-1.5, '
        'my_int32=5, '
        'my_int64=9, '
        'my_uint32=11, '
        'my_uint64=21, '
        'my_bool=False, '
        "my_string='bar', "
        'sub_message=name: "baz"\n, '
        'optional_sub_message=name: "quz"\n, '
        'my_repeated_doubles=[-5.5, 10.5], '
        'repeated_submessages=[name: "foo"\n, name: "bar"\n], '
        'my_required_int32=42, '
        'my_oneof_double=1.5, '
        'pose=position {\n}\norientation {\n  x: 0.5\n  y: 0.5\n  z: 0.5\n  w:'
        ' 0.5\n}\n, '
        'foo=bar {\n  test: "test"\n}\n, '
        'enum_v=3, '
        'executive_test_message=int32_value: 123\n, '
        'string_int32_map={"foo": 1}, '
        "int32_string_map={3: 'foobar'}, "
        'string_message_map={"bar": value: "baz"\n}, '
        'non_unique_field_name=non_unique_field_name {\n}\n, '
        'a={handle: "some-name"})'
    )
    self.assertEqual(str(skill), skill_str)

  def test_gen_skill_nested_map(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    # No default parameters
    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    parameters = test_skill_params_pb2.TestMessage(
        executive_test_message=test_message_pb2.TestMessage(
            string_int32_map={'foo': 2}
        )
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())
    skill = skills.ai.intrinsic.my_skill(
        executive_test_message=parameters.executive_test_message,
        a=provided.ResourceHandle.create(resource_name, [resource_capability]),
    )

    expected_proto = behavior_call_pb2.BehaviorCall(
        skill_id=skill_id, return_value_name=skill.proto.return_value_name
    )
    expected_proto.resources[resource_slot].handle = resource_name
    expected_proto.parameters.Pack(parameters)

    compare.assertProto2Equal(self, expected_proto, skill.proto)

    skill_str = (
        'skills.my_skill('
        'executive_test_message=string_int32_map {\n  key: "foo"\n  value:'
        ' 2\n}\n, '
        'a={handle: "some-name"})'
    )
    self.assertEqual(str(skill), skill_str)

  @parameterized.parameters(
      {
          'value_specification': blackboard_value.BlackboardValue(
              {}, 'test', None, None
          )
      },
      {'value_specification': cel.CelExpression('test')},
  )
  def test_gen_skill_with_blackboard_parameter(self, value_specification):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    parameter_defaults = _DEFAULT_TEST_MESSAGE

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=parameter_defaults,
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    skill = skills.ai.intrinsic.my_skill(
        my_oneof_double=value_specification,
        a=provided.ResourceHandle.create(resource_name, [resource_capability]),
    )

    expected_proto = behavior_call_pb2.BehaviorCall(
        skill_id=skill_id, return_value_name=skill.proto.return_value_name
    )
    expected_proto.resources[resource_slot].handle = resource_name
    expected_proto.parameters.Pack(parameter_defaults)
    expected_proto.assignments.append(
        behavior_call_pb2.BehaviorCall.ParameterAssignment(
            parameter_path='my_oneof_double', cel_expression='test'
        )
    )

    compare.assertProto2Equal(self, expected_proto, skill.proto)

  @parameterized.parameters(
      {
          'value_specification': blackboard_value.BlackboardValue(
              {}, 'test', None, None
          )
      },
      {'value_specification': cel.CelExpression('test')},
  )
  def test_gen_skill_with_nested_blackboard_parameter(
      self, value_specification
  ):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    my_skill = skills.ai.intrinsic.my_skill

    skill = my_skill(
        my_oneof_double=value_specification,
        a=provided.ResourceHandle.create(resource_name, [resource_capability]),
        executive_test_message=my_skill.intrinsic_proto.executive.TestMessage(
            message_list=[
                my_skill.intrinsic_proto.executive.TestMessage(
                    int32_value=value_specification
                ),
                my_skill.intrinsic_proto.executive.TestMessage(
                    message_value=value_specification
                ),
                my_skill.intrinsic_proto.executive.TestMessage(
                    foo_msg=value_specification
                ),
                my_skill.intrinsic_proto.executive.TestMessage(
                    message_list=[
                        my_skill.intrinsic_proto.executive.TestMessage(
                            message_value=value_specification
                        )
                    ]
                ),
                my_skill.intrinsic_proto.executive.TestMessage(
                    message_list=[
                        my_skill.intrinsic_proto.executive.TestMessage(
                            message_list=value_specification
                        )
                    ]
                ),
                my_skill.intrinsic_proto.executive.TestMessage(
                    message_list=[value_specification, value_specification]
                ),
                value_specification,
                my_skill.intrinsic_proto.executive.TestMessage(
                    int32_list=[value_specification, value_specification]
                ),
                # The following is NOT supported, we cannot set a map value from
                # a CEL expression (we cannot address the field with proto_path)
                # my_skill.intrinsic_proto.executive.TestMessage(
                #   string_int32_map={'foo_key': value_specification}
                # ),
            ]
        ),
    )

    expected_proto = behavior_call_pb2.BehaviorCall(
        skill_id=skill_id,
        return_value_name=skill.proto.return_value_name,
        assignments=[
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path='my_oneof_double', cel_expression='test'
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[0].int32_value'
                ),
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[1].message_value'
                ),
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path='executive_test_message.message_list[2].foo_msg',
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path='executive_test_message.message_list[3].message_list[0].message_value',
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path='executive_test_message.message_list[4].message_list[0].message_list',
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[5].message_list[0]'
                ),
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[5].message_list[1]'
                ),
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path='executive_test_message.message_list[6]',
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[7].int32_list[0]'
                ),
                cel_expression='test',
            ),
            behavior_call_pb2.BehaviorCall.ParameterAssignment(
                parameter_path=(
                    'executive_test_message.message_list[7].int32_list[1]'
                ),
                cel_expression='test',
            ),
        ],
    )
    expected_proto.resources[resource_slot].handle = resource_name

    expected_parameters = test_skill_params_pb2.TestMessage(
        executive_test_message=test_message_pb2.TestMessage(
            message_list=[
                test_message_pb2.TestMessage(),
                test_message_pb2.TestMessage(),
                test_message_pb2.TestMessage(),
                test_message_pb2.TestMessage(
                    message_list=[test_message_pb2.TestMessage()]
                ),
                test_message_pb2.TestMessage(
                    message_list=[test_message_pb2.TestMessage()]
                ),
                test_message_pb2.TestMessage(
                    message_list=[
                        test_message_pb2.TestMessage(),
                        test_message_pb2.TestMessage(),
                    ]
                ),
                test_message_pb2.TestMessage(),
                test_message_pb2.TestMessage(int32_list=[0, 0]),
            ]
        )
    )
    expected_proto.parameters.Pack(expected_parameters)
    compare.assertProto2Equal(self, expected_proto, skill.proto)

  def test_gen_skill_with_map_parameter(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    expected_parameters = test_skill_params_pb2.TestMessage(
        string_int32_map={'foo': 1}
    )

    skill = skills.ai.intrinsic.my_skill(string_int32_map={'foo': 1})

    actual_parameters = test_skill_params_pb2.TestMessage()
    skill.proto.parameters.Unpack(actual_parameters)

    compare.assertProto2Equal(self, expected_parameters, actual_parameters)

  def test_gen_skill_with_message_map_parameter_from_alias(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    expected_parameters = test_skill_params_pb2.TestMessage(
        string_message_map={
            'foo': test_skill_params_pb2.TestMessage.MessageMapValue(
                value='bar'
            )
        }
    )

    my_skill = skills.ai.intrinsic.my_skill

    skill = my_skill(
        string_message_map={
            'foo': (
                my_skill.intrinsic_proto.test_data.TestMessage.MessageMapValue(
                    value='bar'
                )
            )
        }
    )

    actual_parameters = test_skill_params_pb2.TestMessage()
    skill.proto.parameters.Unpack(actual_parameters)

    compare.assertProto2Equal(self, expected_parameters, actual_parameters)

  def test_gen_skill_with_message_map_parameter_from_actual_type(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    expected_parameters = test_skill_params_pb2.TestMessage(
        string_message_map={
            'foo': test_skill_params_pb2.TestMessage.MessageMapValue(
                value='bar'
            )
        }
    )

    skill = skills.ai.intrinsic.my_skill(
        string_message_map={
            'foo': test_skill_params_pb2.TestMessage.MessageMapValue(
                value='bar'
            )
        }
    )

    actual_parameters = test_skill_params_pb2.TestMessage()
    skill.proto.parameters.Unpack(actual_parameters)

    compare.assertProto2Equal(self, expected_parameters, actual_parameters)

  def test_gen_skill_with_return_value_key(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.SubMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    my_skill = skills.ai.intrinsic.my_skill

    self.assertRegex(my_skill().proto.return_value_name, '^my_skill_.*$')
    self.assertRegex(
        my_skill(return_value_key=None).proto.return_value_name, '^my_skill_.*$'
    )
    self.assertEqual(
        my_skill(return_value_key='foo').proto.return_value_name, 'foo'
    )

  def test_gen_skill_fails_for_set_instead_of_dict(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    with self.assertRaisesRegex(TypeError, 'Got set where expected dict'):
      # In the following, the map parameter should be initialized as {'foo': 1},
      # with a colon instead of a comma.
      skills.ai.intrinsic.my_skill(string_int32_map={'foo', 1})

  def test_gen_skill_map_rejects_blackboard_value(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    with self.assertRaisesRegex(
        TypeError, 'Cannot set field .* from blackboard'
    ):
      skills.ai.intrinsic.my_skill(
          string_int32_map={
              'foo': blackboard_value.BlackboardValue({}, 'test', None, None),
          }
      )

  def test_gen_skill_with_invalid_parameter(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_name = 'some-name'
    resource_capability = 'some-type'
    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    parameter_defaults = _DEFAULT_TEST_MESSAGE

    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=parameter_defaults,
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    # Assignment to unknown field should fail
    with self.assertRaisesRegex(KeyError, 'not_a_field.*does not exist'):
      skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage(
          not_a_field='hello'
      )

    blackboard_test_value = blackboard_value.BlackboardValue(
        {}, 'test', None, None
    )
    # Assigning blackboard value to unknown field should fail
    with self.assertRaisesRegex(KeyError, 'not_a_field.*does not exist'):
      skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage(
          not_a_field=blackboard_test_value
      )

  def test_compatible_resources(self):
    skill_registry_stub = mock.MagicMock()
    skill_registry_stub.GetSkills.return_value = text_format.Parse(
        """
        skills {
          id: 'ai.intrinsic.skill_one'
          resource_selectors {
            key: 'slot_one'
            value {
              capability_names: 'foo_type'
              capability_names: 'bar_type'
            }
          }
        }
        skills {
          id: 'ai.intrinsic.skill_two'
          resource_selectors {
            key: 'slot_two_a'
            value {
              capability_names: 'foo_type'
            }
          }
          resource_selectors {
            key: 'slot_two_b'
            value {
              capability_names: 'bar_type'
            }
          }
        }
        skills {
          id: 'ai.intrinsic.skill_three'
        }
        skills {
          id: 'ai.intrinsic.skill_four'
          resource_selectors {
            key: 'slot_one'
            value {
              capability_names: 'type_not_matched_by_any_resource'
            }
          }
        }""",
        skill_registry_pb2.GetSkillsResponse(),
    )
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    resource_registry = self._utils.create_resource_registry_with_handles([
        text_format.Parse(
            """name: 'foo_resource'
               resource_data { key: 'foo_type' }""",
            resource_handle_pb2.ResourceHandle(),
        ),
        text_format.Parse(
            """name: 'foo_bar_resource'
               resource_data { key: 'foo_type' }
               resource_data { key: 'bar_type' }""",
            resource_handle_pb2.ResourceHandle(),
        ),
        text_format.Parse(
            """name: 'bar_resource'
               resource_data { key: 'bar_type' }""",
            resource_handle_pb2.ResourceHandle(),
        ),
    ])

    skills = skill_providing.Skills(skill_registry, resource_registry)

    self.assertCountEqual(
        dir(skills.ai.intrinsic.skill_one.compatible_resources['slot_one']),
        ['foo_bar_resource'],
    )
    self.assertCountEqual(
        dir(skills.ai.intrinsic.skill_two.compatible_resources['slot_two_a']),
        ['foo_bar_resource', 'foo_resource'],
    )
    self.assertCountEqual(
        dir(skills.ai.intrinsic.skill_two.compatible_resources['slot_two_b']),
        ['bar_resource', 'foo_bar_resource'],
    )
    self.assertCountEqual(
        dir(skills.ai.intrinsic.skill_three.compatible_resources), []
    )
    self.assertCountEqual(
        dir(skills.ai.intrinsic.skill_four.compatible_resources['slot_one']), []
    )

  def test_gen_skill_incompatible_resources(self):
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'
           resource_selectors {
             key: 'a'
             value {
               capability_names: 'some-type'
               capability_names: 'another-type'
             }
           }
        """ % skill_id,
        skills_pb2.Skill(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    resource_a = provided.ResourceHandle.create('resource_a', ['some-type'])

    with self.assertRaises(TypeError):
      skills.ai.intrinsic.my_skill(a=resource_a)

  def test_skill_class_name(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info('ai.intrinsic.my_skill'),
        self._utils.create_parameterless_skill_info('global_skill'),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )

    self.assertEqual(skills.ai.intrinsic.my_skill.__name__, 'my_skill')
    self.assertEqual(skills.ai.intrinsic.my_skill.__qualname__, 'my_skill')
    self.assertEqual(
        skills.ai.intrinsic.my_skill.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

    self.assertEqual(skills.global_skill.__name__, 'global_skill')
    self.assertEqual(skills.global_skill.__qualname__, 'global_skill')
    self.assertEqual(
        skills.global_skill.__module__,
        'intrinsic.solutions.skills',
    )

  def test_skill_signature_without_default_values(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessage(),
    )
    parameters = _SKILL_PARAMETER_DICT

    # pyformat: disable
    expected_signature = (
        '(*, '
        'sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'my_required_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'pose: Union[intrinsic.math.python.pose3.Pose3, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.Pose, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'executive_test_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.executive.TestMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'non_unique_field_name: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.SomeType, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'my_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_float: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_int64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_uint32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_uint64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_bool: Union[bool, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_string: Union[str, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'optional_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_repeated_doubles: Union[Sequence[Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [], '
        'repeated_submessages: Union[Sequence[Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [], '
        'my_oneof_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_oneof_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'foo: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.Foo, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'enum_v: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.TestEnum, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'string_int32_map: Union[dict[str, '
        'int], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {}, '
        'int32_string_map: Union[dict[int, '
        'str], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {}, '
        'string_message_map: Union[dict[str, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.MessageMapValue], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {}, '
        'return_value_key: Optional[str] = None)'
    )
    # pyformat: enable

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill(**parameters)
    signature = inspect.signature(my_skill.__init__)
    self.assertSignature(signature, expected_signature)

  @parameterized.named_parameters(
      {
          'testcase_name': 'PoseSkill',
          'parameter_defaults': test_skill_params_pb2.PoseSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'param_pose: Union[intrinsic.math.python.pose3.Pose3, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.Pose, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'JointMotionTargetSkill',
          'parameter_defaults': test_skill_params_pb2.JointMotionTargetSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'param_joint_motion_target: Union[intrinsic.world.python.object_world_resources.JointConfiguration, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.icon.JointVec, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'CollisionSettingsSkill',
          'parameter_defaults': test_skill_params_pb2.CollisionSettingsSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'param_collision_settings: Union[intrinsic.solutions.worlds.CollisionSettings, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.world.CollisionSettings, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'CartesianMotionTargetSkill',
          'parameter_defaults': (
              test_skill_params_pb2.CartesianMotionTargetSkill()
          ),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'target: Union[intrinsic.solutions.worlds.CartesianMotionTarget, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.motion_planning.CartesianMotionTarget, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'DurationSkill',
          'parameter_defaults': test_skill_params_pb2.DurationSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'param_duration: Union[datetime.timedelta, '
              'float, '
              'int, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.google.protobuf.Duration, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'ObjectReferenceSkill',
          'parameter_defaults': test_skill_params_pb2.ObjectReferenceSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'param_object: Union[intrinsic.world.python.object_world_resources.TransformNode, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.world.ObjectReference, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None, '
              'param_frame: Union[intrinsic.world.python.object_world_resources.TransformNode, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.world.FrameReference, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None, '
              'param_transform_node: Union[intrinsic.world.python.object_world_resources.TransformNode, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.world.TransformNodeReference, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None, '
              'param_object_or_entity: Union[intrinsic.world.python.object_world_resources.WorldObject, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.world.ObjectOrEntityReference, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
      {
          'testcase_name': 'PoseEstimatorSkill',
          'parameter_defaults': test_skill_params_pb2.PoseEstimatorSkill(),
          'expected_signature': (
              # pyformat: disable
              '(*, '
              'pose_estimator: Union[intrinsic.solutions.pose_estimation.PoseEstimatorId, '
              'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.perception.PoseEstimatorId, '
              'intrinsic.solutions.blackboard_value.BlackboardValue, '
              'intrinsic.solutions.cel.CelExpression, '
              'NoneType] = None)'
              # pyformat: enable
          ),
      },
  )
  def test_skill_signature_for_types_with_auto_conversion(
      self, parameter_defaults, expected_signature
  ):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=parameter_defaults,
    )

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill

    signature = inspect.signature(my_skill)
    self.assertSignature(signature, expected_signature)

  def test_skill_signature_with_default_value(self):
    parameter_defaults = _DEFAULT_TEST_MESSAGE

    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill', parameter_defaults=parameter_defaults
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill()
    signature = inspect.signature(my_skill.__init__)

    # pyformat: disable
    expected_signature = (
        '(*, '
        'my_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 2.5, '
        'my_float: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = -1.5, '
        'my_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 5, '
        'my_int64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 9, '
        'my_uint32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 11, '
        'my_uint64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 21, '
        'my_bool: Union[bool, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = False, '
        'my_string: Union[str, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        "intrinsic.solutions.cel.CelExpression] = 'bar', "
        'sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = name: "baz"\n, '
        'optional_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = name: "quz"\n, '
        'my_repeated_doubles: Union[Sequence[Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [-5.5, '
        '10.5], '
        'repeated_submessages: Union[Sequence[Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [name: "foo"\n, '
        'name: "bar"\n], '
        'my_required_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 42, '
        'my_oneof_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = 1.5, '
        'my_oneof_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'pose: Union[intrinsic.math.python.pose3.Pose3, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.Pose, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = Pose3(Rotation3(Quaternion([0.5, '
        '0.5, '
        '0.5, '
        '0.5])),array([0., '
        '0., '
        '0.])), '
        'foo: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.Foo, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = bar {\n  test: "test"\n}\n, '
        'enum_v: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.TestEnum, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = 3, '
        'string_int32_map: Union[dict[str, '
        'int], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        "intrinsic.solutions.cel.CelExpression] = {'foo': 1}, "
        'int32_string_map: Union[dict[int, '
        'str], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        "intrinsic.solutions.cel.CelExpression] = {3: 'foobar'}, "
        'string_message_map: Union[dict[str, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.MessageMapValue], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        "intrinsic.solutions.cel.CelExpression] = {'bar': value: \"baz\"\n}, "
        'executive_test_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.executive.TestMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = int32_value: 123\n, '
        'non_unique_field_name: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.SomeType, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = non_unique_field_name {\n}\n)'
    )
    # pyformat: enable
    self.assertSignature(signature, expected_signature)

  def test_skill_class_docstring(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
        skill_description='This is an awesome skill.',
        resource_selectors={'a': 'some-type-a', 'b': 'some-type-b'},
    )
    docstring = """\
Skill class for ai.intrinsic.my_skill.

This is an awesome skill."""

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    self.assertEqual(skills.ai.intrinsic.my_skill.__doc__, docstring)

  def test_skill_init_docstring(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
        resource_selectors={'a': 'some-type-a', 'b': 'some-type-b'},
    )
    docstring = """\
Initializes an instance of the skill ai.intrinsic.my_skill.

This method accepts the following proto messages:
  - my_skill.intrinsic_proto.Pose
  - my_skill.intrinsic_proto.executive.TestMessage"""
    docstring += """
  - my_skill.intrinsic_proto.test_data.SubMessage
  - my_skill.intrinsic_proto.test_data.TestMessage.Foo
  - my_skill.intrinsic_proto.test_data.TestMessage.Int32StringMapEntry
  - my_skill.intrinsic_proto.test_data.TestMessage.SomeType
  - my_skill.intrinsic_proto.test_data.TestMessage.StringInt32MapEntry
  - my_skill.intrinsic_proto.test_data.TestMessage.StringMessageMapEntry

This method accepts the following proto enums:
  - my_skill.intrinsic_proto.test_data.TestMessage.TestEnum

Args:
    a:
        Resource with capability some-type-a
    b:
        Resource with capability some-type-b
    my_oneof_sub_message:
        Mockup comment
    return_value_key:
        Blackboard key where to store the return value
    enum_v:
        Mockup comment
        Default value: 3
    executive_test_message:
        Mockup comment
        Default value: int32_value: 123

    foo:
        Mockup comment
        Default value: bar {
  test: "test"
}

    int32_string_map:
        Mockup comment
        Default value: {3: 'foobar'}
    my_bool:
        Mockup comment
        Default value: False
    my_double:
        Mockup comment
        Default value: 2.5
    my_float:
        Mockup comment
        Default value: -1.5
    my_int32:
        Mockup comment
        Default value: 5
    my_int64:
        Mockup comment
        Default value: 9
    my_oneof_double:
        Mockup comment
        Default value: 1.5
    my_repeated_doubles:
        Mockup comment
        Default value: [-5.5, 10.5]
    my_required_int32:
        Mockup comment
        Default value: 42
    my_string:
        Mockup comment
        Default value: bar
    my_uint32:
        Mockup comment
        Default value: 11
    my_uint64:
        Mockup comment
        Default value: 21
    non_unique_field_name:
        Mockup comment
        Default value: non_unique_field_name {
}

    optional_sub_message:
        Mockup comment
        Default value: name: "quz"

    pose:
        Mockup comment
        Default value: Pose3(Rotation3([0.5i + 0.5j + 0.5k + 0.5]),[0. 0. 0.])
    repeated_submessages:
        Mockup comment
        Default value: [name: "foo"
, name: "bar"
]
    string_int32_map:
        Mockup comment
        Default value: {'foo': 1}
    string_message_map:
        Mockup comment
        Default value: {'bar': value: "baz"
}"""
    docstring += """
    sub_message:
        Mockup comment
        Default value: name: "baz"
"""
    docstring += """

Returns:
    enum_v:
        Mockup comment
    executive_test_message:
        Mockup comment
    foo:
        Mockup comment
    int32_string_map:
        Mockup comment
    my_bool:
        Mockup comment
    my_double:
        Mockup comment
    my_float:
        Mockup comment
    my_int32:
        Mockup comment
    my_int64:
        Mockup comment
    my_oneof_double:
        Mockup comment
    my_oneof_sub_message:
        Mockup comment
    my_repeated_doubles:
        Mockup comment
    my_required_int32:
        Mockup comment
    my_string:
        Mockup comment
    my_uint32:
        Mockup comment
    my_uint64:
        Mockup comment
    non_unique_field_name:
        Mockup comment
    optional_sub_message:
        Mockup comment
    pose:
        Mockup comment
    repeated_submessages:
        Mockup comment
    string_int32_map:
        Mockup comment
    string_message_map:
        Mockup comment"""
    docstring += """
    sub_message:
        Mockup comment"""

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    self.assertEqual(skills.ai.intrinsic.my_skill.__init__.__doc__, docstring)

  def test_skill_repr(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
        resource_selectors={'a': 'some-type-a', 'b': 'some-type-b'},
    )
    parameters = {'my_float': 1.25, 'my_bool': True}

    skill_repr = (
        'skills.my_skill('
        'my_double=2.5, '
        'my_float=1.25, '
        'my_int32=5, '
        'my_int64=9, '
        'my_uint32=11, '
        'my_uint64=21, '
        'my_bool=True, '
        "my_string='bar', "
        'sub_message=name: "baz"\n, '
        'optional_sub_message=name: "quz"\n, '
        'my_repeated_doubles=[-5.5, 10.5], '
        'repeated_submessages=[name: "foo"\n, name: "bar"\n], '
        'my_required_int32=42, '
        'my_oneof_double=1.5, '
        'pose=position {\n}\n'
        'orientation {\n  x: 0.5\n  y: 0.5\n  z: 0.5\n  w: 0.5\n}\n, '
        'foo=bar {\n  test: "test"\n}\n, '
        'enum_v=3, '
        'executive_test_message=int32_value: 123\n, '
        'string_int32_map={"foo": 1}, '
        "int32_string_map={3: 'foobar'}, "
        'string_message_map={"bar": value: "baz"\n}, '
        'non_unique_field_name=non_unique_field_name {\n}\n, '
        'a={handle: "resource_a"}, '
        'b={handle: "resource_b"})'
    )

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    resource_a = provided.ResourceHandle.create('resource_a', ['some-type-a'])
    resource_b = provided.ResourceHandle.create('resource_b', ['some-type-b'])

    skill = skills.ai.intrinsic.my_skill(
        **parameters, a=resource_a, b=resource_b
    )
    self.assertEqual(repr(skill), skill_repr)

  def test_ambiguous_parameter_and_resource_name(self):
    """Tests ambiguous parameter name and resource slot are handled properly."""
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = self._utils.create_test_skill_info(
        skill_id=skill_id,
        parameter_defaults=test_skill_params_pb2.ResourceConflict(a='bar'),
        resource_selectors={
            # alias chosen to match a field name from ResourceConflict
            'a': 'some-type-a',
        },
    )
    resource_registry = self._utils.create_resource_registry_with_handles([
        text_format.Parse(
            """name: 'some-resource1'
               resource_data { key: 'some-type-a' }""",
            resource_handle_pb2.ResourceHandle(),
        ),
        text_format.Parse(
            """name: 'some-resource2'
               resource_data { key: 'some-type-a' }""",
            resource_handle_pb2.ResourceHandle(),
        ),
    ])

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        resource_registry,
    )

    self.assertEqual(
        skills.ai.intrinsic.my_skill.__init__.__doc__,
        textwrap.dedent("""\
            Initializes an instance of the skill ai.intrinsic.my_skill.

            Args:
                a_resource:
                    Resource with capability some-type-a
                a:
                    Mockup comment
                    Default value: bar"""),
    )

    resource_a = provided.ResourceHandle.create('resource_a', ['some-type-a'])

    skill = skills.ai.intrinsic.my_skill(a='foo', a_resource=resource_a)
    self.assertEqual(
        repr(skill),
        """skills.my_skill(a='foo', a_resource={handle: "resource_a"})""",
    )

    with self.assertRaises(TypeError):
      skills.ai.intrinsic.my_skill(a=resource_a)

    with self.assertRaisesRegex(KeyError, '.*more than one compatible.*'):
      skills.ai.intrinsic.my_skill(a='foo')

  def test_resource_default_value(self):
    """Tests default resource is used properly."""
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'
           resource_selectors {
             key: 'a'
             value { capability_names: 'some-type-a' }
           }
        """ % skill_id,
        skills_pb2.Skill(),
    )

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        'some-resource', 'some-type-a'
    )

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        resource_registry,
    )

    self.assertEqual(
        skills.ai.intrinsic.my_skill.__init__.__doc__,
        textwrap.dedent("""\
      Initializes an instance of the skill ai.intrinsic.my_skill.

      Args:
          a:
              Resource with capability some-type-a
              Default resource: some-resource"""),
    )

    # Ensure that no "resource not found" exception is thrown
    try:
      skills.ai.intrinsic.my_skill()
    except KeyError:
      self.fail('Instantiating skill failed with default resource')

  def test_non_resource_as_resource_is_rejected(self):
    """Tests non-resource passed for resource parameter is rejected."""
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'
           resource_selectors {
             key: 'a'
             value {
               capability_names: 'some-type-a'
             }
           }
        """ % skill_id,
        skills_pb2.Skill(),
    )

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        'some-resource', 'some-type-a'
    )

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        resource_registry,
    )

    class BogusObject:

      def __init__(self):
        pass

    with self.assertRaisesRegex(TypeError, '.* not a ResourceHandle'):
      skills.ai.intrinsic.my_skill(a=BogusObject())

  def test_timeouts(self):
    """Tests if timeouts are transferred to proto."""
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(f"id: '{skill_id}'", skills_pb2.Skill())
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    skill = skills.ai.intrinsic.my_skill()
    skill.execute_timeout = datetime.timedelta(seconds=5)
    skill.project_timeout = datetime.timedelta(seconds=10)

    expected_proto = text_format.Parse(
        f"""skill_id: '{skill_id}'
            return_value_name: "{skill.proto.return_value_name}"
            skill_execution_options {{
              execute_timeout {{
                seconds: 5
              }}
              project_timeout {{
                seconds: 10
              }}
            }}
        """,
        behavior_call_pb2.BehaviorCall(),
    )
    compare.assertProto2Equal(self, skill.proto, expected_proto)

  def test_nested_message_classes(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    sub_message = (
        skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage(
            name='nested_message_classes_test_name'
        )
    )

    skill_with_nested_class_generated_param = skills.ai.intrinsic.my_skill(
        sub_message=sub_message
    )
    action_proto = skill_with_nested_class_generated_param.proto

    test_message = test_skill_params_pb2.TestMessage()
    action_proto.parameters.Unpack(test_message)
    self.assertEqual(
        test_message.sub_message.name, sub_message.wrapped_message.name
    )

  def test_nested_message_list_with_blackboard_value(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    sub_message = (
        skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage(
            name=cel.CelExpression('test')
        )
    )

    skill_with_nested_class_generated_param = skills.ai.intrinsic.my_skill(
        repeated_submessages=[sub_message]
    )
    action_proto = skill_with_nested_class_generated_param.proto

    test_message = test_skill_params_pb2.TestMessage()
    action_proto.parameters.Unpack(test_message)
    self.assertLen(test_message.repeated_submessages, 1)
    self.assertEqual(
        action_proto.assignments[0].parameter_path,
        'repeated_submessages[0].name',
    )
    self.assertEqual(action_proto.assignments[0].cel_expression, 'test')

  def test_construct_skill_info(self):
    skill_generation.SkillInfoImpl(
        self._utils.create_test_skill_info(
            skill_id='ai.intrinsic.my_skill',
            parameter_defaults=test_skill_params_pb2.TestMessage(),
        )
    )

  @parameterized.parameters(
      {
          'skill': skills_pb2.Skill(
              skill_name='my_skill', id='com.foo.some_skill'
          )
      },
      {'skill': skills_pb2.Skill(id='com.foo.my_skill')},
      {'skill': skills_pb2.Skill(id='foo.my_skill')},
      {'skill': skills_pb2.Skill(id='my_skill')},
  )
  def test_skill_info_skill_name(self, skill):
    info = skill_generation.SkillInfoImpl(skill)
    self.assertEqual(info.skill_name, 'my_skill')

  @parameterized.parameters(
      {
          'skill': skills_pb2.Skill(
              package_name='com.foo', id='com.bar.my_skill'
          ),
          'expected_package_name': 'com.foo',
      },
      {
          'skill': skills_pb2.Skill(id='com.foo.my_skill'),
          'expected_package_name': 'com.foo',
      },
      {
          'skill': skills_pb2.Skill(id='foo.my_skill'),
          'expected_package_name': 'foo',
      },
      {
          'skill': skills_pb2.Skill(id='my_skill'),
          'expected_package_name': '',
      },
  )
  def test_skill_info_package_name(self, skill, expected_package_name):
    info = skill_generation.SkillInfoImpl(skill)
    self.assertEqual(info.package_name, expected_package_name)

  def test_result_access(self):
    """Tests if BlackboardValue gets created when accessing result."""
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    parameters = {'my_float': 1.0, 'my_bool': True}
    skill = skills.ai.intrinsic.my_skill(**parameters)
    self.assertIsInstance(skill.result, blackboard_value.BlackboardValue)
    self.assertContainsSubset(
        _DEFAULT_TEST_MESSAGE.DESCRIPTOR.fields_by_name.keys(),
        dir(skill.result),
        'Missing attributes in BlackboardValue',
    )
    self.assertEqual(skill.result.value_access_path(), skill.result_key)

  def test_gen_message_wrapper(self):
    skill_registry, skill_registry_stub = (
        _create_skill_registry_with_mock_stub()
    )

    skill_id = 'ai.intrinsic.my_skill'
    resource_slot = 'a'
    resource_name = 'some-name'
    resource_capability = 'some-type'

    resource_registry = self._utils.create_resource_registry_with_single_handle(
        resource_name, resource_capability
    )

    # No default parameter.
    skill_registry_stub.GetSkills.return_value = (
        self._utils.create_get_skills_response(
            skill_id=skill_id,
            parameter_defaults=test_skill_params_pb2.TestMessage(),
            resource_selectors={resource_slot: resource_capability},
        )
    )

    skills = skill_providing.Skills(skill_registry, resource_registry)

    parameters = test_skill_params_pb2.SubMessage(name='bar')

    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())
    test_message = (
        skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage(
            name=parameters.name
        )
    )

    self.assertEqual('name: "bar"\n', str(test_message.wrapped_message))

  def test_wrapper_class_name(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill

    # test_data is the subpackage of the proto file and should be represented by
    # a simple namespace class.
    self.assertEqual(my_skill.intrinsic_proto.test_data.__name__, 'test_data')
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.__qualname__,
        'my_skill.intrinsic_proto.test_data',
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

    # SubMessage is a top-level message in proto file.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.SubMessage.__name__, 'SubMessage'
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.SubMessage.__qualname__,
        'my_skill.intrinsic_proto.test_data.SubMessage',
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.SubMessage.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

    # Foo (=TestMessage.Foo) is a nested message in proto file.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.Foo.__name__, 'Foo'
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.Foo.__qualname__,
        'my_skill.intrinsic_proto.test_data.TestMessage.Foo',
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.Foo.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

  def test_wrapper_access(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessageWrapped(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill

    # Shortcut notation: skill.<message name>
    self.assertIsInstance(my_skill.SubMessage(), skill_utils.MessageWrapper)
    self.assertIsInstance(my_skill.Foo(), skill_utils.MessageWrapper)
    self.assertIsInstance(my_skill.Bar(), skill_utils.MessageWrapper)
    self.assertIsInstance(my_skill.Any(), skill_utils.MessageWrapper)

    # Id notation: skill.<full message name>
    self.assertIsInstance(
        my_skill.intrinsic_proto.test_data.SubMessage(),
        skill_utils.MessageWrapper,
    )
    self.assertIsInstance(
        my_skill.intrinsic_proto.test_data.TestMessage(),
        skill_utils.MessageWrapper,
    )
    self.assertIsInstance(
        my_skill.intrinsic_proto.test_data.TestMessage.Foo(),
        skill_utils.MessageWrapper,
    )
    self.assertIsInstance(
        my_skill.intrinsic_proto.test_data.TestMessage.Foo.Bar(),
        skill_utils.MessageWrapper,
    )
    self.assertIsInstance(
        my_skill.intrinsic_proto.executive.TestMessage(),
        skill_utils.MessageWrapper,
    )
    self.assertIsInstance(
        my_skill.google.protobuf.Any(),
        skill_utils.MessageWrapper,
    )

  def test_message_wrapper_class_docstring(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessageWrapped(),
    )

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    self.assertEqual(
        skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.__doc__,
        'Proto message wrapper class for'
        ' intrinsic_proto.test_data.TestMessage.',
    )

  def test_message_wrapper_init_docstring(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessageWrapped(),
    )
    docstring = """\
Initializes an instance of my_skill.intrinsic_proto.test_data.TestMessage.

This method accepts the following proto messages:
  - my_skill.intrinsic_proto.Pose
  - my_skill.intrinsic_proto.executive.TestMessage"""
    docstring += """
  - my_skill.intrinsic_proto.test_data.SubMessage
  - my_skill.intrinsic_proto.test_data.TestMessage.Foo
  - my_skill.intrinsic_proto.test_data.TestMessage.Int32StringMapEntry
  - my_skill.intrinsic_proto.test_data.TestMessage.SomeType
  - my_skill.intrinsic_proto.test_data.TestMessage.StringInt32MapEntry
  - my_skill.intrinsic_proto.test_data.TestMessage.StringMessageMapEntry

This method accepts the following proto enums:
  - my_skill.intrinsic_proto.test_data.TestMessage.TestEnum

Fields:
    enum_v:
        Mockup comment
    executive_test_message:
        Mockup comment
    foo:
        Mockup comment
    int32_string_map:
        Mockup comment
    my_bool:
        Mockup comment
    my_double:
        Mockup comment
    my_float:
        Mockup comment
    my_int32:
        Mockup comment
    my_int64:
        Mockup comment
    my_oneof_double:
        Mockup comment
    my_oneof_sub_message:
        Mockup comment
    my_repeated_doubles:
        Mockup comment
    my_required_int32:
        Mockup comment
    my_string:
        Mockup comment
    my_uint32:
        Mockup comment
    my_uint64:
        Mockup comment
    non_unique_field_name:
        Mockup comment
    optional_sub_message:
        Mockup comment
    pose:
        Mockup comment
    repeated_submessages:
        Mockup comment
    string_int32_map:
        Mockup comment
    string_message_map:
        Mockup comment"""
    docstring += """
    sub_message:
        Mockup comment"""

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    my_skill = skills.ai.intrinsic.my_skill

    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.__init__.__doc__,
        docstring,
    )

  def test_message_wrapper_signature(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessageWrapped(),
    )

    # pyformat: disable
    expected_signature = (
        '(*, '
        'sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'my_required_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'pose: Union[intrinsic.math.python.pose3.Pose3, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.Pose, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'executive_test_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.executive.TestMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'non_unique_field_name: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.SomeType, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression], '
        'my_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_float: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_int32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_int64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_uint32: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_uint64: Union[int, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_bool: Union[bool, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_string: Union[str, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'optional_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_repeated_doubles: Union[Sequence[Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [], '
        'repeated_submessages: Union[Sequence[Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression]], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = [], '
        'my_oneof_double: Union[float, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'my_oneof_sub_message: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.SubMessage, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'foo: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.Foo, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'enum_v: Union[intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.TestEnum, '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression, '
        'NoneType] = None, '
        'string_int32_map: Union[dict[str, '
        'int], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {}, '
        'int32_string_map: Union[dict[int, '
        'str], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {}, '
        'string_message_map: Union[dict[str, '
        'intrinsic.solutions.skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage.MessageMapValue], '
        'intrinsic.solutions.blackboard_value.BlackboardValue, '
        'intrinsic.solutions.cel.CelExpression] = {})'
    )
    # pyformat: enable

    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill
    signature = inspect.signature(
        my_skill.intrinsic_proto.test_data.TestMessage
    )
    self.assertSignature(signature, expected_signature)

  def test_message_wrapper_params(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.TestMessageWrapped(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    expected_test_message = test_skill_params_pb2.TestMessage(
        my_double=2,
        my_float=-1.8,
        my_int32=5,
        my_uint32=11,
        my_bool=True,
        my_string='bar',
        repeated_submessages=[
            test_skill_params_pb2.SubMessage(),
            test_skill_params_pb2.SubMessage(name='foo'),
            test_skill_params_pb2.SubMessage(),
            test_skill_params_pb2.SubMessage(),
        ],
    )

    test_message_wrapper = (
        skills.ai.intrinsic.my_skill.intrinsic_proto.test_data.TestMessage(
            my_double=2.0,
            my_float=-1.8,
            my_int32=5,
            my_int64=blackboard_value.BlackboardValue(
                {}, 'my_int64', None, None
            ),
            my_uint32=11,
            my_uint64=cel.CelExpression('my_uint64'),
            my_bool=True,
            my_string='bar',
            repeated_submessages=[
                blackboard_value.BlackboardValue({}, 'test', None, None),
                test_skill_params_pb2.SubMessage(name='foo'),
                blackboard_value.BlackboardValue({}, 'bar', None, None),
                cel.CelExpression('fax'),
            ],
        )
    )

    self.assertContainsSubset(
        {
            'repeated_submessages[0]': 'test',
            'repeated_submessages[2]': 'bar',
            'repeated_submessages[3]': 'fax',
            'my_int64': 'my_int64',
            'my_uint64': 'my_uint64',
        },
        test_message_wrapper._blackboard_params,
    )
    compare.assertProto2Equal(
        self, test_message_wrapper.wrapped_message, expected_test_message
    )

  def test_enum_wrapper_class(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.VariousEnumsMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill

    global_enum = my_skill.intrinsic_proto.test_data.GlobalEnum
    self.assertTrue(issubclass(global_enum, enum.IntEnum))
    self.assertEqual(global_enum.__name__, 'GlobalEnum')
    self.assertEqual(
        global_enum.__qualname__,
        'my_skill.intrinsic_proto.test_data.GlobalEnum',
    )
    self.assertEqual(
        global_enum.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

    test_enum = my_skill.intrinsic_proto.test_data.TestMessage.TestEnum
    self.assertTrue(issubclass(test_enum, enum.IntEnum))
    self.assertEqual(test_enum.__name__, 'TestEnum')
    self.assertEqual(
        test_enum.__qualname__,
        'my_skill.intrinsic_proto.test_data.TestMessage.TestEnum',
    )
    self.assertEqual(
        test_enum.__module__,
        'intrinsic.solutions.skills.ai.intrinsic',
    )

  def test_enum_values(self):
    skill_info = self._utils.create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=test_skill_params_pb2.VariousEnumsMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )

    my_skill = skills.ai.intrinsic.my_skill

    # Test global enum.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.GlobalEnum.GLOBAL_ENUM_UNSPECIFIED, 0
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.GlobalEnum.GLOBAL_ENUM_ONE, 1
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.GlobalEnum.GLOBAL_ENUM_TWO, 2
    )

    # Test global enum shortcuts.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.GLOBAL_ENUM_UNSPECIFIED, 0
    )
    self.assertEqual(my_skill.intrinsic_proto.test_data.GLOBAL_ENUM_ONE, 1)
    self.assertEqual(my_skill.intrinsic_proto.test_data.GLOBAL_ENUM_TWO, 2)

    # Test enum which is nested in a message.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.TestEnum.UNKNOWN, 0
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.TestEnum.ONE, 1
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.TestEnum.THREE, 3
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.TestMessage.TestEnum.FIVE, 5
    )

    # Test shortcuts for an enum which is nested in a message.
    self.assertEqual(my_skill.intrinsic_proto.test_data.TestMessage.UNKNOWN, 0)
    self.assertEqual(my_skill.intrinsic_proto.test_data.TestMessage.ONE, 1)
    self.assertEqual(my_skill.intrinsic_proto.test_data.TestMessage.THREE, 3)
    self.assertEqual(my_skill.intrinsic_proto.test_data.TestMessage.FIVE, 5)

    # Test enum which is nested in the skills param message.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VariousEnumsEnum.VARIOUS_ENUMS_ENUM_UNSPECIFIED,
        0,
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VariousEnumsEnum.VARIOUS_ENUMS_ENUM_ONE,
        1,
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VariousEnumsEnum.VARIOUS_ENUMS_ENUM_TWO,
        2,
    )

    # Test shortcuts for enum which is nested in the skills param message.
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VARIOUS_ENUMS_ENUM_UNSPECIFIED,
        0,
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VARIOUS_ENUMS_ENUM_ONE,
        1,
    )
    self.assertEqual(
        my_skill.intrinsic_proto.test_data.VariousEnumsMessage.VARIOUS_ENUMS_ENUM_TWO,
        2,
    )

    # Test special shortcuts directly on skill class for enum which is nested in
    # the skills param message.
    self.assertEqual(my_skill.VARIOUS_ENUMS_ENUM_UNSPECIFIED, 0)
    self.assertEqual(my_skill.VARIOUS_ENUMS_ENUM_ONE, 1)
    self.assertEqual(my_skill.VARIOUS_ENUMS_ENUM_TWO, 2)


if __name__ == '__main__':
  absltest.main()
