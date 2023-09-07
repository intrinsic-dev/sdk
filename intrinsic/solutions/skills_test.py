# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.executive.workcell.public.workcell."""

import datetime
import inspect
import os
import textwrap
from typing import Dict
from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2
from google.protobuf import empty_pb2
from google.protobuf import message
from google.protobuf import text_format
from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.math.proto import point_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.proto import quaternion_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import equipment_registry_pb2
from intrinsic.skills.proto import equipment_registry_pb2_grpc
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import equipment as equipment_mod
from intrinsic.solutions import equipment_registry as equipment_registry_mod
from intrinsic.solutions import skills as skills_mod
from intrinsic.solutions.testing import test_skill_params_pb2


FLAGS = flags.FLAGS


def _read_message_from_pbbin_file(filename):
  with open(filename, 'rb') as fileobj:
    return descriptor_pb2.FileDescriptorSet.FromString(fileobj.read())


def _get_test_message_file_descriptor_set() -> descriptor_pb2.FileDescriptorSet:
  """Returns the file descriptor set of transitive dependencies for TestMessage.

  Requires FLAGS to be parsed prior to invocation.
  """
  test_data_path = os.path.join(
      os.environ.get('TEST_WORKSPACE'),
      'intrinsic/solutions/testing',
  )
  file_descriptor_set_pbbin_filename = os.path.join(
      FLAGS.test_srcdir,
      test_data_path,
      'test_skill_params_proto_descriptors_transitive_set_sci.proto.bin',
  )
  return _read_message_from_pbbin_file(file_descriptor_set_pbbin_filename)


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
    my_repeated_doubles=[-5.5, 10.5],
    repeated_submessages=[
        test_skill_params_pb2.SubMessage(name='foo'),
        test_skill_params_pb2.SubMessage(name='bar'),
    ],
    my_oneof_double=1.5,
    pose=pose_pb2.Pose(
        position=point_pb2.Point(),
        orientation=quaternion_pb2.Quaternion(x=0.5, y=0.5, z=0.5, w=0.5),
    ),
)


def _create_test_skill_info(
    skill_id: str,
    parameter_defaults: message.Message = test_skill_params_pb2.TestMessage(),
    equipment_types: Dict[str, str] = None,
) -> skills_pb2.Skill:
  skill_info = skills_pb2.Skill(id=skill_id)

  skill_info.parameter_description.parameter_descriptor_fileset.CopyFrom(
      _get_test_message_file_descriptor_set()
  )

  skill_info.parameter_description.default_value.Pack(parameter_defaults)

  skill_info.parameter_description.parameter_message_full_name = (
      parameter_defaults.DESCRIPTOR.full_name
  )

  for field in parameter_defaults.DESCRIPTOR.fields:
    skill_info.parameter_description.parameter_field_comments[
        field.full_name
    ] = 'Mockup comment'

  if equipment_types:
    for key, value in equipment_types.items():
      skill_info.equipment_selectors[key].equipment_type_names.append(value)

  return skill_info


def _create_test_skill_info_with_return_value(
    skill_id: str,
    parameter_defaults: message.Message = test_skill_params_pb2.TestMessage(),
    equipment_types: Dict[str, str] = None,
) -> skills_pb2.Skill:
  skill_info = skills_pb2.Skill(id=skill_id)

  skill_info.parameter_description.parameter_descriptor_fileset.CopyFrom(
      _get_test_message_file_descriptor_set()
  )

  skill_info.parameter_description.default_value.Pack(parameter_defaults)

  skill_info.parameter_description.parameter_message_full_name = (
      parameter_defaults.DESCRIPTOR.full_name
  )

  skill_info.return_value_description.descriptor_fileset.CopyFrom(
      _get_test_message_file_descriptor_set()
  )

  skill_info.return_value_description.return_value_message_full_name = (
      parameter_defaults.DESCRIPTOR.full_name
  )

  for field in parameter_defaults.DESCRIPTOR.fields:
    skill_info.parameter_description.parameter_field_comments[
        field.full_name
    ] = 'Mockup comment'

  for field in parameter_defaults.DESCRIPTOR.fields:
    skill_info.return_value_description.return_value_field_comments[
        field.full_name
    ] = 'Mockup comment'

  if equipment_types:
    for key, value in equipment_types.items():
      skill_info.equipment_selectors[key].equipment_type_names.append(value)

  return skill_info


def _create_get_skills_response(
    skill_id: str,
    parameter_defaults: test_skill_params_pb2.TestMessage = test_skill_params_pb2.TestMessage(),
    equipment_types: Dict[str, str] = None,
) -> skill_registry_pb2.GetSkillsResponse:
  skill_info = _create_test_skill_info(
      skill_id, parameter_defaults, equipment_types
  )

  skill_registry_response = skill_registry_pb2.GetSkillsResponse()
  skill_registry_response.skills.add().CopyFrom(skill_info)
  return skill_registry_response


def _skill_registry_with_mock_stub():
  skill_registry_stub = mock.MagicMock()
  skill_registry = skill_registry_client.SkillRegistryClient(
      skill_registry_stub
  )

  return (skill_registry, skill_registry_stub)


