# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.solutions.behavior_tree."""

import copy
from typing import Union, cast
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2
from google.protobuf import text_format
from intrinsic.executive.proto import any_with_assignments_pb2
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.executive.proto import proto_builder_pb2
from intrinsic.executive.proto import test_message_pb2
from intrinsic.executive.proto import world_query_pb2
from intrinsic.solutions import behavior_tree as bt
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import cel
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import proto_building
from intrinsic.solutions.internal import behavior_call
from intrinsic.solutions.testing import compare
from intrinsic.solutions.testing import skill_test_utils
from intrinsic.solutions.testing import test_skill_params_pb2
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_resources


def _create_test_decorator(
    cel_expression: str = 'foo',
) -> bt.Decorators:
  return bt.Decorators(condition=bt.Blackboard(cel_expression=cel_expression))


class BehaviorTreeBreakpointTypeTest(absltest.TestCase):
  """Tests functions of BehaviorTree.BreakpointType."""

  def test_from_proto(self):
    """Tests if proto values are correctly converted."""
    none_value = bt.BreakpointType.from_proto(None)
    self.assertIsNone(none_value)

    unspecified_value = bt.BreakpointType.from_proto(
        behavior_tree_pb2.BehaviorTree.Breakpoint.TYPE_UNSPECIFIED
    )
    self.assertIsNone(unspecified_value)

    before = bt.BreakpointType.from_proto(
        behavior_tree_pb2.BehaviorTree.Breakpoint.BEFORE
    )
    self.assertEqual(before, bt.BreakpointType.BEFORE)

    after = bt.BreakpointType.from_proto(
        behavior_tree_pb2.BehaviorTree.Breakpoint.AFTER
    )
    self.assertEqual(after, bt.BreakpointType.AFTER)


class BehaviorTreeMadeParametrizableTest(absltest.TestCase):
  """Test functions of BehaviorTrees initialized as PBTs."""

  def test_initialize_pbt_from_schema(self):
    bt1 = bt.BehaviorTree('test')

    proto_builder_stub: proto_builder_pb2.ProtoBuilderStub = mock.MagicMock()
    proto_builder = proto_building.ProtoBuilder(proto_builder_stub)

    # No need to fill these completely. This test only verifies the file
    # descriptor sets correctly arrive in the behavior tree proto.
    param_desc_set = descriptor_pb2.FileDescriptorSet(
        file=[descriptor_pb2.FileDescriptorProto(name='alpha_params.proto')]
    )
    return_value_desc_set = descriptor_pb2.FileDescriptorSet(
        file=[descriptor_pb2.FileDescriptorProto(name='alpha_return.proto')]
    )
    proto_builder_stub.Compile.side_effect = [
        proto_builder_pb2.ProtoCompileResponse(
            file_descriptor_set=param_desc_set
        ),
        proto_builder_pb2.ProtoCompileResponse(
            file_descriptor_set=return_value_desc_set
        ),
    ]

    parameter_proto_schema = """
          syntax = "proto3";

          message Parameters {
            string value = 1;
          }
        """
    return_value_proto_schema = """
          syntax = "proto3";

          package my_skill;

          message ReturnValue {
            repeated int32 bar = 1;
          }
        """

    bt1.initialize_pbt(
        skill_id='alpha',
        display_name='Alpha',
        parameter_proto_schema=parameter_proto_schema,
        return_value_proto_schema=return_value_proto_schema,
        proto_builder=proto_builder,
        parameter_message_full_name='Parameters',
        return_value_message_full_name='my_skill.ReturnValue',
    )

    self.assertEqual(
        proto_builder_stub.Compile.call_args_list,
        [
            mock.call(
                proto_builder_pb2.ProtoCompileRequest(
                    proto_filename='alpha_params.proto',
                    proto_schema=parameter_proto_schema,
                )
            ),
            mock.call(
                proto_builder_pb2.ProtoCompileRequest(
                    proto_filename='alpha_return.proto',
                    proto_schema=return_value_proto_schema,
                )
            ),
        ],
    )

    bt1.set_root(bt.Sequence())  # Empty root.
    bt1_proto = bt1.proto

    self.assertEqual(bt1_proto.description.display_name, 'Alpha')
    parameter_description = bt1_proto.description.parameter_description
    self.assertEqual(
        parameter_description.parameter_message_full_name,
        'Parameters',
    )
    self.assertEqual(
        parameter_description.parameter_descriptor_fileset, param_desc_set
    )
    return_value_description = bt1_proto.description.return_value_description
    self.assertEqual(
        return_value_description.return_value_message_full_name,
        'my_skill.ReturnValue',
    )
    self.assertEqual(
        return_value_description.descriptor_fileset,
        return_value_desc_set,
    )

  def test_initialize_pbt_with_known_types(self):
    bt1 = bt.BehaviorTree('test')

    bt1.initialize_pbt_with_protos(
        skill_id='alpha',
        display_name='Alpha',
        parameter_proto=test_message_pb2.TestMessage,
    )
    bt1.set_root(bt.Sequence())  # Empty root.
    bt1_proto = bt1.proto

    # Spot check a few attributes of the generated proto.
    self.assertEqual(bt1_proto.description.display_name, 'Alpha')
    parameter_description = bt1_proto.description.parameter_description
    self.assertEqual(
        parameter_description.parameter_message_full_name,
        'intrinsic_proto.executive.TestMessage',
    )
    self.assertLen(
        parameter_description.parameter_descriptor_fileset.file,
        3,
    )

  def test_initialize_pbt_with_custom_proto_dependencies(self):
    bt1 = bt.BehaviorTree('test')

    bt1.initialize_pbt_with_protos(
        skill_id='alpha',
        display_name='Alpha',
        parameter_proto=test_skill_params_pb2.CombinedSkillParams,
    )
    bt1.set_root(bt.Sequence())  # Empty root.
    bt1_proto = bt1.proto

    # Spot check a few attributes of the generated proto.
    self.assertEqual(bt1_proto.description.display_name, 'Alpha')
    parameter_description = bt1_proto.description.parameter_description
    self.assertEqual(
        parameter_description.parameter_message_full_name,
        'intrinsic_proto.test_data.CombinedSkillParams',
    )

    # Verify the transitive file descriptor set has been recovered in full
    expected_fd_set = skill_test_utils._get_test_message_file_descriptor_set(
        'testing/test_skill_params_proto_descriptors_transitive_set_sci.proto.bin'
    )
    descriptors_by_name = {
        file.name: file
        for file in parameter_description.parameter_descriptor_fileset.file
    }
    expected_descriptors_by_name = {
        file.name: file for file in expected_fd_set.file
    }
    self.assertEqual(
        expected_descriptors_by_name.keys(), descriptors_by_name.keys()
    )

    for fd_name, fd in descriptors_by_name.items():
      expected_fd = expected_descriptors_by_name[fd_name]
      compare.assertProto2Equal(
          self,
          fd,
          expected_fd,
          ignored_fields=[
              'source_code_info',
              'message_type.field.json_name',
              'message_type.nested_type.field.json_name',
              'message_type.nested_type.nested_type.field.json_name',
              'extension.json_name',
          ],
      )


