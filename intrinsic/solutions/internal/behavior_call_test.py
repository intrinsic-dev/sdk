# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.executive.workcell.public.plan."""

import datetime
import os
from unittest import mock

from absl import flags
from absl.testing import absltest
from google.protobuf import descriptor_pb2
from google.protobuf import empty_pb2
from google.protobuf import text_format
from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import skill_registry_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import skills as skills_mod
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions
from intrinsic.solutions.internal import behavior_call
from intrinsic.solutions.testing import test_skill_params_pb2


def _create_behavior_call_proto(index: int) -> behavior_call_pb2.BehaviorCall:
  proto = behavior_call_pb2.BehaviorCall(skill_id=f'ai.intrinsic.skill-{index}')
  return proto


def _get_file_descriptor_set():
  test_data_path = os.path.join(
      os.environ.get('TEST_WORKSPACE'),
      'intrinsic/solutions/testing/'
      'test_skill_params_proto_descriptors_transitive_set_sci.proto.bin',
  )

  test_data_filename = os.path.join(flags.FLAGS.test_srcdir, test_data_path)

  with open(test_data_filename, 'rb') as fileobj:
    return descriptor_pb2.FileDescriptorSet.FromString(fileobj.read())


class BehaviorCallActionTest(absltest.TestCase):
  """Tests behavior_call.Action."""

  def test_init_from_proto(self):
    """Tests if BehaviorCallProto object can be constructed from proto."""
    empty_action = behavior_call.Action()
    self.assertEqual(empty_action.proto, behavior_call_pb2.BehaviorCall())

    proto = _create_behavior_call_proto(123)
    action: actions.ActionBase = behavior_call.Action(proto)
    self.assertEqual(action.proto, proto)
    proto.skill_id = 'ai.intrinsic.different_name'
    self.assertEqual(action.proto, _create_behavior_call_proto(123))

  def test_init_from_id(self):
    """Tests if Action object can be constructed from skill ID string."""
    proto = _create_behavior_call_proto(234)
    action = behavior_call.Action(skill_id=proto.skill_id)
    self.assertEqual(action.proto, proto)

  def test_set_proto(self):
    """Tests if proto can properly be read and set."""
    proto = _create_behavior_call_proto(123)
    action = behavior_call.Action()
    self.assertEqual(action.proto, behavior_call_pb2.BehaviorCall())
    action.proto = proto
    self.assertEqual(action.proto, proto)

  def test_timeouts(self):
    """Tests if timeouts are transferred to proto."""
    proto = _create_behavior_call_proto(123)
    action = behavior_call.Action(proto)
    self.assertEqual(action.proto, proto)
    action.execute_timeout = datetime.timedelta(seconds=5)
    action.project_timeout = datetime.timedelta(seconds=10)
    proto.skill_execution_options.execute_timeout.FromTimedelta(
        datetime.timedelta(seconds=5)
    )
    proto.skill_execution_options.project_timeout.FromTimedelta(
        datetime.timedelta(seconds=10)
    )
    self.assertEqual(action.proto, proto)

  def test_str(self):
    """Tests if Action conversion to string works."""
    self.assertEqual(repr(behavior_call.Action()), r"""Action(skill_id='')""")
    self.assertEqual(str(behavior_call.Action()), r"""Action(skill_id='')""")

    proto = text_format.Parse(
        r"""
            skill_id: "ai.intrinsic.my_custom_action"
            equipment {
              key: "device"
              value {
                handle: "SomeSpeaker"
              }
            }
        """,
        behavior_call_pb2.BehaviorCall(),
    )
    self.assertEqual(
        repr(behavior_call.Action(proto)),
        r"""Action(skill_id='ai.intrinsic.my_custom_action')."""
        r"""require(device={handle: "SomeSpeaker"})""",
    )
    self.assertEqual(
        str(behavior_call.Action(proto)),
        r"""Action(skill_id='ai.intrinsic.my_custom_action')."""
        r"""require(device={handle: "SomeSpeaker"})""",
    )

  def test_to_python_no_parameter(self):
    """Tests if Action conversion to python string works without parameters."""

    skill_registry_stub = mock.MagicMock()
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skill_id = 'ai.intrinsic.my_skill'

    skill_info = skills_pb2.Skill(skill_name='my_skill', id=skill_id)

    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response

    equipment_registry_stub = mock.MagicMock()

    skills = skills_mod.Skills(skill_registry, equipment_registry_stub)
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    action = behavior_call_pb2.BehaviorCall(skill_id=skill_id)

    self.assertEqual(
        behavior_call.Action(action).to_python(
            utils.PrefixOptions(), 'action_0', skills
        ),
        'action_0 = skills.my_skill()',
    )

  def test_to_python_with_parameter(self):
    """Tests if Action conversion to python string works with parameters."""

    skill_registry_stub = mock.MagicMock()
    skill_registry = skill_registry_client.SkillRegistryClient(
        skill_registry_stub
    )

    skill_id = 'ai.intrinsic.my_skill'

    skill_info = skills_pb2.Skill(skill_name='my_skill', id=skill_id)

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
        my_repeated_doubles=[0.3, 0.4],
    )

    skill_info.parameter_description.parameter_descriptor_fileset.CopyFrom(
        _get_file_descriptor_set()
    )
    skill_info.parameter_description.default_value.Pack(parameters)
    skill_info.parameter_description.parameter_message_full_name = (
        parameters.DESCRIPTOR.full_name
    )

    skill_registry_response = skill_registry_pb2.GetSkillsResponse()
    skill_registry_response.skills.add().CopyFrom(skill_info)
    skill_registry_stub.GetSkills.return_value = skill_registry_response

    equipment_registry_stub = mock.MagicMock()

    skills = skills_mod.Skills(skill_registry, equipment_registry_stub)
    skill_registry_stub.GetSkills.assert_called_once_with(empty_pb2.Empty())

    action = behavior_call_pb2.BehaviorCall(skill_id=skill_id)
    action.parameters.Pack(parameters)

    self.assertEqual(
        behavior_call.Action(action).to_python(
            utils.PrefixOptions(), 'action_0', skills
        ),
        (
            'action_0 = skills.my_skill(my_double=1.1, my_float=2.0, '
            'my_int32=1, my_int64=2, my_uint32=10, my_uint64=20, '
            "my_bool=True, my_string='foo', "
            'sub_message=skills["ai.intrinsic.my_skill"].message_classes'
            '["intrinsic_proto.test_data.SubMessage"]'
            "(name='bar'), my_repeated_doubles=[0.3, 0.4])"
        ),
    )

  def test_incomplete_abstract_class(self):
    """Tests incomplete actions are rejected."""

    class IncompleteAction(actions.ActionBase):
      # NOT defined: property proto
      pass

    with self.assertRaises(TypeError):
      _ = IncompleteAction()

  def test_require_equipment(self):
    proto = behavior_call_pb2.BehaviorCall(
        skill_id='ai.intrinsic.my_custom_action'
    )
    proto.equipment['robot'].handle = 'my_robot'

    action = behavior_call.Action(
        skill_id='ai.intrinsic.my_custom_action'
    ).require(robot='my_robot')
    self.assertEqual(action.proto, proto)


if __name__ == '__main__':
  absltest.main()