class SkillsTest(parameterized.TestCase):
  """Tests public methods of the skills wrapper class."""

  def _create_empty_equipment_registry(
      self,
  ) -> equipment_registry_mod.EquipmentRegistry:
    # Do not use EquipmentRegistryServicerDouble here so we can support simple
    # test cases externally.
    equipment_registry_stub = mock.MagicMock()

    def dummy_batch_get_equipment_by_selector(
        request: equipment_registry_pb2.EquipmentBySelectorBatchRequest,
    ) -> equipment_registry_pb2.EquipmentBySelectorBatchResponse:
      return equipment_registry_pb2.EquipmentBySelectorBatchResponse(
          responses=[
              equipment_registry_pb2.EquipmentBySelectorResponse()
              for _ in request.requests
          ]
      )

    equipment_registry_stub.BatchGetEquipmentBySelector.side_effect = (
        dummy_batch_get_equipment_by_selector
    )
    return equipment_registry_mod.EquipmentRegistry(equipment_registry_stub)

  def assertSignature(self, actual, expected):
    actual = str(actual)
    self.assertEqual(actual, expected)

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
  )
  def test_gen_skill_param_message_type_mismatch(self, parameter):
    skill_registry, skill_registry_stub = _skill_registry_with_mock_stub()
    skill_registry_stub.GetSkills.return_value = _create_get_skills_response(
        'my_skill', parameter_defaults=_DEFAULT_TEST_MESSAGE
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )

    with self.assertRaises(TypeError):
      skills.my_skill(**parameter)

  def test_list_skills(self):
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'""" % skill_id, skills_pb2.Skill()
    )
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub = mock.MagicMock()
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )

    skills = dir(skills)
    self.assertEqual(skills, ['my_skill'])
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

  def test_gen_skill_incompatible_equipment(self):
    skill_registry_stub = mock.MagicMock()
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'
           equipment_selectors {
             key: 'a'
             value {
               equipment_type_names: 'some-type'
               equipment_type_names: 'another-type'
             }
           }
        """ % skill_id,
        skills_pb2.Skill(),
    )
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    equipment_a = equipment_mod.EquipmentHandle.create(
        'equipment_a', ['some-type']
    )

    with self.assertRaises(TypeError):
      skills.my_skill(a=equipment_a)

  def test_skills_access(self):
    skill_registry_stub = mock.MagicMock()
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(
        """id: '%s'""" % skill_id, skills_pb2.Skill()
    )
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )

    _ = skills['my_skill']

    with self.assertRaises(KeyError):
      _ = skills['skill5']

  def test_skill_signature(self):
    skill_info = _create_test_skill_info(skill_id='ai.intrinsic.my_skill')
    parameters = _SKILL_PARAMETER_DICT

    # pyformat: disable
    expected_signature = (
        '(*, '
        'my_double: float, '
        'my_float: float, '
        'my_int32: int, '
        'my_int64: int, '
        'my_uint32: int, '
        'my_uint64: int, '
        'my_bool: bool, '
        'my_string: str, '
        'sub_message: intrinsic.solutions.skills.my_skill.SubMessage, '
        'optional_sub_message: intrinsic.solutions.skills.my_skill.SubMessage, '
        'my_required_int32: int, '
        'my_oneof_double: float, '
        'my_oneof_sub_message: intrinsic.solutions.skills.my_skill.SubMessage, '
        'pose: intrinsic.solutions.skills.my_skill.Pose, '
        'foo: intrinsic.solutions.skills.my_skill.Foo, '
        'enum_v: int, '
        'my_repeated_doubles: Sequence[float] = [], '
        'repeated_submessages: Sequence[intrinsic.solutions.skills.my_skill.SubMessage] '
        '= [])'
    )
    # pyformat: enable

    skill_registry_stub = mock.MagicMock()
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )

    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    my_skill = skills.my_skill(**parameters)
    signature = inspect.signature(my_skill.__init__)
    self.assertSignature(signature, expected_signature)

  def test_skill_signature_with_default_value(self):
    skill_registry_stub = mock.MagicMock()

    parameter_defaults = _DEFAULT_TEST_MESSAGE

    skill_info = _create_test_skill_info(
        skill_id='ai.intrinsic.my_skill', parameter_defaults=parameter_defaults
    )

    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    my_skill = skills.my_skill()
    signature = inspect.signature(my_skill.__init__)

    expected_signature = (
        '(*, '
        'sub_message:'
        ' intrinsic.solutions.skills.my_skill.SubMessage, '
        'optional_sub_message:'
        ' intrinsic.solutions.skills.my_skill.SubMessage, '
        'my_required_int32: int, '
        'my_oneof_sub_message:'
        ' intrinsic.solutions.skills.my_skill.SubMessage, '
        'pose:'
        ' intrinsic.solutions.skills.my_skill.Pose, '
        'foo: intrinsic.solutions.skills.my_skill.Foo, '
        'enum_v: int, '
        'my_double: float = 2.5, '
        'my_float: float = -1.5, '
        'my_int32: int = 5, '
        'my_int64: int = 9, '
        'my_uint32: int = 11, '
        'my_uint64: int = 21, '
        'my_bool: bool = False, '
        "my_string: str = 'bar', "
        'my_repeated_doubles: Sequence[float] = [-5.5, 10.5], '
        'repeated_submessages:'
        ' Sequence[intrinsic.solutions.skills.my_skill.SubMessage]'
        ' = [name: "foo"\n, name: "bar"\n], '
        'my_oneof_double: float = 1.5)'
    )
    self.assertSignature(signature, expected_signature)

  def test_str(self):
    """Tests if Action conversion to string works."""
    skill_info = _create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
        equipment_types={'a': 'some-type-a', 'b': 'some-type-b'},
    )
    docstring = """\
