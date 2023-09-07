# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.solutions.behavior_tree."""

import io
from typing import cast
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import text_format
from intrinsic.executive.proto import any_with_assignments_pb2
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.executive.proto import test_message_pb2
from intrinsic.executive.proto import world_query_pb2
from intrinsic.solutions import behavior_tree as bt
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import providers
from intrinsic.solutions.internal import behavior_call
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

    self.assertEqual(bt1.proto, bt_pb1)

    bt2 = bt.BehaviorTree(bt=bt1)
    self.assertEqual(bt1.proto, bt2.proto)

    bt3 = bt.BehaviorTree(bt=bt1.proto)
    self.assertEqual(bt1.proto, bt3.proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree is correctly constructed given an action."""
    bt1 = bt.BehaviorTree(
        'my_bt', behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )

    bt_pb1 = behavior_tree_pb2.BehaviorTree()
    bt_pb1.name = 'my_bt'
    bt_pb1.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    self.assertEqual(bt1.proto, bt_pb1)

    bt1.set_root(behavior_call.Action(skill_id='ai.intrinsic.skill-1'))
    bt_pb1.root.task.call_behavior.skill_id = 'ai.intrinsic.skill-1'

    self.assertEqual(bt1.proto, bt_pb1)

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
    self.assertEqual(bt_instance.proto, bt_proto)

  def test_str_conversion(self):
    """Tests if behavior tree conversion to a string works."""
    my_bt = bt.BehaviorTree('my_bt')
    self.assertEqual(
        str(my_bt), 'BehaviorTree(name: my_bt,\n             root: None)'
    )
    action = behavior_call.Action(skill_id='say').require(device='SomeSpeaker')
    my_bt.set_root(bt.Task(action))
    self.assertEqual(
        str(my_bt), 'BehaviorTree(name: my_bt,\n             root: Task(say))'
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
    self.assertEqual(my_bt.proto, my_proto)

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

    self.assertEqual(my_bt.proto, my_proto)
    self.assertEqual(
        bt.BehaviorTree.create_from_proto(my_proto).proto, my_proto
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

    self.assertEqual(my_bt.proto, expected_proto)

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


class BehaviorTreeTaskTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Task."""

  def test_init(self):
    """Tests if BehaviorTree.Task is correctly constructed."""
    node = bt.Task(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0'), name='skill 0'
    )
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='skill 0')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Task(behavior_call.Action(skill_id='ai.intrinsic.skill-0'))
    self.assertEqual(str(node), 'Task(ai.intrinsic.skill-0)')

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Task(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0'), name='foo'
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_to_proto_and_from_proto_call_behavior(self):
    """Tests if conversion to and from a proto representation works.

    This tests the specific case of using the call_behavior oneof option.
    """
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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
    self.assertEqual(node.proto, node_proto)

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
        (
            'SubTree(BehaviorTree(name: some_sub_tree,\n'
            '             root: Task(some_skill)))'
        ),
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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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
    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Fail('')
    self.assertEqual(str(node), 'Fail()')
    node = bt.Fail('some_failure_message')
    self.assertEqual(str(node), 'Fail(some_failure_message)')

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    node = bt.Fail('some_failure_message', name='expected failure')

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='expected failure')
    node_proto.fail.failure_message = 'some_failure_message'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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


class BehaviorTreeSequenceTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Sequence."""

  def test_init(self):
    """Tests if BehaviorTree.Sequence is correctly constructed."""
    node = bt.Sequence(name='foo')
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    self.assertEqual(node.proto, node_proto)

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'

    self.assertEqual(node.proto, node_proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree.Sequence is correctly constructed from actions."""
    node = bt.Sequence([behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_0'

    self.assertEqual(node.proto, node_proto)

    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_1')),
        bt.Task(behavior_call.Action(skill_id='skill_2')),
    )

    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.sequence.children.add().task.call_behavior.skill_id = 'skill_2'

    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Sequence()
    self.assertEqual(str(node), 'Sequence([ ])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(str(node), 'Sequence([ Task(skill_0) Task(skill_1) ])')

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty sequence node to a proto works."""
    node = bt.Sequence()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.sequence.CopyFrom(behavior_tree_pb2.BehaviorTree.SequenceNode())

    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

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
    self.assertEqual(node.proto, node_proto)

  def test_init_with_actions(self):
    """Tests if BehaviorTree.Parallel is correctly constructed from actions."""
    node = bt.Parallel(children=[behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.parallel.children.add().task.call_behavior.skill_id = 'skill_0'
    self.assertEqual(node.proto, node_proto)

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
    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Parallel()
    self.assertEqual(str(node), 'Parallel([ ])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(str(node), 'Parallel([ Task(skill_0) Task(skill_1) ])')

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty parallel node to a proto works."""
    node = bt.Parallel()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.parallel.CopyFrom(behavior_tree_pb2.BehaviorTree.ParallelNode())
    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

  def test_proto_with_unspecified_failure_behavior_resolves_to_default(self):
    node = bt.Parallel.create_from_proto(behavior_tree_pb2.BehaviorTree.Node())
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
    self.assertEqual(node.proto, node_proto)

  def test_init_with_actions(self):
    """Tests if BehaviorTree.Selector is correctly constructed from actions."""
    node = bt.Selector([behavior_call.Action(skill_id='skill_0')])
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_0'

    self.assertEqual(node.proto, node_proto)

    node.set_children(
        behavior_call.Action(skill_id='skill_1'),
        behavior_call.Action(skill_id='skill_2'),
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.selector.children.add().task.call_behavior.skill_id = 'skill_2'
    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Selector()
    self.assertEqual(str(node), 'Selector([ ])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(str(node), 'Selector([ Task(skill_0) Task(skill_1) ])')

  def test_to_proto_empty_node(self):
    """Tests if empty node conversion to a proto representation works."""
    node = bt.Selector()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.selector.CopyFrom(behavior_tree_pb2.BehaviorTree.SelectorNode())
    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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

    self.assertEqual(node.proto, node_proto)

  def test_init_from_action(self):
    """Tests if BehaviorTree.Retry is correctly constructed from actions."""
    node = bt.Retry(2, behavior_call.Action(skill_id='skill_0'))

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.retry.max_tries = 2
    node_proto.retry.child.task.call_behavior.skill_id = 'skill_0'
    node_proto.retry.retry_counter_blackboard_key = node.retry_counter

    self.assertEqual(node.proto, node_proto)
    node.set_child(behavior_call.Action(skill_id='skill_1'))

    node_proto.retry.child.task.call_behavior.skill_id = 'skill_1'

    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Retry()
    self.assertEqual(str(node), 'Retry 0(child=None, recovery=None)')
    node.max_tries = 2
    node.set_child(bt.Task(behavior_call.Action(skill_id='skill_0')))
    self.assertEqual(str(node), 'Retry 2(child=Task(skill_0), recovery=None)')
    node.set_recovery(bt.Task(behavior_call.Action(skill_id='skill_1')))
    self.assertEqual(
        str(node), 'Retry 2(child=Task(skill_0), recovery=Task(skill_1))'
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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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
    self.assertEqual(node.proto, node_proto)

  def test_init_with_action(self):
    """Tests if BehaviorTree.Fallback is correctly constructed from actions."""
    node = bt.Fallback([behavior_call.Action(skill_id='skill_0')])

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_0'

    self.assertEqual(node.proto, node_proto)

    node.set_children(
        behavior_call.Action(skill_id='skill_1'),
        behavior_call.Action(skill_id='skill_2'),
    )
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_1'
    node_proto.fallback.children.add().task.call_behavior.skill_id = 'skill_2'

    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Fallback()
    self.assertEqual(str(node), 'Fallback([ ])')
    node.set_children(
        bt.Task(behavior_call.Action(skill_id='skill_0')),
        bt.Task(behavior_call.Action(skill_id='skill_1')),
    )
    self.assertEqual(str(node), 'Fallback([ Task(skill_0) Task(skill_1) ])')

  def test_to_proto_empty_node(self):
    """Tests if conversion of an empty fallback node to a proto works."""
    node = bt.Fallback()
    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.fallback.CopyFrom(behavior_tree_pb2.BehaviorTree.FallbackNode())
    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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

    self.assertEqual(node.proto, node_proto)

  def test_init_from_action(self):
    """Tests if BehaviorTree.Loop is correctly constructed from actions."""
    node = bt.Loop(
        max_times=2, do_child=behavior_call.Action(skill_id='skill_0')
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node()
    node_proto.loop.max_times = 2
    node_proto.loop.do.task.call_behavior.skill_id = 'skill_0'
    node_proto.loop.loop_counter_blackboard_key = node.loop_counter

    self.assertEqual(node.proto, node_proto)
    node.set_do_child(behavior_call.Action(skill_id='skill_1'))

    node_proto.loop.do.task.call_behavior.skill_id = 'skill_1'

    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Loop()
    self.assertEqual(str(node), 'Loop (None)')
    node.max_times = 2
    node.set_do_child(behavior_call.Action(skill_id='skill_0'))
    node.set_while_condition(bt.Blackboard('foo'))
    self.assertEqual(
        str(node), 'Loop (iterations <= 2) and Blackboard(foo) (Task(skill_0))'
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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
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

    self.assertEqual(
        node.proto,
        node_proto,
    )
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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

    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    node = bt.Branch()
    self.assertEqual(str(node), 'Branch')
    node.set_then_child(behavior_call.Action(skill_id='skill_0'))
    node.set_if_condition(bt.Blackboard('foo'))
    self.assertEqual(str(node), 'Branch Blackboard(foo) then (Task(skill_0))')

    node.set_else_child(behavior_call.Action(skill_id='skill_1'))
    self.assertEqual(
        str(node),
        'Branch Blackboard(foo) then (Task(skill_0)) else (Task(skill_1))',
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

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
    )

    node.set_decorators(_create_test_decorator())
    node_proto.decorators.condition.blackboard.cel_expression = 'foo'

    self.assertEqual(node.proto, node_proto)
    self.assertEqual(
        bt.Node.create_from_proto(node_proto).proto,
        node_proto,
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

    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)

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

    self.assertEqual(node.proto, node_proto)

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

    node = bt.Data.create_from_proto(node_proto)

    self.assertEqual(node.proto, node_proto)

  def test_create_from_proto_remove(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    node = bt.Data.create_from_proto(node_proto)

    self.assertEqual(node.proto, node_proto)

  def test_create_from_proto_without_data_node_fails(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      _ = bt.Data.create_from_proto(node_proto)

  def test_create_from_proto_without_operation_fails(self):
    """Tests if BehaviorTree.Data is correctly constructed."""
    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.CopyFrom(behavior_tree_pb2.BehaviorTree.DataNode())

    with self.assertRaises(solutions_errors.InvalidArgumentError):
      _ = bt.Data.create_from_proto(node_proto)

  def test_init_remove_ctor(self):
    """Tests if BehaviorTree.Data is correctly for removal."""
    node = bt.Data(
        name='foo',
        operation=bt.Data.OperationType.REMOVE,
        blackboard_key='bbfoo',
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    self.assertEqual(node.proto, node_proto)

  def test_init_remove_builder(self):
    """Tests if BehaviorTree.Data is correctly for removal."""
    node = (
        bt.Data(name='foo')
        .set_operation(bt.Data.OperationType.REMOVE)
        .set_blackboard_key('bbfoo')
    )

    node_proto = behavior_tree_pb2.BehaviorTree.Node(name='foo')
    node_proto.data.remove.blackboard_key = 'bbfoo'

    self.assertEqual(node.proto, node_proto)

  @mock.patch.object(bt, '_generate_unique_identifier', autospec=True)
  def test_print_python_code_remove(self, generate_mock):
    """Tests if BehaviorTree.Data is correctly printed."""

    node = (
        bt.Data(name='foo')
        .set_operation(bt.Data.OperationType.REMOVE)
        .set_blackboard_key('bbfoo')
    )

    generate_mock.side_effect = ['bar1']

    expected_str = """bar1 = BT.Data(name="foo", operation=OperationType.REMOVE, blackboard_key="bbfoo")
"""

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      node.print_python_code(
          [], mock.create_autospec(providers.SkillProvider, instance=True)
      )

    self.assertEqual(mock_stdout.getvalue(), expected_str)

  @parameterized.named_parameters(
      dict(
          testcase_name='cel_expression',
          arg_name='cel_expression',
          arg_value='5+5',
          expected_string='cel_expression="5+5"',
      ),
      dict(
          testcase_name='world_query',
          arg_name='world_query',
          arg_value=bt.WorldQuery().select(
              children_of=object_world_refs_pb2.ObjectReference(
                  by_name=object_world_refs_pb2.ObjectReferenceByName(
                      object_name='bar'
                  )
              )
          ),
          expected_string='''world_query=WorldQuery(text_format.Parse("""select {
  children_of {
    by_name {
      object_name: "bar"
    }
  }
}
""", intrinsic_proto.executive.WorldQuery()))''',
      ),
      dict(
          testcase_name='proto',
          arg_name='proto',
          arg_value=test_message_pb2.TestMessage(int64_value=123),
          expected_string='''proto=text_format.Parse("""int64_value: 123
""", intrinsic_proto.executive.TestMessage())''',
      ),
      dict(
          testcase_name='protos',
          arg_name='protos',
          arg_value=[
              test_message_pb2.TestMessage(int64_value=123),
              test_message_pb2.TestMessage(int32_value=234),
          ],
          expected_string='''protos=[text_format.Parse("""int64_value: 123

""", intrinsic_proto.executive.TestMessage()), text_format.Parse("""int32_value: 234

""", intrinsic_proto.executive.TestMessage())]''',
      ),
  )
  @mock.patch.object(bt, '_generate_unique_identifier', autospec=True)
  def test_print_python_code_create_or_update(
      self, generate_mock, arg_name, arg_value, expected_string
  ):
    """Tests if BehaviorTree.Data is correctly printed."""

    node_args = {
        'name': 'foo',
        'operation': bt.Data.OperationType.CREATE_OR_UPDATE,
        'blackboard_key': 'bbfoo',
        arg_name: arg_value,
    }
    node = bt.Data(**node_args)

    generate_mock.side_effect = ['bar1']

    expected_str = f"""bar1 = BT.Data(name="foo", operation=OperationType.CREATE_OR_UPDATE, blackboard_key="bbfoo", {expected_string})
"""

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      node.print_python_code(
          [], mock.create_autospec(providers.SkillProvider, instance=True)
      )

    self.assertEqual(mock_stdout.getvalue(), expected_str)

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
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    self.assertEqual(condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.SubTreeCondition(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )
    self.assertEqual(
        str(condition), 'SubTreeCondition(Task(ai.intrinsic.skill-0))'
    )

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.SubTreeCondition(
        behavior_call.Action(skill_id='ai.intrinsic.skill-0')
    )

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'

    self.assertEqual(condition.proto, condition_proto)
    self.assertEqual(
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )

    condition_proto.blackboard.cel_expression = 'ai.intrinsic.skill-0'
    with self.assertRaises(ValueError):
      bt.SubTreeCondition.create_from_proto(condition_proto)


class BehaviorTreeBlackboardConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Blackboard."""

  def test_init(self):
    """Tests if BehaviorTree.Blackboard is correctly constructed."""
    condition = bt.Blackboard('result.accepted')
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.blackboard.cel_expression = 'result.accepted'
    self.assertEqual(condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.Blackboard('result.accepted')
    self.assertEqual(str(condition), 'Blackboard(result.accepted)')

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.Blackboard('result.accepted')

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.blackboard.cel_expression = 'result.accepted'

    self.assertEqual(condition.proto, condition_proto)
    self.assertEqual(
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )

    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    with self.assertRaises(ValueError):
      bt.Blackboard.create_from_proto(condition_proto)


class BehaviorTreeAllOfConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.AllOf."""

  def test_init(self):
    """Tests if BehaviorTree.AllOf is correctly constructed."""
    condition = bt.AllOf()
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.all_of.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
    )
    self.assertEqual(condition.proto, condition_proto)

    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.all_of.conditions.add().blackboard.cel_expression = 'bar'
    self.assertEqual(condition.proto, condition_proto)

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

    self.assertEqual(condition.proto, condition_proto)
    self.assertEqual(
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )

    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    with self.assertRaises(ValueError):
      bt.AllOf.create_from_proto(condition_proto)


class BehaviorTreeAnyOfConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.AnyOf."""

  def test_init(self):
    """Tests if BehaviorTree.AnyOf is correctly constructed."""
    condition = bt.AnyOf()
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    condition_proto.any_of.CopyFrom(
        behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
    )
    self.assertEqual(condition.proto, condition_proto)

    condition.set_conditions([bt.Blackboard('foo'), bt.Blackboard('bar')])
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'foo'
    condition_proto.any_of.conditions.add().blackboard.cel_expression = 'bar'
    self.assertEqual(condition.proto, condition_proto)

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

    self.assertEqual(condition.proto, condition_proto)
    self.assertEqual(
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )

    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    with self.assertRaises(ValueError):
      bt.AnyOf.create_from_proto(condition_proto)


class BehaviorTreeNotConditionTest(absltest.TestCase):
  """Tests the method functions of BehaviorTree.Not."""

  def test_init(self):
    """Tests if BehaviorTree.AnyOf is correctly constructed."""
    condition = bt.Not(bt.Blackboard('foo'))
    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(condition_proto, 'not')
    not_proto.blackboard.cel_expression = 'foo'
    self.assertEqual(condition.proto, condition_proto)

  def test_str_conversion(self):
    """Tests if conversion to string works."""
    condition = bt.Not(bt.Blackboard('foo'))
    self.assertEqual(str(condition), 'Not(Blackboard(foo))')

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    condition = bt.Not(bt.Blackboard('foo'))

    condition_proto = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(condition_proto, 'not')
    not_proto.blackboard.cel_expression = 'foo'

    self.assertEqual(condition.proto, condition_proto)
    self.assertEqual(
        bt.Condition.create_from_proto(condition_proto).proto,
        condition_proto,
    )

    condition_proto.tree.task.call_behavior.skill_id = 'ai.intrinsic.skill-0'
    with self.assertRaises(ValueError):
      bt.Not.create_from_proto(condition_proto)


class DecoratorsTest(absltest.TestCase):
  """Tests the method functions of Decorators."""

  def test_init(self):
    """Tests if Decorators object is correctly constructed."""
    decorators = bt.Decorators()

    decorators_proto = behavior_tree_pb2.BehaviorTree.Node.Decorators()
    self.assertEqual(decorators.proto, decorators_proto)

    decorators = _create_test_decorator('foo')
    decorators_proto.condition.blackboard.cel_expression = 'foo'
    self.assertEqual(decorators.proto, decorators_proto)

  def test_to_proto_and_from_proto(self):
    """Tests if conversion to and from a proto representation works."""
    decorators = bt.Decorators(
        condition=bt.Blackboard(cel_expression='foo'),
        breakpoint_type=bt.BreakpointType.BEFORE,
    )

    decorators_proto = behavior_tree_pb2.BehaviorTree.Node.Decorators()
    decorators_proto.condition.blackboard.cel_expression = 'foo'
    decorators_proto.breakpoint = (
        behavior_tree_pb2.BehaviorTree.Breakpoint.BEFORE
    )

    self.assertEqual(decorators.proto, decorators_proto)
    self.assertEqual(
        bt.Decorators.create_from_proto(decorators_proto).proto,
        decorators_proto,
    )

  @mock.patch.object(bt, '_generate_unique_identifier', autospec=True)
  def test_print_python_code(self, generate_mock):
    """Tests that the expected Python string is generated."""

    decorators = bt.Decorators(
        condition=bt.Blackboard(cel_expression='foo'),
        breakpoint_type=bt.BreakpointType.BEFORE,
    )

    generate_mock.side_effect = ['bar1', 'bar2']

    expected_str = """bar1 = BT.Blackboard(cel_expression="foo")
bar2 = BT.Decorators(condition=bar1, breakpoint_type=BT.BreakpointType.BEFORE)
"""

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      decorators.print_python_code(
          [], mock.create_autospec(providers.SkillProvider, instance=True)
      )

    self.assertEqual(mock_stdout.getvalue(), expected_str)


if __name__ == '__main__':
  absltest.main()