class BehaviorTreeTest(parameterized.TestCase):
  """Tests the method functions of BehaviorTree."""

  def test_init(self):
    """Tests if BehaviorTree is correctly constructed."""
    bt1 = bt.BehaviorTree('my_bt')
    bt1.set_root(
        bt.Sequence([
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0')),
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-1')),
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-2')),
        ])
    )

    bt_pb1 = behavior_tree_pb2.BehaviorTree()
    bt_pb1.name = 'my_bt'
    bt_pb1.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )
    bt_pb1.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-1'
    )
    bt_pb1.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-2'
    )

    compare.assertProto2Equal(
        self, bt1.proto, bt_pb1, ignored_fields=['tree_id']
    )

    bt2 = bt.BehaviorTree(bt=bt1)
    compare.assertProto2Equal(self, bt1.proto, bt2.proto)

    bt3 = bt.BehaviorTree(bt=bt1.proto)
    compare.assertProto2Equal(self, bt1.proto, bt3.proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree is correctly constructed given an action."""
    bt1 = bt.BehaviorTree(
        'my_bt', behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )

    bt_pb1 = behavior_tree_pb2.BehaviorTree()
    bt_pb1.name = 'my_bt'
    bt_pb1.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    compare.assertProto2Equal(
        self, bt1.proto, bt_pb1, ignored_fields=['tree_id']
    )

    bt1.set_root(behavior_call.Action(skill_id='ai.intrinsic.skill-1'))
    bt_pb1.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'

    compare.assertProto2Equal(
        self, bt1.proto, bt_pb1, ignored_fields=['tree_id']
    )

  def test_init_both_root_and_proto_arguments_given(self):
    """Tests if BehaviorTree is correctly constructed."""
    some_proto = behavior_tree_pb2.BehaviorTree()
    some_proto.name = 'my_bt'
    some_proto.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )
    some_proto.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-1'
    )
    some_proto.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-2'
    )
    for child in some_proto.root.sequence.children:
      child.decorators.CopyFrom(
          behavior_tree_pb2.BehaviorTree.Node.Decorators()
      )
    some_proto.root.decorators.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Node.Decorators()
    )

    bt_instance = bt.BehaviorTree(
        root=bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0')),
        bt=some_proto,
    )

    bt_proto = behavior_tree_pb2.BehaviorTree()
    bt_proto.name = 'my_bt'
    bt_proto.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    compare.assertProto2Equal(
        self, bt_instance.proto, bt_proto, ignored_fields=['tree_id']
    )

  def test_str_conversion(self):
    """Tests if behavior tree conversion to a string works."""
    my_bt = bt.BehaviorTree('my_bt')
    self.assertEqual(str(my_bt), 'BehaviorTree(name="my_bt", root=None)')
    action = behavior_call.Action(skill_id='say').require(device='SomeSpeaker')
    my_bt.set_root(bt.Task(action))
    self.assertEqual(
        str(my_bt),
        'BehaviorTree(name="my_bt",'
        ' root=Task(action=behavior_call.Action(skill_id="say")))',
    )
    my_bt = bt.BehaviorTree(root=bt.Task(action))
    self.assertEqual(
        str(my_bt),
        'BehaviorTree(root=Task(action=behavior_call.Action(skill_id="say")))',
    )

  def test_to_proto_required_root_attribute(self):
    """Tests if conversion to a proto fails when the root node is None."""
    my_bt = bt.BehaviorTree()
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      my_bt.proto  # pylint: disable=pointless-statement

  def test_to_proto_with_default_behavior_tree_name(self):
    """Tests if conversion to a proto succeeds when name is set to default."""
    my_bt = bt.BehaviorTree(
        root=bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    )
    my_proto = behavior_tree_pb2.BehaviorTree()
    my_proto.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    compare.assertProto2Equal(
        self, my_bt.proto, my_proto, ignored_fields=['tree_id', 'root.id']
    )

  def test_generates_tree_id(self):
    """Tests if behavior tree generate_and_set_unique_id generates a tree_id."""
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
        )
    )
    expected_id = my_bt.generate_and_set_unique_id()

    self.assertIsNotNone(my_bt.tree_id)
    self.assertNotEqual(my_bt.tree_id, '')
    self.assertEqual(my_bt.tree_id, expected_id)

  def test_to_proto_and_from_proto(self):
    """Tests if behavior tree conversion to/from proto representation works."""
    my_bt = bt.BehaviorTree('my_bt')

    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
        )
    )

    my_proto = behavior_tree_pb2.BehaviorTree()
    my_proto.name = 'my_bt'
    my_proto.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )

    compare.assertProto2Equal(
        self,
        my_bt.proto,
        my_proto,
        ignored_fields=['tree_id', 'root.id', 'root.sequence.children.id'],
    )
    compare.assertProto2Equal(
        self,
        bt.BehaviorTree.create_from_proto(my_proto).proto,
        my_proto,
        ignored_fields=['tree_id', 'root.id', 'root.sequence.children.id'],
    )

  def test_to_proto_and_from_proto_retains_ids(self):
    """Tests if behavior tree conversion to/from proto respects ids."""
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.tree_id = 'custom_tree_id'
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
        )
    )
    my_bt.root.node_id = 42
    my_bt.root.children[0].node_id = 43

    my_proto = behavior_tree_pb2.BehaviorTree(
        name='my_bt', tree_id='custom_tree_id'
    )
    my_proto.root.sequence.children.add().task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )
    my_proto.root.id = 42
    my_proto.root.sequence.children[0].id = 43

    compare.assertProto2Equal(self, my_bt.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.BehaviorTree.create_from_proto(my_proto).proto, my_proto
    )

  def test_validate_accepts_nested_same_node_ids_across_subtrees(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
        )
    )
    my_bt.tree_id = 'tree_id'
    my_bt.root.node_id = 1
    my_bt.root.children[0].behavior_tree.tree_id = 'sub_tree_id'
    my_bt.root.children[0].node_id = 2
    my_bt.root.children[0].behavior_tree.root.node_id = 1
    my_bt.root.children[1].behavior_tree.tree_id = 'other_sub_tree_id'
    my_bt.root.children[1].node_id = 3
    my_bt.root.children[1].behavior_tree.root.node_id = 1

    my_bt.validate_id_uniqueness()

  def test_validate_accepts_nested_same_node_ids_across_subtree_conditions(
      self,
  ):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Fail(name='root').set_decorators(
            bt.Decorators(
                condition=bt.SubTreeCondition(
                    tree=bt.BehaviorTree(
                        name='subtree_condition_tree',
                        root=bt.Fail(name='subtree_condition_root'),
                    )
                )
            )
        )
    )
    my_bt.root.node_id = 1
    my_bt.root.decorators.condition.tree.root.node_id = 1

    my_bt.validate_id_uniqueness()

  def test_validate_accepts_unset_node_and_tree_ids(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
        )
    )

    my_bt.validate_id_uniqueness()

  def test_validate_accepts_generated_node_and_tree_ids(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    )
                )
            ),
        )
    )
    my_bt.generate_and_set_unique_id()
    my_bt.root.generate_and_set_unique_id()
    my_bt.root.children[0].behavior_tree.generate_and_set_unique_id()
    my_bt.root.children[0].generate_and_set_unique_id()
    my_bt.root.children[0].behavior_tree.root.generate_and_set_unique_id()
    my_bt.root.children[1].behavior_tree.generate_and_set_unique_id()
    my_bt.root.children[1].generate_and_set_unique_id()
    my_bt.root.children[1].behavior_tree.root.generate_and_set_unique_id()

    my_bt.validate_id_uniqueness()

  def test_validate_detects_tree_ids(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    name='other_tree',
                    root=bt.Task(
                        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
                    ),
                )
            )
        )
    )
    my_bt.tree_id = 'tree_id'
    my_bt.root.children[0].behavior_tree.tree_id = 'tree_id'

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*contains 2 trees with id "tree_id".*my_bt.*other_tree.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_validate_detects_node_ids(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence(name='root_node').set_children(
            bt.Task(
                name='child_node',
                action=behavior_call.Action(skill_id='ai.intrinsic.skill-0'),
            )
        )
    )
    my_bt.root.node_id = 1
    my_bt.root.children[0].node_id = 1

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*contains 2 nodes with id 1.*root_node.*child_node.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_validate_detects_within_subtrees(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.SubTree(
            behavior_tree=bt.BehaviorTree(
                root=bt.Sequence(name='subtree_sequence').set_children(
                    bt.Fail(name='subtree_child0'),
                    bt.Fail(name='subtree_child1'),
                )
            )
        )
    )
    my_bt.root.node_id = 1  # setting this is not a violation
    my_bt.root.behavior_tree.root.children[0].node_id = 1
    my_bt.root.behavior_tree.root.children[1].node_id = 1

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*contains 2 nodes with id 1.*subtree_child0.*subtree_child1.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_validate_detects_within_subtree_conditions(
      self,
  ):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Fail(name='root').set_decorators(
            bt.Decorators(
                condition=bt.SubTreeCondition(
                    tree=bt.BehaviorTree(
                        name='subtree_condition_tree',
                        root=bt.Sequence(name='subtree_sequence').set_children(
                            bt.Fail(name='subtree_child0'),
                            bt.Fail(name='subtree_child1'),
                        ),
                    )
                )
            )
        )
    )
    my_bt.root.node_id = 1  # setting this is not a violation
    my_bt.root.decorators.condition.tree.root.children[0].node_id = 1
    my_bt.root.decorators.condition.tree.root.children[1].node_id = 1

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*contains 2 nodes with id 1.*subtree_child0.*subtree_child1.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_validate_detects_accidental_violation(self):
    my_bt = bt.BehaviorTree('my_bt')
    move_home = bt.Fail(name='move_home')
    pick_up = bt.Fail(name='pick_up')
    place = bt.Fail(name='place')
    my_bt.set_root(
        bt.Sequence(name='subtree_sequence').set_children(
            move_home, pick_up, move_home, place
        )
    )
    # This changes both move_home nodes as they are the same object
    move_home.generate_and_set_unique_id()

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*contains 2 nodes with id .*move_home.*move_home.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_validates_multiple_node_and_tree_ids(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    name='violates_4_and_2_times',
                    root=bt.Sequence(
                        children=[
                            bt.Fail(name='4x_0'),
                            bt.Fail(name='4x_1'),
                            bt.Fail(name='2x_0'),
                            bt.Fail(name='ok'),
                            bt.Fail(name='4x_2'),
                            bt.Fail(name='2x_1'),
                            bt.Fail(name='4x_3'),
                            bt.SubTree(
                                behavior_tree=bt.BehaviorTree(
                                    name='sub_sub_tree0', root=bt.Fail()
                                )
                            ),
                        ]
                    ),
                )
            ),
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    name='violates_2_times',
                    root=bt.Sequence(
                        children=[
                            bt.Fail(name='2x_0'),
                            bt.Fail(name='ok'),
                            bt.Fail(name='2x_1'),
                            bt.Fail(name='ok'),
                            bt.SubTree(
                                behavior_tree=bt.BehaviorTree(
                                    name='sub_sub_tree1', root=bt.Fail()
                                )
                            ),
                        ]
                    ),
                )
            ),
            bt.SubTree(
                behavior_tree=bt.BehaviorTree(
                    name='consistent',
                    root=bt.Sequence(
                        children=[
                            bt.Fail(name='consistent_0'),
                            bt.Fail(name='consistent_1'),
                            bt.Fail(name='consistent_2'),
                            bt.SubTree(
                                behavior_tree=bt.BehaviorTree(
                                    name='sub_sub_tree2', root=bt.Fail()
                                )
                            ),
                        ]
                    ),
                )
            ),
        )
    )
    my_bt.tree_id = 'tree_id'
    my_bt.root.node_id = 1
    my_bt.root.children[0].behavior_tree.tree_id = 'tree_id_3x'
    my_bt.root.children[0].behavior_tree.root.children[
        7
    ].behavior_tree.tree_id = 'tree_id_3x'
    my_bt.root.children[1].behavior_tree.tree_id = 'tree_id_2x'
    my_bt.root.children[1].behavior_tree.root.children[
        4
    ].behavior_tree.tree_id = 'tree_id_3x'
    my_bt.root.children[2].behavior_tree.tree_id = 'tree_id_unique'
    my_bt.root.children[2].behavior_tree.root.children[
        3
    ].behavior_tree.tree_id = 'tree_id_2x'

    my_bt.root.children[0].node_id = 10
    my_bt.root.children[0].behavior_tree.root.node_id = 1
    my_bt.root.children[0].behavior_tree.root.children[0].node_id = 44
    my_bt.root.children[0].behavior_tree.root.children[1].node_id = 44
    my_bt.root.children[0].behavior_tree.root.children[2].node_id = 22
    my_bt.root.children[0].behavior_tree.root.children[3].node_id = 13
    my_bt.root.children[0].behavior_tree.root.children[4].node_id = 44
    my_bt.root.children[0].behavior_tree.root.children[5].node_id = 22
    my_bt.root.children[0].behavior_tree.root.children[6].node_id = 44
    my_bt.root.children[0].behavior_tree.root.children[7].node_id = 17
    my_bt.root.children[1].node_id = 11
    my_bt.root.children[1].behavior_tree.root.node_id = 1
    my_bt.root.children[1].behavior_tree.root.children[0].node_id = 44
    my_bt.root.children[1].behavior_tree.root.children[1].node_id = 11
    my_bt.root.children[1].behavior_tree.root.children[2].node_id = 44
    my_bt.root.children[1].behavior_tree.root.children[3].node_id = 13
    my_bt.root.children[1].behavior_tree.root.children[4].node_id = 14
    my_bt.root.children[2].node_id = 12
    my_bt.root.children[2].behavior_tree.root.node_id = 1
    my_bt.root.children[2].behavior_tree.root.children[0].node_id = 22
    my_bt.root.children[2].behavior_tree.root.children[1].node_id = 23
    my_bt.root.children[2].behavior_tree.root.children[2].node_id = 44
    my_bt.root.children[2].behavior_tree.root.children[3].node_id = 45

    with self.assertRaisesRegex(
        solutions_errors.InvalidArgumentError,
        """^.*violates uniqueness.*
.*violates_4_and_2_times.*contains 4 nodes with id 44.*4x_0.*4x_1.*4x_2.*4x_3.*
.*violates_4_and_2_times.*contains 2 nodes with id 22.*2x_0.*2x_1.*
.*violates_2_times.*contains 2 nodes with id 44.*2x_0.*2x_1.*
.*contains 3 trees with id "tree_id_3x".*violates_4_and_2_times.*sub_sub_tree0.*sub_sub_tree1.*
.*contains 2 trees with id "tree_id_2x".*violates_2_times.*sub_sub_tree2.*$""",
    ):
      my_bt.validate_id_uniqueness()

  def test_finds_node(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence(name='root_node').set_children(
            bt.Task(
                name='child_node',
                action=behavior_call.Action(skill_id='ai.intrinsic.skill-0'),
            )
        )
    )
    my_bt.tree_id = 'tree'
    my_bt.root.node_id = 1
    my_bt.root.children[0].node_id = 2

    self.assertEqual(my_bt.find_tree_and_node_id('root_node'), ('tree', 1))
    self.assertEqual(my_bt.find_tree_and_node_id('child_node'), ('tree', 2))
    self.assertEqual(my_bt.find_tree_and_node_ids('root_node'), [('tree', 1)])
    self.assertEqual(my_bt.find_tree_and_node_ids('child_node'), [('tree', 2)])

  def test_find_node_validates(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence(name='root_node').set_children(
            bt.Fail(name='child_node'),
            bt.Fail(name='duplicate'),
            bt.Fail(name='duplicate'),
        )
    )
    my_bt.tree_id = 'tree'
    my_bt.root.node_id = 1
    my_bt.root.children[1].node_id = 3
    my_bt.root.children[2].node_id = 4

    with self.assertRaises(solutions_errors.NotFoundError):
      my_bt.find_tree_and_node_id('unknown')
    self.assertEqual(my_bt.find_tree_and_node_ids('unknown'), [])

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      my_bt.find_tree_and_node_id('duplicate')
    self.assertEqual(
        my_bt.find_tree_and_node_ids('duplicate'), [('tree', 3), ('tree', 4)]
    )

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      my_bt.find_tree_and_node_id('child_node')
    self.assertEqual(
        my_bt.find_tree_and_node_ids('child_node'), [('tree', None)]
    )

  def test_dot_graph_empty_instance(self):
    """Tests if an empty behavior tree converts to a dot representation ok."""
    my_bt = bt.BehaviorTree()
    self.assertIsNotNone(my_bt.dot_graph())

  def test_dot_graph(self):
    """Tests if behavior tree conversion to a dot representation works."""
    my_bt = bt.BehaviorTree('my_bt')

    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
        )
    )

    dot_string = """digraph my_bt {
  graph [label=my_bt labeljust=l labelloc=t]
    subgraphcluster_ {
      graph[label="" labeljust=l labelloc=t]
      {
        sequence [label=sequence shape=cds]
        {
          task_0 [label="Skill ai.intrinsic.skill-0" shape=box]
        }
          sequence -> task_0 [label=""]
      }
    }
}"""

    self.assertEqual(
        ''.join(str(my_bt.dot_graph()).split()), ''.join(dot_string.split())
    )

  @parameterized.named_parameters(
      dict(
          testcase_name='BEFORE',
          breakpoint_type=bt.BreakpointType.BEFORE,
          expected_proto_enum=behavior_tree_pb2.BehaviorTree.Breakpoint.BEFORE,
      ),
      dict(
          testcase_name='AFTER',
          breakpoint_type=bt.BreakpointType.AFTER,
          expected_proto_enum=behavior_tree_pb2.BehaviorTree.Breakpoint.AFTER,
      ),
  )
  def test_breakpoints(self, breakpoint_type, expected_proto_enum):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(
                behavior_call.Action(skill_id='ai.intrinsic.skill-1')
            ).set_breakpoint(breakpoint_type),
        )
    )

    root = cast(bt.NodeWithChildren, my_bt.root)
    self.assertEqual(root.children[0].breakpoint, breakpoint_type)

    expected_proto = behavior_tree_pb2.BehaviorTree(name='my_bt')

    child = expected_proto.root.sequence.children.add()
    child.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'
    child.decorators.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Node.Decorators(
            breakpoint=expected_proto_enum
        )
    )

    compare.assertProto2Equal(
        self, my_bt.proto, expected_proto, ignored_fields=['tree_id']
    )

  def test_no_default_breakpoint(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-1'))
    )

    self.assertIsNone(my_bt.root.breakpoint)

  @parameterized.named_parameters(
      dict(
          testcase_name='BEFORE',
          breakpoint_type=bt.BreakpointType.BEFORE,
      ),
      dict(
          testcase_name='AFTER',
          breakpoint_type=bt.BreakpointType.AFTER,
      ),
  )
  def test_breakpoints_with_preexisting_decorator(self, breakpoint_type):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(
                behavior_call.Action(skill_id='ai.intrinsic.skill-1')
            ).set_decorators(bt.Decorators(condition=bt.Blackboard('true'))),
        )
    )

    root = cast(bt.NodeWithChildren, my_bt.root)

    self.assertIsNone(root.children[0].breakpoint)

    root.children[0].set_breakpoint(breakpoint_type)
    self.assertEqual(root.children[0].breakpoint, breakpoint_type)

  def test_disable_enable_node(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(
                behavior_call.Action(skill_id='ai.intrinsic.skill-1')
            ).disable_execution(),
        )
    )

    node_execution_settings = (
        behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings(
            mode=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.DISABLED
        )
    )
    node_execution_mode = bt.NodeExecutionMode.from_proto(
        node_execution_settings.mode
    )

    root = cast(bt.NodeWithChildren, my_bt.root)
    self.assertEqual(root.children[0].execution_mode, node_execution_mode)

    expected_proto = behavior_tree_pb2.BehaviorTree(name='my_bt')

    child = expected_proto.root.sequence.children.add()
    child.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'
    child.decorators.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Node.Decorators(
            execution_settings=node_execution_settings
        )
    )

    compare.assertProto2Equal(
        self, my_bt.proto, expected_proto, ignored_fields=['tree_id']
    )

    my_bt.root.children[0].enable_execution()

    child.decorators.CopyFrom(behavior_tree_pb2.BehaviorTree.Node.Decorators())
    compare.assertProto2Equal(
        self, my_bt.proto, expected_proto, ignored_fields=['tree_id']
    )

  def test_no_node_execution_mode(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-1'))
    )

    # By default, execution_settings are not set
    expected_proto = behavior_tree_pb2.BehaviorTree.Node()
    expected_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'
    compare.assertProto2Equal(
        self, my_bt.root.proto, expected_proto, ignored_fields=['id']
    )
    self.assertEqual(
        my_bt.root.execution_mode,
        bt.NodeExecutionMode.from_proto(
            behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.NORMAL
        ),
    )

  def test_disable_node_with_result_state(self):
    my_bt = bt.BehaviorTree('my_bt')
    my_bt.set_root(
        bt.Sequence().set_children(
            bt.Task(
                behavior_call.Action(skill_id='ai.intrinsic.skill-1')
            ).disable_execution(result_state=bt.DisabledResultState.FAILED),
        )
    )

    node_execution = behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings(
        mode=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.DISABLED,
        disabled_result_state=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.FAILED,
    )
    node_execution_mode = bt.NodeExecutionMode.from_proto(node_execution.mode)

    root = cast(bt.NodeWithChildren, my_bt.root)
    self.assertEqual(root.children[0].execution_mode, node_execution_mode)

    expected_proto = behavior_tree_pb2.BehaviorTree(name='my_bt')

    child = expected_proto.root.sequence.children.add()
    child.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'
    child.decorators.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Node.Decorators(
            execution_settings=node_execution
        )
    )

    compare.assertProto2Equal(
        self, my_bt.proto, expected_proto, ignored_fields=['tree_id']
    )


class BehaviorTreeVisitorTest(absltest.TestCase):
  """Tests the visitor function for BehaviorTrees."""

  def setUp(self):
    super().setUp()
    self.visited_names = []
    self.visited_trees = []

  def visit_callback(
      self,
      containing_tree: bt.BehaviorTree,
      tree_object: Union[bt.BehaviorTree, bt.Node, bt.Condition],
  ) -> None:
    self.visited_trees.append(containing_tree.name)
    if isinstance(tree_object, bt.BehaviorTree | bt.Node):
      self.visited_names.append(tree_object.name)
    elif isinstance(tree_object, bt.Blackboard):
      self.visited_names.append(tree_object.cel_expression)
    elif isinstance(tree_object, bt.Condition):
      self.visited_names.append(tree_object.__class__.__name__)
    else:
      raise TypeError(f'Did not expect a {tree_object.__class__.__name__}')

  def test_visits_simple_tree(self):
    """Tests if a node in a simple tree is visited."""
    my_bt = bt.BehaviorTree(name='my_bt')
    my_bt.set_root(
        bt.Sequence(name='seq').set_children(
            bt.Task(
                name='task',
                action=behavior_call.Action(skill_id='ai.intrinsic.skill-1'),
            )
        )
    )

    my_bt.visit(self.visit_callback)
    self.assertEqual(self.visited_names, ['my_bt', 'seq', 'task'])

  def test_visits_all_tree(self):
    """Test if a tree with all node types is visited recursively."""
    my_bt = bt.BehaviorTree(name='all_tree')
    my_bt.set_root(
        bt.Sequence(name='main_sequence').set_children(
            bt.Task(
                name='task',
                action=behavior_call.Action(skill_id='ai.intrinsic.skill-1'),
            ),
            bt.SubTree(
                name='subtree_node',
                behavior_tree=bt.BehaviorTree(
                    name='subtree_tree', root=bt.Fail(name='subtree_root')
                ),
            ),
            bt.Fail(name='fail'),
            bt.Sequence(
                name='sequence',
                children=[
                    bt.Fail(name='sequence_child0'),
                    bt.Fail(name='sequence_child1'),
                ],
            ),
            bt.Parallel(
                name='parallel',
                children=[
                    bt.Fail(name='parallel_child0'),
                    bt.Fail(name='parallel_child1'),
                ],
            ),
            bt.Selector(
                name='selector',
                children=[
                    bt.Fail(name='selector_child0'),
                    bt.Fail(name='selector_child1'),
                ],
            ),
            bt.Retry(
                name='retry',
                child=bt.Fail(name='retry_child'),
                recovery=bt.Fail(name='retry_recovery'),
            ),
            bt.Fallback(
                name='fallback',
                children=[
                    bt.Fail(name='fallback_child0'),
                    bt.Fail(name='fallback_child1'),
                ],
            ),
            bt.Loop(
                name='loop',
                while_condition=bt.Blackboard(cel_expression='loop_condition'),
                do_child=bt.Fail(name='do_child'),
            ),
            bt.Branch(
                name='branch',
                if_condition=bt.Blackboard(cel_expression='branch_condition'),
                then_child=bt.Fail(name='branch_then'),
                else_child=bt.Fail(name='branch_else'),
            ),
            bt.Data(name='data'),
            bt.Debug(name='debug'),
        )
    )

    my_bt.visit(self.visit_callback)
    self.assertEqual(
        self.visited_names,
        [
            'all_tree',
            'main_sequence',
            'task',
            'subtree_node',
            'subtree_tree',
            'subtree_root',
            'fail',
            'sequence',
            'sequence_child0',
            'sequence_child1',
            'parallel',
            'parallel_child0',
            'parallel_child1',
            'selector',
            'selector_child0',
            'selector_child1',
            'retry',
            'retry_child',
            'retry_recovery',
            'fallback',
            'fallback_child0',
            'fallback_child1',
            'loop',
            'loop_condition',
            'do_child',
            'branch',
            'branch_condition',
            'branch_then',
            'branch_else',
            'data',
            'debug',
        ],
    )

  def test_visits_containing_tree(self):
    """Test if the containing_tree is correctly set."""
    my_bt = bt.BehaviorTree(name='all_tree')
    my_bt.set_root(
        bt.Sequence(name='main_sequence').set_children(
            bt.SubTree(
                name='subtree_node',
                behavior_tree=bt.BehaviorTree(
                    name='subtree_tree', root=bt.Fail(name='subtree_root')
                ),
            ),
            bt.Loop(
                name='loop',
                while_condition=bt.SubTreeCondition(
                    tree=bt.BehaviorTree(
                        name='loop_condition_subtree',
                        root=bt.Fail(name='loop_condition_subtree_root'),
                    )
                ),
                do_child=bt.Fail(name='do_child'),
            ),
        )
    )

    my_bt.visit(self.visit_callback)
    self.assertEqual(
        self.visited_names,
        [
            'all_tree',
            'main_sequence',
            'subtree_node',
            'subtree_tree',
            'subtree_root',
            'loop',
            'SubTreeCondition',
            'loop_condition_subtree',
            'loop_condition_subtree_root',
            'do_child',
        ],
    )
    self.assertEqual(
        self.visited_trees,
        [
            'all_tree',
            'all_tree',
            'all_tree',
            'subtree_tree',
            'subtree_tree',
            'all_tree',
            'all_tree',
            'loop_condition_subtree',
            'loop_condition_subtree',
            'all_tree',
        ],
    )

  def test_visits_all_decorators(self):
    """Test if all node types visit their decorators."""
    my_bt = bt.BehaviorTree(name='all_tree')
    my_bt.set_root(
        bt.Sequence(name='main_sequence').set_children(
            bt.Task(
                name='task',
                action=behavior_call.Action(skill_id='ai.intrinsic.skill-1'),
            ),
            bt.SubTree(name='subtree'),
            bt.Fail(name='fail'),
            bt.Sequence(name='sequence'),
            bt.Parallel(name='parallel'),
            bt.Selector(name='selector'),
            bt.Retry(name='retry'),
            bt.Fallback(name='fallback'),
            bt.Loop(name='loop'),
            bt.Branch(name='branch'),
            bt.Data(name='data'),
        )
    )
    for num, child in enumerate(my_bt.root.children):
      child.set_decorators(
          bt.Decorators(
              condition=bt.Blackboard(cel_expression=f'decorator{num}')
          )
      )

    my_bt.visit(self.visit_callback)
    self.assertEqual(
        self.visited_names,
        [
            'all_tree',
            'main_sequence',
            'decorator0',
            'task',
            'decorator1',
            'subtree',
            'decorator2',
            'fail',
            'decorator3',
            'sequence',
            'decorator4',
            'parallel',
            'decorator5',
            'selector',
            'decorator6',
            'retry',
            'decorator7',
            'fallback',
            'decorator8',
            'loop',
            'decorator9',
            'branch',
            'decorator10',
            'data',
        ],
    )

  def test_visits_condition_tree(self):
    """Test if a tree visits conditions recursively."""
    my_cond = bt.AllOf(
        conditions=[
            bt.AnyOf(
                conditions=[
                    bt.Blackboard(cel_expression='allof_anyof0'),
                    bt.Blackboard(cel_expression='allof_anyof1'),
                ]
            ),
            bt.Blackboard(cel_expression='allof_blackboard'),
            bt.Not(condition=bt.Blackboard(cel_expression='allof_not')),
            bt.SubTreeCondition(
                tree=bt.BehaviorTree(
                    name='allof_subtree',
                    root=bt.Fail(name='allof_subtree_root'),
                )
            ),
        ]
    )

    def rename_cond(cond: bt.Condition, prefix: str) -> None:
      cond.conditions[0].conditions[0].cel_expression = (
          cond.conditions[0]
          .conditions[0]
          .cel_expression.replace('allof', f'{prefix}_allof')
      )
      cond.conditions[0].conditions[1].cel_expression = (
          cond.conditions[0]
          .conditions[1]
          .cel_expression.replace('allof', f'{prefix}_allof')
      )
      cond.conditions[1].cel_expression = cond.conditions[
          1
      ].cel_expression.replace('allof', f'{prefix}_allof')
      cond.conditions[2].condition.cel_expression = cond.conditions[
          2
      ].condition.cel_expression.replace('allof', f'{prefix}_allof')
      cond.conditions[3].tree.name = cond.conditions[3].tree.name.replace(
          'allof', f'{prefix}_allof'
      )
      cond.conditions[3].tree.root.name = cond.conditions[
          3
      ].tree.root.name.replace('allof', f'{prefix}_allof')

    my_while = copy.deepcopy(my_cond)
    rename_cond(my_while, 'while')
    my_branch = copy.deepcopy(my_cond)
    rename_cond(my_branch, 'branch')
    my_decorator_cond = copy.deepcopy(my_cond)
    rename_cond(my_decorator_cond, 'decorator')
    my_nested_decorator_cond = copy.deepcopy(my_cond)
    rename_cond(my_nested_decorator_cond, 'nested_decorator')
    # The root node of the subtree condition of my_decorator has another
    # decorator condition
    my_decorator_cond.conditions[3].tree.root.set_decorators(
        bt.Decorators(condition=my_nested_decorator_cond)
    )

    my_bt = bt.BehaviorTree(name='all_tree')
    my_bt.set_root(
        bt.Sequence(name='main_sequence').set_children(
            bt.Fail(name='fail_with_decorator'),
            bt.Loop(
                name='loop',
                while_condition=my_while,
                do_child=bt.Fail(name='do_child'),
            ),
            bt.Branch(
                name='branch',
                if_condition=my_branch,
                then_child=bt.Fail(name='branch_then'),
                else_child=bt.Fail(name='branch_else'),
            ),
        )
    )
    my_bt.root.children[0].set_decorators(
        bt.Decorators(condition=my_decorator_cond)
    )

    my_bt.visit(self.visit_callback)
    self.assertEqual(
        self.visited_names,
        [
            'all_tree',
            'main_sequence',
            'AllOf',
            'AnyOf',
            'decorator_allof_anyof0',
            'decorator_allof_anyof1',
            'decorator_allof_blackboard',
            'Not',
            'decorator_allof_not',
            'SubTreeCondition',
            'decorator_allof_subtree',
            'AllOf',
            'AnyOf',
            'nested_decorator_allof_anyof0',
            'nested_decorator_allof_anyof1',
            'nested_decorator_allof_blackboard',
            'Not',
            'nested_decorator_allof_not',
            'SubTreeCondition',
            'nested_decorator_allof_subtree',
            'nested_decorator_allof_subtree_root',
            'decorator_allof_subtree_root',
            'fail_with_decorator',
            'loop',
            'AllOf',
            'AnyOf',
            'while_allof_anyof0',
            'while_allof_anyof1',
            'while_allof_blackboard',
            'Not',
            'while_allof_not',
            'SubTreeCondition',
            'while_allof_subtree',
            'while_allof_subtree_root',
            'do_child',
            'branch',
            'AllOf',
            'AnyOf',
            'branch_allof_anyof0',
            'branch_allof_anyof1',
            'branch_allof_blackboard',
            'Not',
            'branch_allof_not',
            'SubTreeCondition',
            'branch_allof_subtree',
            'branch_allof_subtree_root',
            'branch_then',
            'branch_else',
        ],
    )


class BehaviorTreeTaskTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Task."""

  def test_init(self):
    """Tests if BehaviorTree.Task is correctly constructed."""
    node = bt.Task(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0'), name='skill 0'
    )
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='skill 0')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    self.assertEqual(
        str(node),
        'Task(action=behavior_call.Action(skill_id="ai.intrinsic.skill-0"))',
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Task(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0'), name='foo'
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_to_proto_and_from_proto_call_behavior(self):
    """Tests if conversion to and from a proto representation works.

    This tests the specific case of using the call_behavior oneof option.
    """
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(id=42)
    my_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Task(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0'), name='foo'
    )

    dot_string = """digraph {
  task [label="foo (ai.intrinsic.skill-0)" shape=box]
}"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'task')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )


class BehaviorTreeSubTreeTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.SubTree."""

  def test_init(self):
    """Tests if BehaviorTree.SubTree is correctly constructed."""
    node = bt.SubTree()
    node.set_behavior_tree(
        bt.BehaviorTree(
            'some_sub_tree',
            bt.Task(behavior_call.Action(skill_id='some_skill')),
        )
    )
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sub_tree.tree.name = 'some_sub_tree'
    node_proto.sub_tree.tree.root.task.call_behavior.skill_id = 'some_skill'
    compare.assertProto2Equal(
        self, node.proto, node_proto, ignored_fields=['sub_tree.tree.tree_id']
    )

  def test_init_name(self):
    """Tests if name is correctly set during construction."""
    subtree_from_behavior_tree = bt.SubTree(
        bt.BehaviorTree(
            'some_sub_tree',
            bt.Task(behavior_call.Action(skill_id='some_skill')),
        ),
        'some name',
    )
    subtree_from_node = bt.SubTree(
        bt.Task(behavior_call.Action(skill_id='some_skill')),
        'some name',
    )

    self.assertEqual(subtree_from_behavior_tree.name, 'some name')
    self.assertEqual(subtree_from_node.name, 'some name')

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.SubTree()
    self.assertEqual(str(node), 'SubTree()')
    node.set_behavior_tree(
        bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )
    self.assertEqual(
        str(node),
        'SubTree(behavior_tree=BehaviorTree(name="some_sub_tree",'
        ' root=Task(action=behavior_call.Action(skill_id="some_skill"))))',
    )

  def test_to_proto_with_empty_root_fails(self):
    """Tests if converting a SubTree node without a root to a proto fails."""
    node = bt.SubTree()
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      node.proto  # pylint: disable=pointless-statement

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.SubTree()
    node.set_behavior_tree(
        bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sub_tree.tree.name = 'some_sub_tree'
    node_proto.sub_tree.tree.root.task.call_behavior.skill_id = 'some_skill'

    compare.assertProto2Equal(
        self, node.proto, node_proto, ignored_fields=['sub_tree.tree.tree_id']
    )
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
        ignored_fields=['sub_tree.tree.tree_id'],
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(
        self, node.proto, node_proto, ignored_fields=['sub_tree.tree.tree_id']
    )
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
        ignored_fields=['sub_tree.tree.tree_id'],
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.SubTree(
        behavior_tree=bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.SubTree(
        behavior_tree=bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.SubTree(
        behavior_tree=bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(
        id=42,
        sub_tree=behavior_tree_pb2.BehaviorTree.SubtreeNode(
            tree=behavior_tree_pb2.BehaviorTree(
                name='some_sub_tree',
                root=behavior_tree_pb2.BehaviorTree.Node(
                    task=behavior_tree_pb2.BehaviorTree.TaskNode()
                ),
            )
        ),
    )
    my_proto.sub_tree.tree.root.task.call_behavior.skill_id = 'some_skill'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty_instance(self):
    """Tests if the conversion of empty node to a dot representation works."""
    node = bt.SubTree()

    dot_string = """digraph{sub_tree [label=sub_tree shape=point]}"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'sub_tree')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if non-empty node conversion to a dot representation works."""
    node = bt.SubTree()
    node.set_behavior_tree(
        bt.BehaviorTree(
            name='some_sub_tree',
            root=behavior_call.Action(skill_id='some_skill'),
        )
    )

    dot_string = """digraph cluster_some_sub_tree {
  graph [label=some_sub_tree labeljust=l labelloc=t]
  {
    task_0 [label="Skill some_skill" shape=box]
  }
}"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'task_0')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )


class BehaviorTreeFailTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Fail."""

  def test_init(self):
    """Tests if BehaviorTree.Fail is correctly constructed."""
    node = bt.Fail('some_failure_message', name='expected failure')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='expected failure')
    node_proto.fail.failure_message = 'some_failure_message'
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Fail()
    self.assertEqual(str(node), 'Fail()')
    node = bt.Fail('some_failure_message')
    self.assertEqual(str(node), 'Fail(failure_message="some_failure_message")')
    node = bt.Fail(name='my_fail', failure_message='some_failure_message')
    self.assertEqual(
        str(node),
        'Fail(name="my_fail", failure_message="some_failure_message")',
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Fail('some_failure_message', name='expected failure')

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='expected failure')
    node_proto.fail.failure_message = 'some_failure_message'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Fail()
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Fail()
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Fail('failed')
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(id=42)
    my_proto.fail.failure_message = 'failed'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Fail('some_failure_message')

    dot_string = """digraph {
  fail [label=fail shape=box]
}"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'fail')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )


class BehaviorTreeDebugTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Debug."""

  def test_init(self):
    """Tests if BehaviorTree.Debug is correctly constructed."""
    node = bt.Debug(fail_on_resume=True, name='pause')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='pause')
    node_proto.debug.suspend.fail_on_resume = True
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Debug()
    self.assertEqual(str(node), 'Debug()')
    node = bt.Debug(True)
    self.assertEqual(str(node), 'Debug(fail_on_resume=True)')
    node = bt.Debug(name='my_debug', fail_on_resume=True)
    self.assertEqual(
        str(node),
        'Debug(name="my_debug", fail_on_resume=True)',
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Debug(True, name='pause')

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='pause')
    node_proto.debug.suspend.fail_on_resume = True

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Debug()
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Debug()
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Debug()
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(id=42)
    my_proto.debug.suspend.fail_on_resume = False

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Debug()

    dot_string = """digraph {
  debug [label=debug shape=box]
}"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'debug')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )


class BehaviorTreeSequenceTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Sequence."""

  def test_init(self):
    """Tests if BehaviorTree.Sequence is correctly constructed."""
    node = bt.Sequence(name='foo')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    compare.assertProto2Equal(self, node.proto, node_proto)

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree.Sequence is correctly constructed from actions."""
    node = bt.Sequence([behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'

    compare.assertProto2Equal(self, node.proto, node_proto)

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_1')),
        bt.Task(behavior_call.Action(skill_id='skill_2')),
    )

    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_2'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Sequence()
    self.assertEqual(str(node), 'Sequence(children=[])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(
        str(node),
        'Sequence(children=[Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' Task(action=behavior_call.Action(skill_id="skill_1"))])',
    )

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty sequence node to a proto works."""
    node = bt.Sequence()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Sequence(name='foo')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Sequence(name='foo')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Sequence(name='foo')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Sequence(name='foo')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'
    my_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_create_from_proto_prevents_accidental_call_from_subclass(self):
    """create_from_proto should only be called on the base Node."""
    node = bt.Sequence(name='foo')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    with self.assertRaises(TypeError):
      bt.Sequence.create_from_proto(node.proto)
    bt.Node.create_from_proto(node.proto)

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Sequence()

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t] {
        sequence [label=sequence shape=cds]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'sequence')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Sequence()
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    dot_string = """digraph cluster_ {
      graph[label="" labeljust=l labelloc=t] {
        sequence [label=sequence shape=cds]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        sequence -> task_0 [label=""]
        {
          task_1 [label="Skill skill_1" shape=box]
        }
        sequence -> task_1 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeParallelTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Parallel."""

  def test_init(self):
    """Tests if BehaviorTree.Parallel is correctly constructed."""
    node = bt.Parallel(name='bar')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node.failure_behavior = node.FailureBehavior.WAIT_FOR_REMAINING_CHILDREN

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='bar')
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.parallel.failure_behavior = (
        node_proto.parallel.FailureBehavior.WAIT_FOR_REMAINING_CHILDREN
    )
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_with_actions(self):
    """Tests if BehaviorTree.Parallel is correctly constructed from actions."""
    node = bt.Parallel(children=[behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_0'
    compare.assertProto2Equal(self, node.proto, node_proto)

    node.set_children(
        behavior_call.Action(skill_id='skill_1'),
        behavior_call.Action(skill_id='skill_2'),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_2'

    node_proto.parallel.failure_behavior = (
        node_proto.parallel.FailureBehavior.DEFAULT
    )
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Parallel()
    self.assertEqual(str(node), 'Parallel(children=[])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(
        str(node),
        'Parallel(children=[Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' Task(action=behavior_call.Action(skill_id="skill_1"))])',
    )

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty parallel node to a proto works."""
    node = bt.Parallel()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.parallel.CopyFrom(behavior_tree_pb2.BehaviorTree.ParallelNode())
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Parallel(name='foo')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Parallel(name='foo')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Parallel(name='foo')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Parallel(name='foo')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_0'
    my_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_proto_with_unspecified_failure_behavior_resolves_to_default(self):
    node: bt.Parallel = bt.Node.create_from_proto(
        behavior_tree_pb2.BehaviorTree.Node(
            parallel=behavior_tree_pb2.BehaviorTree.ParallelNode()
        )
    )
    self.assertEqual(node.failure_behavior, node.FailureBehavior.DEFAULT)

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Parallel()

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t] {
        parallel [label=parallel shape=trapezium]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'parallel')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Parallel()
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t]  {
        parallel [label=parallel shape=trapezium]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        parallel -> task_0 [label=""]
        {
          task_1 [label="Skill skill_1" shape=box]
        }
        parallel -> task_1 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeSelectorTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Selector."""

  def test_init(self):
    """Tests if BehaviorTree.Selector is correctly constructed."""
    node = bt.Selector(name='bar')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='bar')
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_1'
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_with_actions(self):
    """Tests if BehaviorTree.Selector is correctly constructed from actions."""
    node = bt.Selector([behavior_call.Action(skill_id='skill_0')])
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_0'

    compare.assertProto2Equal(self, node.proto, node_proto)

    node.set_children(
        behavior_call.Action(skill_id='skill_1'),
        behavior_call.Action(skill_id='skill_2'),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_2'
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Selector()
    self.assertEqual(str(node), 'Selector(children=[])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(
        str(node),
        'Selector(children=[Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' Task(action=behavior_call.Action(skill_id="skill_1"))])',
    )

  def test_to_proto_empty_node(self):
    """Tests if empty node conversion to a proto representation works."""
    node = bt.Selector()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.CopyFrom(behavior_tree_pb2.BehaviorTree.SelectorNode())
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Selector(name='bar')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='bar')

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Selector(name='bar')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Selector(name='bar')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Selector(name='bar')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='bar', id=42)
    my_proto.selector.children.add().task.call_behavior.skill_id = 'skill_0'
    my_proto.selector.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Selector()

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t] {
        selector [label=selector shape=octagon]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'selector')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Selector()
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    dot_string = """digraph cluster_ {
      graph[label="" labeljust=l labelloc=t]  {
        selector [label=selector shape=octagon]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        selector -> task_0 [label=""]
        {
          task_1 [label="Skill skill_1" shape=box]
        }
        selector -> task_1 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeRetryTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Retry."""

  def test_init(self):
    """Tests if BehaviorTree.Retry is correctly constructed."""
    node = bt.Retry(2, name='foo')
    node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.retry.max_tries = 2
    node_proto.retry.child.task.call_behavior.skill_id = 'skill_0'
    node_proto.retry.retry_counter_blackboard_key = node.retry_counter

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_from_action(self):
    """Tests if BehaviorTree.Retry is correctly constructed from actions."""
    node = bt.Retry(2, behavior_call.Action(skill_id='skill_0'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.retry.max_tries = 2
    node_proto.retry.child.task.call_behavior.skill_id = 'skill_0'
    node_proto.retry.retry_counter_blackboard_key = node.retry_counter

    compare.assertProto2Equal(self, node.proto, node_proto)
    node.set_child(behavior_call.Action(skill_id='skill_1'))

    node_proto.retry.child.task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Retry()
    self.assertEqual(str(node), 'Retry(max_tries=0, child=None, recovery=None)')
    node.max_tries = 2
    node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    self.assertEqual(
        str(node),
        'Retry(max_tries=2,'
        ' child=Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' recovery=None)',
    )
    node.set_recovery(bt.Task(behavior_call.Action(skill_id='skill_1')))
    self.assertEqual(
        str(node),
        'Retry(max_tries=2,'
        ' child=Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' recovery=Task(action=behavior_call.Action(skill_id="skill_1")))',
    )

  def test_to_proto_empty_child(self):
    """Tests if converting a node without the child to a proto fails."""
    node = bt.Retry()
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      node.proto  # pylint: disable=pointless-statement

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Retry(2, name='foo')
    node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    node.set_recovery(bt.Task(behavior_call.Action(skill_id='skill_1')))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.retry.max_tries = 2
    node_proto.retry.child.task.call_behavior.skill_id = 'skill_0'
    node_proto.retry.recovery.task.call_behavior.skill_id = 'skill_1'
    node_proto.retry.retry_counter_blackboard_key = node.retry_counter

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Retry(2, name='foo')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Retry(2, name='foo')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Retry(2, name='foo')
    my_node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.retry.max_tries = 2
    my_proto.retry.child.task.call_behavior.skill_id = 'skill_0'
    my_proto.retry.retry_counter_blackboard_key = my_node.retry_counter

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Retry()

    dot_string = """digraphcluster_ {
      graph [label="" labeljust=l labelloc=t] {
        retry [label="retry0" shape=hexagon]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'retry')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Retry(2)
    node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    node.set_recovery(bt.Task(behavior_call.Action(skill_id='skill_1')))

    dot_string = """digraph cluster_ {
      graph [label="" labeljust=l labelloc=t] {
        retry [label="retry 2" shape=hexagon]
        {
          task_child [label="Skill skill_0" shape=box]
        }
        retry -> task_child [label=""]
        {
          task_recovery [label="Skill skill_1" shape=box]
        }
        retry -> task_recovery [label=Recovery]
      }
    }"""

    self.assertEqual(
        ' '.join(str(node.dot_graph()[0]).split()),
        ' '.join(dot_string.split()),
    )


class BehaviorTreeFallbackTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Fallback."""

  def test_init(self):
    """Tests if BehaviorTree.Fallback is correctly constructed."""
    node = bt.Fallback(name='foo')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_1'
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree.Fallback is correctly constructed from actions."""
    node = bt.Fallback([behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_0'

    compare.assertProto2Equal(self, node.proto, node_proto)

    node.set_children(
        behavior_call.Action(skill_id='skill_1'),
        behavior_call.Action(skill_id='skill_2'),
    )
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_2'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Fallback()
    self.assertEqual(str(node), 'Fallback(children=[])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(
        str(node),
        'Fallback(children=[Task(action=behavior_call.Action(skill_id="skill_0")),'
        ' Task(action=behavior_call.Action(skill_id="skill_1"))])',
    )

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty fallback node to a proto works."""
    node = bt.Fallback()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Fallback(name='foo')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Fallback(name='foo')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Fallback(name='foo')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Fallback(name='foo')
    my_node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_0'
    my_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Fallback()

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t] {
        fallback [label=fallback shape=octagon]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'fallback')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Fallback()
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )

    dot_string = """digraphcluster_ {
      graph[label="" labeljust=l labelloc=t] {
        fallback [label=fallback shape=octagon]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        fallback -> task_0 [label=""]
        {
          task_1 [label="Skill skill_1" shape=box]
        }
        fallback -> task_1 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeLoopTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Loop."""

  def test_init(self):
    """Tests if BehaviorTree.Loop is correctly constructed."""
    node = bt.Loop(max_times=2, name='foo')
    node.set_do_child(bt.Task(behavior_call.Action(skill_id='skill_0')))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.loop.max_times = 2
    node_proto.loop.do.task.call_behavior.skill_id = 'skill_0'
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_from_action(self):
    """Tests if BehaviorTree.Loop is correctly constructed from actions."""
    node = bt.Loop(
        max_times=2, do_child=behavior_call.Action(skill_id='skill_0')
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.loop.max_times = 2
    node_proto.loop.do.task.call_behavior.skill_id = 'skill_0'
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter

    compare.assertProto2Equal(self, node.proto, node_proto)
    node.set_do_child(behavior_call.Action(skill_id='skill_1'))

    node_proto.loop.do.task.call_behavior.skill_id = 'skill_1'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Loop()
    self.assertEqual(str(node), 'Loop(do_child=None)')
    node.max_times = 2
    node.set_do_child(behavior_call.Action(skill_id='skill_0'))
    node.set_while_condition(bt.Blackboard('foo'))
    self.assertEqual(
        str(node),
        'Loop(while_condition=Blackboard(foo), max_times=2, '
        'do_child=Task(action=behavior_call.Action(skill_id="skill_0")))',
    )

  def test_to_proto_empty_child(self):
    """Tests if converting a node without the do child to a proto fails."""
    node = bt.Loop()
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      node.proto  # pylint: disable=pointless-statement

  def test_construct_while_and_for_each_fails(self):
    """Tests that one cannot create a node that is both while and for_each."""
    # set for_each on while
    node = bt.Loop(do_child=bt.Fail())
    with self.assertRaises(solutions_errors.InvalidArgumentError):
      node.set_while_condition(
          bt.Blackboard('foo')
      ).set_for_each_generator_cel_expression('skill.result')
    node = bt.Loop(do_child=bt.Fail())
    with self.assertRaises(solutions_errors.InvalidArgumentError):
      msg = test_message_pb2.TestMessage()
      node.set_while_condition(bt.Blackboard('foo')).set_for_each_protos([msg])
    # set while on for_each
    node = bt.Loop(do_child=bt.Fail())
    with self.assertRaises(solutions_errors.InvalidArgumentError):
      node.set_for_each_generator_cel_expression(
          'skill.result'
      ).set_while_condition(bt.Blackboard('foo'))

  def test_construct_for_each_unique(self):
    """Tests that only one way to define a for_each node is used."""
    node = bt.Loop(do_child=bt.Fail())
    with self.assertRaises(solutions_errors.InvalidArgumentError):
      msg = test_message_pb2.TestMessage()
      node.set_for_each_generator_cel_expression(
          'skill.result'
      ).set_for_each_protos([msg])

  def test_construct_for_each_invalid_fails(self):
    """Tests that at least one way to define a for_each node is used."""
    node = bt.Loop(do_child=bt.Fail()).set_for_each_value_key(
        'i_want_to_be_for_each'
    )
    # Note: No method for generating for_each is set.
    with self.assertRaises(solutions_errors.InvalidArgumentError):
      node.proto  # pylint: disable=pointless-statement

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""

    node = bt.Loop(max_times=2, name='foo')
    node.set_do_child(behavior_call.Action(skill_id='skill_0'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.loop.max_times = 2
    node_proto.loop.do.task.call_behavior.skill_id = 'skill_0'
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
        ignored_fields=['loop.loop_counter_blackboard_key'],
    )

    node.set_while_condition(bt.Blackboard('foo'))
    condition = getattr(node_proto.loop, 'while')
    condition.CopyFrom(node.while_condition.proto)

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
        ignored_fields=['loop.loop_counter_blackboard_key'],
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
        ignored_fields=['loop.loop_counter_blackboard_key'],
    )

  def test_to_proto_and_from_proto_for_each(self):
    """Tests if conversion to and from a proto works for for_each nodes."""
    node = bt.Loop()
    node.set_do_child(bt.Fail()).set_for_each_generator_cel_expression(
        'skill.result.poses'
    )

    node_proto = text_format.Parse(
        """
    loop {
      do {
        fail {}
      }
      max_times: 0
      for_each {
        generator_cel_expression: "skill.result.poses"
      }
    }
    """,
        behavior_tree_pb2.BehaviorTree.Node(),
    )
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter
    node_proto.loop.for_each.value_blackboard_key = node.for_each_value_key

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    msg1 = test_message_pb2.TestMessage(int32_value=1)
    msg2 = test_message_pb2.TestMessage(int32_value=2)
    node = bt.Loop()
    node.set_do_child(bt.Fail()).set_for_each_protos([msg1, msg2])

    node_proto = text_format.Parse(
        """
    loop {
      do {
        fail {}
      }
      max_times: 0
      for_each {
        protos {
          items {
            [type.googleapis.com/intrinsic_proto.executive.TestMessage] {
              int32_value: 1
            }
          }
          items {
            [type.googleapis.com/intrinsic_proto.executive.TestMessage] {
              int32_value: 2
            }
          }
        }
      }
    }
    """,
        behavior_tree_pb2.BehaviorTree.Node(),
    )
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter
    node_proto.loop.for_each.value_blackboard_key = node.for_each_value_key

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_to_proto_and_from_proto_for_each_accepts_world_objects(self):
    """Tests if conversion from WorldObjects happens automatically."""
    stub = mock.MagicMock()
    w1 = object_world_resources.WorldObject(
        world_object=object_world_service_pb2.Object(
            name='n1',
            object_component=object_world_service_pb2.ObjectComponent(),
            name_is_global_alias=True,
            id='1',
        ),
        stub=stub,
    )
    w2 = object_world_resources.WorldObject(
        world_object=object_world_service_pb2.Object(
            name='n2',
            object_component=object_world_service_pb2.ObjectComponent(),
            name_is_global_alias=True,
            id='2',
        ),
        stub=stub,
    )
    w3 = object_world_resources.Frame(
        world_frame=object_world_service_pb2.Frame(
            name='n3',
            id='3',
        ),
        stub=stub,
    )

    node = bt.Loop()
    node.set_do_child(bt.Fail()).set_for_each_protos([w1, w2, w3])

    node_proto = text_format.Parse(
        """
    loop {
      do {
        fail {}
      }
      max_times: 0
      for_each {
        protos {
          items {
            [type.googleapis.com/intrinsic_proto.world.ObjectReference] {
              by_name {
                object_name: "n1"
              }
            }
          }
          items {
            [type.googleapis.com/intrinsic_proto.world.ObjectReference] {
              by_name {
                object_name: "n2"
              }
            }
          }
          items {
            [type.googleapis.com/intrinsic_proto.world.FrameReference] {
              id: "3"
              debug_hint: "Created from path world.n3"
            }
          }
        }
      }
    }
    """,
        behavior_tree_pb2.BehaviorTree.Node(),
    )
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter
    node_proto.loop.for_each.value_blackboard_key = node.for_each_value_key

    compare.assertProto2Equal(
        self,
        node.proto,
        node_proto,
    )
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Loop(max_times=2, name='foo')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Loop(max_times=2, name='foo')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Loop(max_times=2, name='foo')
    my_node.set_do_child(behavior_call.Action(skill_id='skill_0'))
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.loop.max_times = 2
    my_proto.loop.do.task.call_behavior.skill_id = 'skill_0'
    my_proto.loop.loop_counter_blackboard_key = my_node.loop_counter

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Loop()

    dot_string = """digraphcluster_ {
      graph [label="" labeljust=l labelloc=t] {
        loop [label=loop shape=hexagon]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'loop')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Loop(while_condition=bt.Blackboard('true'), max_times=2)
    node.set_do_child(behavior_call.Action(skill_id='skill_0'))

    dot_string = """digraphcluster_ {
      graph [label="" labeljust=l labelloc=t] {
        loop [label="loop 2 + while condition" shape=hexagon]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        loop -> task_0 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )

  def test_dot_graph_for_each(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Loop(
        for_each_generator_cel_expression='skill.result', max_times=2
    )
    node.set_do_child(behavior_call.Action(skill_id='skill_0'))

    dot_string = """digraphcluster_ {
      graph [label="" labeljust=l labelloc=t] {
        loop [label="loop 2 + for_each" shape=hexagon]
        {
          task_0 [label="Skill skill_0" shape=box]
        }
        loop -> task_0 [label=""]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeBranchTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Branch."""

  def test_init(self):
    """Tests if BehaviorTree.Branch is correctly constructed."""
    node = bt.Branch(name='foo')
    node.set_then_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    node.set_if_condition(bt.Blackboard('foo'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.branch.then.task.call_behavior.skill_id = 'skill_0'

    condition_proto = bt.Blackboard('foo').proto
    condition = getattr(node_proto.branch, 'if')
    condition.CopyFrom(condition_proto)

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_from_action(self):
    """Tests if BehaviorTree.Branch is correctly constructed from actions."""
    node = bt.Branch(else_child=behavior_call.Action(skill_id='skill_0'))
    node.set_if_condition(bt.Blackboard('bar'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node()

    else_proto = bt.Task(behavior_call.Action(skill_id='skill_0')).proto
    child = getattr(node_proto.branch, 'else')
    child.CopyFrom(else_proto)

    condition_proto = bt.Blackboard('bar').proto
    condition = getattr(node_proto.branch, 'if')
    condition.CopyFrom(condition_proto)

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Branch()
    self.assertEqual(str(node), 'Branch()')
    node.set_then_child(behavior_call.Action(skill_id='skill_0'))
    node.set_if_condition(bt.Blackboard('foo'))
    self.assertEqual(
        str(node),
        'Branch(if_condition=Blackboard(foo), then_child='
        'Task(action=behavior_call.Action(skill_id="skill_0")), )',
    )

    node.set_else_child(behavior_call.Action(skill_id='skill_1'))
    self.assertEqual(
        str(node),
        'Branch(if_condition=Blackboard(foo), then_child='
        'Task(action=behavior_call.Action(skill_id="skill_0")), else_child='
        'Task(action=behavior_call.Action(skill_id="skill_1")))',
    )

  def test_to_proto_no_then_or_else(self):
    """Tests if converting a node without a then or else to a proto fails."""
    node = bt.Branch()
    node.set_if_condition(bt.Blackboard('foo'))
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      node.proto  # pylint: disable=pointless-statement

  def test_to_proto_no_condition(self):
    """Tests if converting a node without a if_condition to a proto fails."""
    node = bt.Branch()
    node.set_then_child(behavior_call.Action(skill_id='skill_0'))
    with self.assertRaises(ValueError):
      # We disable the warning because this is statement is necessary as it will
      # raise the expected ValueError
      node.proto  # pylint: disable=pointless-statement

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Branch(name='foo')
    node.set_then_child(behavior_call.Action(skill_id='skill_0'))
    node.set_if_condition(bt.Blackboard('foo'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.branch.then.task.call_behavior.skill_id = 'skill_0'
    condition = getattr(node_proto.branch, 'if')
    condition.CopyFrom(bt.Blackboard('foo').proto)

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, node.proto, node_proto)
    compare.assertProto2Equal(
        self,
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Branch(name='foo')
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Branch(name='foo')
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Branch(name='foo')
    my_node.set_then_child(behavior_call.Action(skill_id='skill_0'))
    my_node.set_if_condition(bt.Blackboard('foo'))
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.branch.then.task.call_behavior.skill_id = 'skill_0'
    condition = getattr(my_proto.branch, 'if')
    condition.CopyFrom(bt.Blackboard('foo').proto)

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_dot_graph_empty_node(self):
    """Tests if empty node conversion to a dot representation works."""
    node = bt.Branch()

    dot_string = """digraphcluster_ {
      graph [label="" labeljust=l labelloc=t] {
        branch [label=branch shape=diamond]
      }
    }"""

    node_dot, node_root_name = node.dot_graph()
    self.assertEqual(node_root_name, 'branch')
    self.assertEqual(
        ''.join(str(node_dot).split()), ''.join(dot_string.split())
    )

  def test_dot_graph(self):
    """Tests if node conversion to a dot representation works."""
    node = bt.Branch()
    node.set_then_child(behavior_call.Action(skill_id='skill_0'))

    dot_string = """digraph cluster_ {
      graph [label="" labeljust=l labelloc=t] {
        branch [label=branch shape=diamond]
        {
          task_1 [label="Skill skill_0" shape=box]
        }
        branch -> task_1 [label=then]
      }
    }"""

    self.assertEqual(
        ''.join(str(node.dot_graph()[0]).split()), ''.join(dot_string.split())
    )


class BehaviorTreeDataTest(parameterized.TestCase):
  """Tests the method functions of BehaviorTree.Data."""

  def test_init_from_cel_expression(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node = bt.Data(name='foo')
    node.set_blackboard_key('bbfoo')
    node.set_operation(bt.Data.OperationType.CREATE_OR_UPDATE)
    node.set_cel_expression('bar')

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.create_or_update.cel_expression = 'bar'
    node_proto.data.create_or_update.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, node.proto, node_proto)

  @parameterized.named_parameters(
      dict(
          testcase_name='child_frames',
          query_field='child_frames_of',
      ),
      dict(
          testcase_name='child_objects',
          query_field='child_objects_of',
      ),
      dict(
          testcase_name='children_of',
          query_field='children_of',
      ),
  )
  def test_init_from_world_query(self, query_field):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.CREATE_OR_UPDATE,
        blackboard_key='bbfoo',
    )
    select_args = {
        query_field: object_world_refs_pb2.ObjectReference(
            by_name=object_world_refs_pb2.ObjectReferenceByName(
                object_name='bar'
            )
        )
    }
    world_query = (
        bt.WorldQuery()
        .select(**select_args)
        .filter(name_regex='xyz.*')
        .order(
            by=bt.WorldQuery.OrderCriterion.NAME,
            direction=bt.WorldQuery.OrderDirection.DESCENDING,
        )
    )
    node.set_world_query(world_query)

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    world_query_proto = world_query_pb2.WorldQuery()
    getattr(world_query_proto.select, query_field).by_name.object_name = 'bar'
    world_query_proto.filter.name_regex = 'xyz.*'
    world_query_proto.order.by = world_query_pb2.WorldQuery.Order.NAME
    world_query_proto.order.direction = (
        world_query_pb2.WorldQuery.Order.DESCENDING
    )
    node_proto.data.create_or_update.from_world.proto.Pack(world_query_proto)
    node_proto.data.create_or_update.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, node.proto, node_proto)

  @parameterized.named_parameters(
      dict(
          testcase_name='child_frames',
          query_field='child_frames_of',
      ),
      dict(
          testcase_name='child_objects',
          query_field='child_objects_of',
      ),
      dict(
          testcase_name='children_of',
          query_field='children_of',
      ),
  )
  def test_init_from_world_query_with_blackboard_values(self, query_field):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.CREATE_OR_UPDATE,
        blackboard_key='bbfoo',
    )
    select_args = {
        query_field: blackboard_value.BlackboardValue({}, 'bar', None, None)
    }
    world_query = (
        bt.WorldQuery()
        .select(**select_args)
        .filter(
            name_regex=blackboard_value.BlackboardValue(
                {}, 'name_key', None, None
            )
        )
        .order(
            by=bt.WorldQuery.OrderCriterion.NAME,
            direction=bt.WorldQuery.OrderDirection.DESCENDING,
        )
    )
    node.set_world_query(world_query)

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    world_query_proto = world_query_pb2.WorldQuery()
    getattr(
        world_query_proto.select, query_field
    ).Clear()  # field is set, but empty
    world_query_proto.order.by = world_query_pb2.WorldQuery.Order.NAME
    world_query_proto.order.direction = (
        world_query_pb2.WorldQuery.Order.DESCENDING
    )
    node_proto.data.create_or_update.from_world.proto.Pack(world_query_proto)
    node_proto.data.create_or_update.from_world.assign.append(
        any_with_assignments_pb2.AnyWithAssignments.Assignment(
            path='select.' + query_field, cel_expression='bar'
        )
    )
    node_proto.data.create_or_update.from_world.assign.append(
        any_with_assignments_pb2.AnyWithAssignments.Assignment(
            path='filter.name_regex', cel_expression='name_key'
        )
    )
    node_proto.data.create_or_update.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, node.proto, node_proto)

  @parameterized.named_parameters(
      dict(
          testcase_name='child_frames_of',
          query_field='child_frames_of',
      ),
      dict(
          testcase_name='child_objects_of',
          query_field='child_objects_of',
      ),
      dict(
          testcase_name='children_of',
          query_field='children_of',
      ),
  )
  def test_create_from_proto_create_or_update(self, query_field):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    world_query_proto = world_query_pb2.WorldQuery()
    getattr(world_query_proto.select, query_field).by_name.object_name = 'bar'
    world_query_proto.filter.name_regex = 'xyz.*'
    world_query_proto.order.by = world_query_pb2.WorldQuery.Order.NAME
    world_query_proto.order.direction = (
        world_query_pb2.WorldQuery.Order.DESCENDING
    )
    node_proto.data.create_or_update.from_world.proto.Pack(world_query_proto)
    node_proto.data.create_or_update.blackboard_key = 'bbfoo'

    node = bt.Node.create_from_proto(node_proto)

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_create_from_proto_remove(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    node = bt.Node.create_from_proto(node_proto)

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_create_from_proto_without_data_node_fails(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    with self.assertRaises(TypeError):
      _ = bt.Node.create_from_proto(node_proto)

  def test_create_from_proto_without_operation_fails(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.CopyFrom(behavior_tree_pb2.BehaviorTree.DataNode())

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      _ = bt.Node.create_from_proto(node_proto)

  def test_attributes(self):
    """Tests the name and node_id attributes."""
    my_node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.REMOVE,
        blackboard_key='bbfoo',
    )
    self.assertIsNone(my_node.node_id)
    my_node.name = 'foo'
    my_node.node_id = 42
    self.assertEqual(my_node.name, 'foo')
    self.assertEqual(my_node.node_id, 42)

  def test_generates_node_id(self):
    """Tests if generate_and_set_unique_id generates a node_id."""
    my_node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.REMOVE,
        blackboard_key='bbfoo',
    )
    expected_id = my_node.generate_and_set_unique_id()

    self.assertIsNotNone(my_node.node_id)
    self.assertNotEqual(my_node.node_id, '')
    self.assertEqual(my_node.node_id, expected_id)

  def test_to_proto_and_from_proto_retains_node_id(self):
    """Tests if node conversion to/from proto respects node_id."""
    my_node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.REMOVE,
        blackboard_key='bbfoo',
    )
    my_node.node_id = 42

    my_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo', id=42)
    my_proto.data.remove.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, my_node.proto, my_proto)
    compare.assertProto2Equal(
        self, bt.Node.create_from_proto(my_proto).proto, my_proto
    )

  def test_init_remove_ctor(self):
    """Tests if BehaviorTree.Data is correctly for removal."""
    node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.REMOVE,
        blackboard_key='bbfoo',
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_init_remove_builder(self):
    """Tests if BehaviorTree.Data is correctly for removal."""
    node = (
        bt.Data(name='foo')
        .set_operation(bt.Data.OperationType.REMOVE)
        .set_blackboard_key('bbfoo')
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    compare.assertProto2Equal(self, node.proto, node_proto)

  def test_proto_error_on_no_input(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node = bt.Data(name='foo')
    node.set_blackboard_key('bbfoo')
    node.set_operation(bt.Data.OperationType.CREATE_OR_UPDATE)

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      _ = node.proto

  def test_proto_error_on_missing_blackboard_key(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node = bt.Data(name='foo')
    node.set_operation(bt.Data.OperationType.CREATE_OR_UPDATE)
    node.set_cel_expression('bar')

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      _ = node.proto


class BehaviorTreeSubTreeConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.SubTreeCondition."""

  def test_init(self):
    """Tests if BehaviorTree.SubTreeCondition is correctly constructed."""
    condition = bt.SubTreeCondition(
        bt.BehaviorTree(
            root=behavior_call.Action(skill_id='ai.intrinsic.skill-0')
        )
    )
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.behavior_tree.root.task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )
    compare.assertProto2Equal(
        self,
        condition.proto,
        condition_proto,
        ignored_fields=['behavior_tree.tree_id'],
    )

  def test_init_from_skill(self):
    """Tests if BehaviorTree.SubTreeCondition is correctly constructed from a skill."""
    condition = bt.SubTreeCondition(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.behavior_tree.root.task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )
    compare.assertProto2Equal(
        self,
        condition.proto,
        condition_proto,
        ignored_fields=['behavior_tree.tree_id'],
    )

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.SubTreeCondition(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )
    self.assertEqual(
        str(condition),
        'SubTreeCondition(BehaviorTree(root=Task(action=behavior_call.Action(skill_id="ai.intrinsic.skill-0"))))',
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.SubTreeCondition(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.behavior_tree.root.task.call_behavior.skill_id = (
        'ai.intrinsic.skill-0'
    )

    compare.assertProto2Equal(
        self,
        condition.proto,
        condition_proto,
        ignored_fields=['behavior_tree.tree_id'],
    )
    compare.assertProto2Equal(
        self,
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
        ignored_fields=['behavior_tree.tree_id'],
    )


class BehaviorTreeBlackboardConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Blackboard."""

  def test_init(self):
    """Tests if BehaviorTree.Blackboard is correctly constructed."""
    condition = bt.Blackboard('result.accepted')
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.blackboard.cel_expression = 'result.accepted'
    compare.assertProto2Equal(self, condition.proto, condition_proto)

  def test_init_from_cel_expression(self):
    """Tests if BehaviorTree.Blackboard is correctly constructed."""
    condition = bt.Blackboard(cel.CelExpression('result.accepted'))
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.blackboard.cel_expression = 'result.accepted'
    compare.assertProto2Equal(self, condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.Blackboard('result.accepted')
    self.assertEqual(str(condition), 'Blackboard(result.accepted)')

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.Blackboard('result.accepted')

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.blackboard.cel_expression = 'result.accepted'

    compare.assertProto2Equal(self, condition.proto, condition_proto)
    compare.assertProto2Equal(
        self,
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )


class BehaviorTreeAllOfConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.AllOf."""

  def test_init(self):
    """Tests if BehaviorTree.AllOf is correctly constructed."""
    condition = bt.AllOf()
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.all_of.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
    )
    compare.assertProto2Equal(self, condition.proto, condition_proto)

    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'bar'
    compare.assertProto2Equal(self, condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.AllOf()
    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    self.assertEqual(
        str(condition), 'AllOf([ Blackboard(foo) Blackboard(bar) ])'
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.AllOf()
    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'bar'

    compare.assertProto2Equal(self, condition.proto, condition_proto)
    compare.assertProto2Equal(
        self,
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )


class BehaviorTreeAnyOfConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.AnyOf."""

  def test_init(self):
    """Tests if BehaviorTree.AnyOf is correctly constructed."""
    condition = bt.AnyOf()
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.any_of.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
    )
    compare.assertProto2Equal(self, condition.proto, condition_proto)

    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'bar'
    compare.assertProto2Equal(self, condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.AnyOf()
    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    self.assertEqual(
        str(condition), 'AnyOf([ Blackboard(foo) Blackboard(bar) ])'
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.AnyOf()
    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'bar'

    compare.assertProto2Equal(self, condition.proto, condition_proto)
    compare.assertProto2Equal(
        self,
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )


class BehaviorTreeNotConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Not."""

  def test_init(self):
    """Tests if BehaviorTree.AnyOf is correctly constructed."""
    condition = bt.Not(bt.Blackboard('foo'))
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(condition_proto, 'not')
    not_proto.blackboard.cel_expression = 'foo'
    compare.assertProto2Equal(self, condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.Not(bt.Blackboard('foo'))
    self.assertEqual(str(condition), 'Not(Blackboard(foo))')

  def test_create_from_proto_prevents_accidental_call_from_subclass(self):
    """create_from_proto should only be called on the base Condition."""
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(condition_proto, 'not')
    not_proto.blackboard.cel_expression = 'foo'
    with self.assertRaises(TypeError):
      bt.Not.create_from_proto(condition_proto)
    bt.Condition.create_from_proto(condition_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.Not(bt.Blackboard('foo'))

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(condition_proto, 'not')
    not_proto.blackboard.cel_expression = 'foo'

    compare.assertProto2Equal(self, condition.proto, condition_proto)
    compare.assertProto2Equal(
        self,
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )


class DecoratorsTest(absltest.TestCase):
  """Tests the method functions of Decorators."""

  def test_init(self):
    """Tests if Decorators object is correctly constructed."""
    decorators = bt.Decorators()

    decorators_proto = behavior_tree_pb2.BehaviorTree.Node.Decorators()
    compare.assertProto2Equal(self, decorators.proto, decorators_proto)

    decorators = _create_test_decorator('foo')
    decorators_proto.condition.blackboard.cel_expression = 'foo'
    compare.assertProto2Equal(self, decorators.proto, decorators_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    decorators = bt.Decorators(
        condition=bt.Blackboard(cel_expression='foo'),
        breakpoint_type=bt.BreakpointType.BEFORE,
        execution_mode=bt.NodeExecutionMode.DISABLED,
        disabled_result_state=bt.DisabledResultState.FAILED,
    )

    decorators_proto = behavior_tree_pb2.BehaviorTree.Node.Decorators()
    decorators_proto.condition.blackboard.cel_expression = 'foo'
    decorators_proto.breakpoint = (
        behavior_tree_pb2.BehaviorTree.Breakpoint.BEFORE
    )
    execution_settings_proto = behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings(
        mode=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.DISABLED,
        disabled_result_state=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.FAILED,
    )
    decorators_proto.execution_settings.CopyFrom(execution_settings_proto)

    compare.assertProto2Equal(self, decorators.proto, decorators_proto)
    compare.assertProto2Equal(
        self,
        bt.Decorators.create_from_proto(decorators_proto).proto,
        decorators_proto,
    )


if __name__ == '__main__':
  absltest.main()