Skill class for ai.intrinsic.my_skill skill.


Args:
    a:
        equipment of type some-type-a
    b:
        equipment of type some-type-b
    enum_v:
        Mockup comment
    foo:
        Mockup comment
    my_oneof_sub_message:
        Mockup comment
    my_required_int32:
        Mockup comment
    optional_sub_message:
        Mockup comment
    pose:
        Mockup comment
    return_value_key:
        Blackboard key where to store the return value"""
    docstring += """
    sub_message:
        Mockup comment"""
    docstring += """
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
    my_string:
        Mockup comment
        Default value: bar
    my_uint32:
        Mockup comment
        Default value: 11
    my_uint64:
        Mockup comment
        Default value: 21
    repeated_submessages:
        Mockup comment
        Default value: [name: "foo"
, name: "bar"
]

Returns:
    enum_v:
        Mockup comment
    foo:
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
    optional_sub_message:
        Mockup comment
    pose:
        Mockup comment
    repeated_submessages:
        Mockup comment"""
    docstring += """
    sub_message:
        Mockup comment"""
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
        'my_repeated_doubles=[-5.5, 10.5], '
        'repeated_submessages=[name: "foo"\n, name: "bar"\n], '
        'my_oneof_double=1.5, '
        'pose=position {\n}\n'
        'orientation {\n  x: 0.5\n  y: 0.5\n  z: 0.5\n  w: 0.5\n}\n, '
        'a={handle: "equipment_a"}, '
        'b={handle: "equipment_b"})'
    )

    skill_registry_stub = mock.MagicMock()
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)

    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    self.assertEqual(skills.my_skill.__doc__, docstring)

    equipment_a = equipment_mod.EquipmentHandle.create(
        'equipment_a', ['some-type-a']
    )
    equipment_b = equipment_mod.EquipmentHandle.create(
        'equipment_b', ['some-type-b']
    )

    skill = skills.my_skill(**parameters, a=equipment_a, b=equipment_b)
    self.assertEqual(repr(skill), skill_repr)

  def test_timeouts(self):
    """Tests if timeouts are transferred to proto."""
    skill_id = 'ai.intrinsic.my_skill'
    skill_info = text_format.Parse(f"id: '{skill_id}'", skills_pb2.Skill())
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub = mock.MagicMock()
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )

    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    skill = skills.my_skill()
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
    self.assertEqual(skill.proto, expected_proto)

  def test_nested_message_classes(self):
    skill_info = _create_test_skill_info(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
    )

    skill_registry_stub = mock.MagicMock()
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    sub_message_cls = skills.my_skill.SubMessage
    sub_message = sub_message_cls(name='nested_message_classes_test_name')

    skill_with_nested_class_generated_param = skills.my_skill(
        sub_message=sub_message
    )
    action_proto = skill_with_nested_class_generated_param.proto

    test_message = test_skill_params_pb2.TestMessage()
    action_proto.parameters.Unpack(test_message)
    self.assertEqual(
        test_message.sub_message.name, sub_message.wrapped_message.name
    )

  def test_construct_skill_info(self):
    skills_mod.SkillInfoImpl(
        _create_test_skill_info(skill_id='ai.intrinsic.my_skill')
    )

  def test_result_access(self):
    """Tests if BlackboardValue gets created when accessing result."""
    skill_info = _create_test_skill_info_with_return_value(
        skill_id='ai.intrinsic.my_skill',
        parameter_defaults=_DEFAULT_TEST_MESSAGE,
    )

    skill_registry_stub = mock.MagicMock()
    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)

    skill_registry_stub.GetSkills.return_value = skill_registry_response
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skills = skills_mod.Skills(
        skill_registry, self._create_empty_equipment_registry()
    )
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    parameters = {'my_float': 1.0, 'my_bool': True}
    skill = skills.my_skill(**parameters)
    self.assertIsInstance(skill.result, blackboard_value.BlackboardValue)
    self.assertContainsSubset(
        _DEFAULT_TEST_MESSAGE.DESCRIPTOR.fields_by_name.keys(),
        dir(skill.result),
        'Missing attributes in BlackboardValue',
    )
    self.assertEqual(skill.result.value_access_path(), skill.result_key)


if __name__ == '__main__':
  absltest.main()
