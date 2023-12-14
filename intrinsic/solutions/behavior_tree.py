# Copyright 2023 Intrinsic Innovation LLC

"""Python API for behavior trees.

Includes a BehaviorTree class, which inherits from Plan,
a nested Node class, which represents the nodes of the tree,
and various children classes of Node for each type of supported
BT node.
The BehaviorTree includes a method to generate a Graphviz dot representation
for it, a method to generate a proto of type behavior_tree_pb2,
and a class method to initialize a new BehaviorTree from a BT proto object.

To execute the behavior tree, simply pass an instance of BehaviorTree to the
executive.run() method.
"""

import abc
import collections
import enum
import sys
from typing import Any as AnyType, Callable, Iterable, List, Mapping, Optional, Sequence as SequenceType, Tuple, Union
import uuid

from google.protobuf import any_pb2
from google.protobuf import descriptor_pb2
from google.protobuf import message as protobuf_message
import graphviz
from intrinsic.executive.proto import any_list_pb2
from intrinsic.executive.proto import any_with_assignments_pb2
from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.executive.proto import world_query_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import ipython
from intrinsic.solutions import providers
from intrinsic.solutions import skill_utils
from intrinsic.solutions import skills as skills_mod
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions
from intrinsic.solutions.internal import behavior_call
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.python import object_world_resources

_SUBTREE_DOT_ATTRIBUTES = {'labeljust': 'l', 'labelloc': 't'}
_NODE_TYPES_TO_DOT_SHAPES = {
    'task': 'box',
    'sub_tree': 'point',
    'fail': 'box',
    'sequence': 'cds',
    'parallel': 'trapezium',
    'selector': 'octagon',
    'fallback': 'octagon',
    'loop': 'hexagon',
    'retry': 'hexagon',
    'branch': 'diamond',
    'data': 'box',
}


def _generate_unique_identifier(base_name: str, identifiers: List[str]) -> str:
  """Generates a unique identifier using the given base name.

  The returned string will be unique amongst the list of identifiers, achieved
  by adding the count of the time the base name already exists.

  Args:
    base_name: The base of the desired identifier, is returned unchanged if
      unique.
     identifiers: List of already present identifiers.

  Returns:
    unique identifier created from base_name and number of occurrences of said
    base_name

  Example: The list of identifiers includes `sequence` and `sequence1`, given
    the base_name `sequence` this function will return `sequence2`.
  """
  base_name = base_name.lower().replace(' ', '_').replace('-', '_')
  while base_name in identifiers:
    base_name = (
        base_name
        + '_'
        + str(sum(1 for name in identifiers if base_name + '_' in name) + 1)
    )
  identifiers.append(base_name)
  return base_name


def _transform_to_node(node: Union['Node', actions.ActionBase]) -> 'Node':
  if isinstance(node, actions.ActionBase):
    return Task(node)
  return node


def _transform_to_optional_node(
    node: Optional[Union['Node', actions.ActionBase]]
) -> Optional['Node']:
  if node is None:
    return None
  return _transform_to_node(node)


def _dot_wrap_in_box(
    child_graph: graphviz.Digraph, name: str, label: str
) -> graphviz.Digraph:
  box_dot_graph = graphviz.Digraph()
  box_dot_graph.name = 'cluster_' + name
  box_dot_graph.graph_attr = {'label': label}
  box_dot_graph.graph_attr.update(_SUBTREE_DOT_ATTRIBUTES)
  box_dot_graph.subgraph(child_graph)
  return box_dot_graph


def _dot_append_child(
    dot_graph: graphviz.Digraph,
    parent_node_name: str,
    child_node: 'Node',
    child_node_id_suffix: str,
    edge_label: str = '',
):
  """Inserts in place a subgraph of the given child into the given graph.

  This function has side effects!
  It changes the `dot_graph` and returns nothing.

  Args:
    dot_graph: The dot graph instance, which should be updated.
    parent_node_name: The name of the node in the dot graph, which should get an
      edge connecting it to the child node.
    child_node: A behavior tree Node, which should get converted to dot and its
      graph should be appended to the `dot_graph`.
    child_node_id_suffix: A little string to make the child node name unique
      within the dot graph.
    edge_label: Typically, the edge from the parent to the child is not
      annotated with a label. If a custom edge annotation is needed, this
      argument value can be used for that.
  """
  child_dot_graph, child_node_name = child_node.dot_graph(child_node_id_suffix)
  dot_graph.subgraph(child_dot_graph)
  dot_graph.edge(parent_node_name, child_node_name, label=edge_label)


def _dot_append_children(
    dot_graph: graphviz.Digraph,
    parent_node_name: str,
    child_nodes: Iterable['Node'],
    parent_node_id_suffix: str,
    node_id_suffix_offset: int,
):
  """Inserts in place subgraphs of the given children into the given graph.

  This function has side effects!
  It changes the `dot_graph` and returns nothing.

  Args:
    dot_graph: The dot graph instance, which should be updated.
    parent_node_name: The name of the node in the dot graph, which should get
      edges connecting it to the child nodes.
    child_nodes: A list of behavior tree Nodes, which should get converted to a
      dot representation and be added to the `dot_graph` as subgraphs.
    parent_node_id_suffix: The suffix that was used to make the parent node
      unique in the dot graph.
    node_id_suffix_offset: A number that is unique among the children of the
      given parent node, which is appended as a suffix to the child node names
      to make them unique in the dot graph.
  """
  for i, child_node in enumerate(child_nodes):
    _dot_append_child(
        dot_graph,
        parent_node_name,
        child_node,
        parent_node_id_suffix + '_' + str(i + node_id_suffix_offset),
    )


# The following is of type TypeAlias, but this is not available in Python 3.9
# which is still used for the externalized version.
WorldQueryObject = Union[
    object_world_resources.WorldObject,
    object_world_refs_pb2.ObjectReference,
    blackboard_value.BlackboardValue,
]


class WorldQuery:
  """Wrapper for WorldQuery proto for easier construction and conversion."""

  _proto: world_query_pb2.WorldQuery
  _assignments: List[any_with_assignments_pb2.AnyWithAssignments.Assignment]

  def __init__(self, proto: Optional[world_query_pb2.WorldQuery] = None):
    self._proto = world_query_pb2.WorldQuery()
    if proto is not None:
      self._proto.CopyFrom(proto)
    self._assignments = []

  def _object_to_reference(
      self, obj: Optional[WorldQueryObject]
  ) -> Optional[object_world_refs_pb2.ObjectReference]:
    """Converts an object to a reference (or returns as-is if reference given).

    Args:
      obj: object to convert

    Returns:
      An object reference, either retrieved from the WorldObject or just the
      reference that was passed in.

    Raises:
      TypeError: if the passed in object is neither a WorldObject nor an
        ObjectReference.
    """
    if obj is None:
      return None

    if isinstance(obj, blackboard_value.BlackboardValue):
      return object_world_refs_pb2.ObjectReference()

    if isinstance(obj, object_world_resources.WorldObject):
      return obj.reference

    if isinstance(obj, object_world_refs_pb2.ObjectReference):
      return obj

    raise TypeError(
        'Invalid type for object, cannot convert to ObjectReference'
    )

  @utils.protoenum(
      proto_enum_type=world_query_pb2.WorldQuery.Order.Criterion,
      unspecified_proto_enum_map_to_none=world_query_pb2.WorldQuery.Order.Criterion.SORT_ORDER_UNSPECIFIED,
  )
  class OrderCriterion(enum.Enum):
    """Specifies what to sort returned values by."""

  @utils.protoenum(proto_enum_type=world_query_pb2.WorldQuery.Order.Direction)
  class OrderDirection(enum.Enum):
    """Specifies sort order for returned items."""

  def _handle_blackboard_assignments(
      self, path: str, assigned: AnyType
  ) -> None:
    """Handle assignments that might come from the blackboard.

    If the assigned object is a BlackboardValue an assignment to path will be
    added. Otherwise nothing happens.

    Args:
      path: The field in the WorldQuery that would be set.
      assigned: Either a BlackboardValue or something else.
    """
    if isinstance(assigned, blackboard_value.BlackboardValue):
      self._assignments.append(
          any_with_assignments_pb2.AnyWithAssignments.Assignment(
              path=path,
              cel_expression=assigned.value_access_path(),
          )
      )

  def select(
      self,
      *,
      child_frames_of: Optional[WorldQueryObject] = None,
      child_objects_of: Optional[WorldQueryObject] = None,
      children_of: Optional[WorldQueryObject] = None,
  ) -> 'WorldQuery':
    """Sets the query of the world query.

    Set only one of the possible arguments.

    Args:
      child_frames_of: the object of which to retrieve child frames of
      child_objects_of: the object of which to retrieve child objects of
      children_of: the object of which to retrieve children of

    Returns:
      Self (for chaining in a builder pattern)

    Raises:
      InvalidArgumentError: if zero or more than 1 input argument is set
    """
    num_inputs = 0

    if child_frames_of is not None:
      num_inputs += 1
      self._proto.select.child_frames_of.CopyFrom(
          self._object_to_reference(child_frames_of)
      )
      self._handle_blackboard_assignments(
          'select.child_frames_of', child_frames_of
      )
    if child_objects_of is not None:
      num_inputs += 1
      self._proto.select.child_objects_of.CopyFrom(
          self._object_to_reference(child_objects_of)
      )
      self._handle_blackboard_assignments(
          'select.child_objects_of', child_objects_of
      )
    if children_of is not None:
      num_inputs += 1
      self._proto.select.children_of.CopyFrom(
          self._object_to_reference(children_of)
      )
      self._handle_blackboard_assignments('select.children_of', children_of)

    if num_inputs != 1:
      raise solutions_errors.InvalidArgumentError(
          'Data node for create or update requires exactly 1 input'
          f' element, got {num_inputs}'
      )

    return self

  def filter(
      self, *, name_regex: Union[str, blackboard_value.BlackboardValue]
  ) -> 'WorldQuery':
    """Sets the filter of the world query.

    Args:
      name_regex: RE2 regular expression that names must fully match to be
        returned.

    Returns:
      Self (for chaining in a builder pattern)
    """
    if isinstance(name_regex, blackboard_value.BlackboardValue):
      self._handle_blackboard_assignments('filter.name_regex', name_regex)
    else:
      self._proto.filter.name_regex = name_regex
    return self

  def order(
      self,
      *,
      by: OrderCriterion,
      direction: OrderDirection = OrderDirection.ASCENDING,
  ) -> 'WorldQuery':
    """Sets the ordering of the world query.

    Args:
      by: criterion identifying what to order by
      direction: ordering direction, ascending or descending

    Returns:
      Self (for chaining in a builder pattern)
    """
    self._proto.order.by = by.value
    self._proto.order.direction = direction.value
    return self

  @property
  def proto(self) -> world_query_pb2.WorldQuery:
    return self._proto

  @property
  def assignments(
      self,
  ) -> List[any_with_assignments_pb2.AnyWithAssignments.Assignment]:
    return self._assignments

  @classmethod
  def create_from_proto(
      cls, proto_object: world_query_pb2.WorldQuery
  ) -> 'WorldQuery':
    return cls(proto_object)

  def __str__(self) -> str:
    return (
        f'WorldQuery(text_format.Parse("""{self._proto}""",'
        ' intrinsic_proto.executive.WorldQuery()))'
    )


@utils.protoenum(
    proto_enum_type=behavior_tree_pb2.BehaviorTree.Breakpoint.Type,
    unspecified_proto_enum_map_to_none=behavior_tree_pb2.BehaviorTree.Breakpoint.TYPE_UNSPECIFIED,
)
class BreakpointType(enum.Enum):
  """Specifies when to apply a breakpoint."""


@utils.protoenum(
    proto_enum_type=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.Mode,
    unspecified_proto_enum_map_to_none=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.UNSPECIFIED,
)
class NodeExecutionMode(enum.Enum):
  """Specifies the execution mode for a node."""


@utils.protoenum(
    proto_enum_type=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.DisabledResultState,
    unspecified_proto_enum_map_to_none=behavior_tree_pb2.BehaviorTree.Node.ExecutionSettings.DISABLED_RESULT_STATE_UNSPECIFIED,
)
class DisabledResultState(enum.Enum):
  """Specifies the forced resulting state for a disabled node."""


class Decorators:
  """Collection of properties assigned to a node.

  Currently, we support a single condition decorator.

  Attributes:
    condition: A condition to decide if a node can be executed or should fail
      immediately.
    breakpoint_type: Optional breakpoint type for the node, see BreakpointType.
    execution_mode: Optional NodeExecutionMode that allows to disable a node.
    disabled_result_state: Optional DisabledResultState forcing a resulting
      state for disabled nodes. Ignored unless execution_mode is DISABLED.
    proto: The proto representation of the decorators objects.
  """

  condition: Optional['Condition']
  breakpoint_type: Optional['BreakpointType']
  execution_mode: Optional[NodeExecutionMode]
  disabled_result_state: Optional[DisabledResultState]

  def __init__(
      self,
      condition: Optional['Condition'] = None,
      breakpoint_type: Optional['BreakpointType'] = None,
      execution_mode: Optional[NodeExecutionMode] = None,
      disabled_result_state: Optional[DisabledResultState] = None,
  ):
    self.condition = condition
    self.breakpoint_type = breakpoint_type
    self.execution_mode = execution_mode
    self.disabled_result_state = disabled_result_state

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node.Decorators:
    """Converts the Decorators object to a Decorators proto.

    Returns:
      A proto representation of this object.
    """
    proto_message = behavior_tree_pb2.BehaviorTree.Node.Decorators()
    if self.condition is not None:
      proto_message.condition.CopyFrom(self.condition.proto)
    if self.breakpoint_type is not None:
      proto_message.breakpoint = self.breakpoint_type.value
    if self.execution_mode is not None:
      proto_message.execution_settings.mode = self.execution_mode.value
      if self.disabled_result_state is not None:
        proto_message.execution_settings.disabled_result_state = (
            self.disabled_result_state.value
        )

    return proto_message

  @classmethod
  def create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.Node.Decorators
  ) -> 'Decorators':
    """Creates an instance from a Decorators proto.

    Args:
      proto_object: Proto to read data from.

    Returns:
      Instance of Decorators wrapper with data from proto.
    """
    decorator = cls()
    if proto_object.HasField('condition'):
      decorator.condition = Condition.create_from_proto(proto_object.condition)
    if proto_object.HasField('breakpoint'):
      decorator.breakpoint_type = BreakpointType.from_proto(
          proto_object.breakpoint
      )
    if proto_object.HasField('execution_settings'):
      execution_settings_proto = proto_object.execution_settings
      decorator.execution_mode = NodeExecutionMode.from_proto(
          execution_settings_proto.mode
      )
      if execution_settings_proto.HasField('disabled_result_state'):
        decorator.disabled_result_state = DisabledResultState.from_proto(
            execution_settings_proto.disabled_result_state
        )
    return decorator

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    """Prints string with Python code that would create the same instance.

    Args:
      identifiers: Already existing identifiers (in the larger tree context).
      skills: Provider giving access to available skills.

    Returns:
      Identifier used to declare the Decorator, or empty string if no
      decorator needed to be generated (no field set).
    """
    if self.condition is not None:
      condition_identifier = self.condition.print_python_code(
          identifiers, skills
      )

    if (
        self.condition is not None
        or self.breakpoint_type is not None
        or self.execution_mode is not None
    ):
      identifier = _generate_unique_identifier('decorator', identifiers)
      if self.execution_mode is not None:
        execution_mode_identifier = _generate_unique_identifier(
            'node_execution_mode', identifiers
        )
        disabled_result_state_identifier = None
        if self.disabled_result_state is not None:
          disabled_result_state_identifier = _generate_unique_identifier(
              'disabled_result_state', identifiers
          )
          print(
              f'{execution_mode_identifier} ='
              f' BT.NodeExecutionMode({self.execution_mode}){disabled_result_state_identifier} ='
              f' BT.DisabledResultState({self.disabled_result_state})'
          )
        else:
          print(
              f'{execution_mode_identifier} ='
              f' BT.NodeExecutionMode({self.execution_mode})'
          )
      sys.stdout.write(f'{identifier} = BT.Decorators(')
      decorator_params = []
      if self.condition is not None:
        decorator_params.append(f'condition={condition_identifier}')
      if self.breakpoint_type is not None:
        decorator_params.append(f'breakpoint_type=BT.{self.breakpoint_type}')
      if self.execution_mode is not None:
        decorator_params.append(f'execution_mode={execution_mode_identifier}')
        if self.disabled_result_state is not None:
          decorator_params.append(
              f'disabled_result_state={disabled_result_state_identifier}'
          )
      sys.stdout.write(', '.join(decorator_params))
      print(')')
      return identifier

    return ''


class Node(abc.ABC):
  """Parent abstract base class for all the supported behavior tree nodes.

  Attributes:
    proto: The proto representation of the node.
    name: Optional name of the node.
    node_type: A string label of the node type.
    decorators: A list of decorators for the current node.
    breakpoint: Optional type of breakpoint configured for this node.
    execution_mode: Optional execution mode for this node.
    node_id: A unique id for this node.
  """

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}({self._name_repr()})'

  def _name_repr(self) -> str:
    """Returns a snippet for the name attribute to be used in __repr__.

    The snippet is a keyword argument of the form 'name="example_name", '. It
    will be empty, if name is not set. It can be inserted in the output of a
    constructor call in __repr__ without any logic (e.g., adding commas or not,
    handling the name not being set).
    """
    name_snippet = ''
    if self.name is not None:
      name_snippet = f'name="{self.name}", '
    return name_snippet

  @classmethod
  def create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.Node
  ) -> 'Node':
    """Instantiates a Node instance from a proto."""
    if cls != Node:
      raise TypeError('create_from_proto can only be called on the Node class')
    node_type = proto_object.WhichOneof('node_type')
    # pylint:disable=protected-access
    # Intentionally using knowledge of subclasses in this parent class, so that
    # it is possible to provide a generic function to create the appropriate
    # subclass from a Node proto.
    if node_type == 'task':
      created_node = Task._create_from_proto(proto_object.task)
    elif node_type == 'sub_tree':
      created_node = SubTree._create_from_proto(proto_object.sub_tree)
    elif node_type == 'fail':
      created_node = Fail._create_from_proto(proto_object.fail)
    elif node_type == 'sequence':
      created_node = Sequence._create_from_proto(proto_object.sequence)
    elif node_type == 'parallel':
      created_node = Parallel._create_from_proto(proto_object.parallel)
    elif node_type == 'selector':
      created_node = Selector._create_from_proto(proto_object.selector)
    elif node_type == 'retry':
      created_node = Retry._create_from_proto(proto_object.retry)
    elif node_type == 'fallback':
      created_node = Fallback._create_from_proto(proto_object.fallback)
    elif node_type == 'loop':
      created_node = Loop._create_from_proto(proto_object.loop)
    elif node_type == 'branch':
      created_node = Branch._create_from_proto(proto_object.branch)
    elif node_type == 'data':
      created_node = Data._create_from_proto(proto_object.data)
    else:
      raise TypeError('Unsupported proto node type', node_type)
    # pylint:enable=protected-access
    if proto_object.HasField('decorators'):
      created_node.set_decorators(
          Decorators.create_from_proto(proto_object.decorators)
      )
    if proto_object.HasField('name'):
      created_node.name = proto_object.name
    if proto_object.HasField('id') and proto_object.id != 0:
      created_node.node_id = proto_object.id
    return created_node

  @property
  @abc.abstractmethod
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    """Return proto representation of a Node object."""
    proto_message = behavior_tree_pb2.BehaviorTree.Node()
    if self.name is not None:
      proto_message.name = self.name
    if self.node_id is not None:
      proto_message.id = self.node_id
    if self.decorators is not None:
      proto_message.decorators.CopyFrom(self.decorators.proto)

    return proto_message

  def generate_and_set_unique_id(self) -> int:
    """Generates a new random id and sets it for this node."""
    if self.node_id is not None:
      print(
          'Warning: Creating a new unique id, but this node already had an id'
          f' ({self.node_id})'
      )
    uid = uuid.uuid4()
    uid_128 = uid.int
    # The proto only specifies uint32, so a 128-bit UUID wouldn't fit. XOR
    # this together to retain sufficient randomness to prevent collisions.
    # Node Ids must be unique only within the behavior tree that is being
    # created.
    uid_32 = (
        (uid_128 & 0xFFFFFFFF)
        ^ (uid_128 & (0xFFFFFFFF << 32)) >> 32
        ^ (uid_128 & (0xFFFFFFFF << 64)) >> 64
        ^ (uid_128 & (0xFFFFFFFF << 96)) >> 96
    )
    self.node_id = uid_32
    return self.node_id

  @property
  @abc.abstractmethod
  def node_type(self) -> str:
    ...

  @abc.abstractmethod
  def dot_graph(
      self,
      node_id_suffix: str = '',
      node_label: Optional[str] = None,
      name: Optional[str] = None,
  ) -> Tuple[graphviz.Digraph, str]:
    """Generates a graphviz subgraph with a single node for `self`.

    Args:
      node_id_suffix: A little string of form `_1_2`, which is just a suffix to
        make a unique node name in the graph. If the node names clash within the
        graph, they are merged into one, and we do not want to merge unrelated
        nodes.
      node_label: The label is typically just the type of the node. To use a
        different value, this argument can be used.
      name: name of the node as set by the user.

    Returns:
      A tuple of the generated graphviz dot graph and
      the name of the graph's root node.
    """

    dot_graph = graphviz.Digraph()
    node_name = self.node_type.lower() + node_id_suffix
    dot_graph.node(
        node_name,
        label=node_label if node_label is not None else self.node_type.lower(),
        shape=_NODE_TYPES_TO_DOT_SHAPES[self.node_type.lower()],
    )
    if name:
      dot_graph.name = name
      dot_graph.graph_attr = {'label': name}

    return dot_graph, node_name

  def show(self) -> None:
    return ipython.display_if_ipython(self.dot_graph()[0])

  @property
  @abc.abstractmethod
  def name(self) -> Optional[str]:
    ...

  @name.setter
  @abc.abstractmethod
  def name(self, value: str):
    ...

  @property
  @abc.abstractmethod
  def node_id(self) -> Optional[int]:
    ...

  @node_id.setter
  @abc.abstractmethod
  def node_id(self, value: int):
    ...

  @abc.abstractmethod
  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    ...

  @property
  @abc.abstractmethod
  def decorators(self) -> Optional['Decorators']:
    ...

  @abc.abstractmethod
  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ):
    ...

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    if self.decorators is not None and self.decorators.condition is not None:
      self.decorators.condition.visit(containing_tree, callback)
    callback(containing_tree, self)

  @property
  def breakpoint(self) -> 'BreakpointType':
    if self.decorators is not None:
      return self.decorators.breakpoint_type
    return None

  def set_breakpoint(
      self, breakpoint_type: Optional['BreakpointType']
  ) -> 'Node':
    """Sets the breakpoint type on the decorator.

    Args:
      breakpoint_type: desired breakpoint type, None to remove type.

    Returns:
      Builder pattern, returns self.
    """
    decorators = self.decorators or Decorators()
    decorators.breakpoint_type = breakpoint_type
    self.set_decorators(decorators)
    return self

  @property
  def execution_mode(self) -> NodeExecutionMode:
    if (
        self.decorators is not None
        and self.decorators.execution_mode is not None
    ):
      return self.decorators.execution_mode
    return NodeExecutionMode.NORMAL

  def disable_execution(
      self,
      result_state: Optional[DisabledResultState] = None,
  ) -> 'Node':
    """Disables a node, so that it is not executed and appears to be skipped.

    Args:
      result_state: Optionally force the result of the execution to this state.
        If not set, the resulting state is automatically determined, so that the
        node is skipped.

    Returns:
      Builder pattern, returns self.
    """
    decorators = self.decorators or Decorators()
    decorators.execution_mode = NodeExecutionMode.DISABLED
    if result_state is not None:
      decorators.disabled_result_state = result_state
    self.set_decorators(decorators)
    return self

  def enable_execution(self) -> 'Node':
    """Enables a node, so that it will be executed.

    Returns:
      Builder pattern, returns self.
    """
    decorators = self.decorators or Decorators()
    decorators.execution_mode = None
    decorators.disabled_result_state = None
    self.set_decorators(decorators)
    return self


class Condition(abc.ABC):
  """Parent abstract base class for supported behavior tree conditions.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
  """

  @classmethod
  def create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.Condition
  ) -> 'Condition':
    """Instantiates a Condition instance from a proto."""
    if cls != Condition:
      raise TypeError(
          'create_from_proto can only be called on the Condition class'
      )
    condition_type = proto_object.WhichOneof('condition_type')
    # pylint:disable=protected-access
    # Intentionally using knowledge of subclasses in this parent class, so that
    # it is possible to provide a generic function to create the appropriate
    # subclass from a Condition proto.
    if condition_type == 'behavior_tree':
      return SubTreeCondition._create_from_proto(proto_object.behavior_tree)
    elif condition_type == 'blackboard':
      return Blackboard._create_from_proto(proto_object.blackboard)
    elif condition_type == 'domain_formula':
      raise NotImplementedError(
          'DomainFormular conditions are not yet supported.'
      )
    elif condition_type == 'all_of':
      return AllOf._create_from_proto(proto_object.all_of)
    elif condition_type == 'any_of':
      return AnyOf._create_from_proto(proto_object.any_of)
    elif condition_type == 'not':
      return Not._create_from_proto(getattr(proto_object, 'not'))
    else:
      raise TypeError('Unsupported proto condition type', condition_type)
    # pylint:enable=protected-access

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}()'

  @property
  @abc.abstractmethod
  def condition_type(self) -> str:
    ...

  @property
  @abc.abstractmethod
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    ...

  @abc.abstractmethod
  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    ...

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    callback(containing_tree, self)


class SubTreeCondition(Condition):
  """A BT condition of type SubTree.

  The outcome of the subtree determines the result of the condition. If the
  tree succeeds, the condition evaluates to true, if the tree fails, it
  evaluates to false.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
    tree: The subtree deciding the outcome of the condition.
  """

  tree: 'BehaviorTree'

  def __init__(self, tree: Union['BehaviorTree', 'Node', actions.ActionBase]):
    if tree is None:
      raise ValueError(
          'SubTreeCondition requires `tree` to be set to either a BehaviorTree,'
          ' Node, or a skill.'
      )
    if not isinstance(tree, BehaviorTree):
      node = _transform_to_optional_node(tree)
      tree = BehaviorTree(root=node)
    self.tree = tree

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}({str(self.tree)})'

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    proto_object = behavior_tree_pb2.BehaviorTree.Condition()
    proto_object.behavior_tree.CopyFrom(self.tree.proto)
    return proto_object

  @property
  def condition_type(self) -> str:
    return 'sub_tree'

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree
  ) -> 'SubTreeCondition':
    return cls(BehaviorTree.create_from_proto(proto_object))

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    tree_identifier = self.tree.print_python_code(skills, identifiers)
    identifier = _generate_unique_identifier('subtree_condition', identifiers)
    print(f'{identifier} = BT.SubTreeCondition(tree={tree_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.tree is not None:
      self.tree.visit(callback)


class Blackboard(Condition):
  """A BT condition of type Blackboard.

  Evaluates a boolean CEL expression with respect to a reference to a proto.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
    cel_expression: string containing a CEL expression evaluated on the
      blackboard.
  """

  def __init__(self, cel_expression: str):
    self.cel_expression: str = cel_expression

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}({self.cel_expression})'

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    proto_object = behavior_tree_pb2.BehaviorTree.Condition()
    proto_object.blackboard.cel_expression = self.cel_expression
    return proto_object

  @property
  def condition_type(self) -> str:
    return 'blackboard'

  @classmethod
  def _create_from_proto(
      cls,
      proto_object: behavior_tree_pb2.BehaviorTree.Condition.BlackboardExpression,
  ) -> 'Blackboard':
    return cls(proto_object.cel_expression)

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    identifier = _generate_unique_identifier(
        'blackboard_condition', identifiers
    )
    print(
        f'{identifier} = BT.Blackboard(cel_expression="{self.cel_expression}")'
    )
    return identifier


class CompoundCondition(Condition):
  """A base implementation for conditions composed of a number of conditions.

  Does not impose specific semantics on the children (these are to be defined
  by the sub-classes).

  Attributes:
    conditions: The list of conditions of the given condition.
    proto: The proto representation of the node.
  """

  def __init__(self, conditions: Optional[List['Condition']] = None):
    self.conditions: List['Condition'] = conditions or []

  def set_conditions(self, conditions: List['Condition']) -> 'Condition':
    self.conditions = conditions
    return self

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    representation = f'{type(self).__name__}([ '
    for condition in self.conditions:
      representation += f'{str(condition)} '
    representation += '])'
    return representation

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    identifier = _generate_unique_identifier(self.condition_type, identifiers)
    conditions = [
        c.print_python_code(identifiers, skills) for c in self.conditions
    ]
    print(
        f'{identifier} ='
        f' BT.{self.condition_type}(conditions=[{", ".join(conditions)}])'
    )
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    for condition in self.conditions:
      condition.visit(containing_tree, callback)


class AllOf(CompoundCondition):
  """A BehaviorTree condition encoding a boolean “and”.

  Compound of conditions, all of the sub-conditions need to be true.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
  """

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    proto_object = behavior_tree_pb2.BehaviorTree.Condition()
    if self.conditions:
      for condition in self.conditions:
        proto_object.all_of.conditions.append(condition.proto)
    else:
      proto_object.all_of.CopyFrom(
          behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
      )
    return proto_object

  @property
  def condition_type(self) -> str:
    return 'AllOf'

  @classmethod
  def _create_from_proto(
      cls,
      proto_object: behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound,
  ) -> 'AllOf':
    condition = cls()
    for condition_proto in proto_object.conditions:
      condition.conditions.append(Condition.create_from_proto(condition_proto))
    return condition


class AnyOf(CompoundCondition):
  """A BehaviorTree condition encoding a boolean “or”.

  Compound of conditions, any of the sub-conditions needs to be true.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
  """

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    proto_object = behavior_tree_pb2.BehaviorTree.Condition()
    if self.conditions:
      for condition in self.conditions:
        proto_object.any_of.conditions.append(condition.proto)
    else:
      proto_object.any_of.CopyFrom(
          behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound()
      )
    return proto_object

  @property
  def condition_type(self) -> str:
    return 'AnyOf'

  @classmethod
  def _create_from_proto(
      cls,
      proto_object: behavior_tree_pb2.BehaviorTree.Condition.LogicalCompound,
  ) -> 'AnyOf':
    condition = cls()
    for condition_proto in proto_object.conditions:
      condition.conditions.append(Condition.create_from_proto(condition_proto))
    return condition


class Not(Condition):
  """A BT condition of type Not.

  Negates a condition.

  Attributes:
    proto: The proto representation of the node.
    condition_type: A string label of the condition type.
    condition: The condition to negate.
  """

  def __init__(self, condition: 'Condition'):
    self.condition: 'Condition' = condition

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}({self.condition})'

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Condition:
    proto_object = behavior_tree_pb2.BehaviorTree.Condition()
    not_proto = getattr(proto_object, 'not')
    not_proto.CopyFrom(self.condition.proto)
    return proto_object

  @property
  def condition_type(self) -> str:
    return 'not'

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.Condition
  ) -> 'Not':
    return cls(Condition.create_from_proto(proto_object))

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    identifier = _generate_unique_identifier('not', identifiers)
    condition = self.condition.print_python_code(identifiers, skills)
    print(f'{identifier} = BT.Not(condition={condition})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.condition is not None:
      self.condition.visit(containing_tree, callback)


class Task(Node):
  """A BT node of type Task for behavior_tree_pb2.TaskNode.

  This node type is a thin wrapper around a plan action, which is a thin
  wrapper around a skill. Ultimately, a plan represented as a behavior tree
  is a set of task nodes, which are combined together using the other node
  types that guide the control flow of the plan.

  Attributes:
    proto: The proto representation of the node.
    node_type: A string label of the node type.
    result: A reference to the result value on the blackboard, if available.

  Raises:
    solutions_errors.InvalidArgumentError: Unknown action specification.
  """

  _action: Optional[actions.ActionBase]
  _behavior_call_proto: Optional[behavior_call_pb2.BehaviorCall]
  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      action: Union[actions.ActionBase, behavior_call_pb2.BehaviorCall],
      name: Optional[str] = None,
  ):
    self._behavior_call_proto = None
    self._decorators = None
    if isinstance(action, actions.ActionBase):
      self._behavior_call_proto = action.proto
      self._action = action
    elif isinstance(action, behavior_call_pb2.BehaviorCall):
      self._behavior_call_proto = action
    else:
      raise solutions_errors.InvalidArgumentError(
          f'Unknown action specification: {action}'
      )
    self._name = name
    self._node_id = None
    super().__init__()

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return f'{type(self).__name__}({self._name_repr()}action=behavior_call.Action(skill_id="{self._behavior_call_proto.skill_id}"))'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self._behavior_call_proto:
      proto_object.task.call_behavior.CopyFrom(self._behavior_call_proto)
    return proto_object

  @property
  def node_type(self) -> str:
    return 'task'

  @property
  def result(self) -> Optional[blackboard_value.BlackboardValue]:
    if self._action and hasattr(self._action, 'result'):
      return self._action.result
    return None

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.TaskNode
  ) -> 'Task':
    return cls(proto_object.call_behavior)

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    name = self._name or ''
    if self._behavior_call_proto:
      if name:
        name += f' ({self._behavior_call_proto.skill_id})'
      else:
        name += f'Skill {self._behavior_call_proto.skill_id}'
    return super().dot_graph(node_id_suffix, name)

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    behavior_call_action = behavior_call.Action(self.proto.task.call_behavior)
    name = self._name or self.proto.task.call_behavior.skill_id
    identifier_prefix = name.replace('.', '_')

    call_identifier = _generate_unique_identifier(
        identifier_prefix + '_behavior_call',
        identifiers,
    )
    task_identifier = _generate_unique_identifier(
        identifier_prefix, identifiers
    )
    print(
        behavior_call_action.to_python(
            prefix_options=utils.PrefixOptions(),
            identifier=call_identifier,
            skills=skills,
        )
    )
    print(
        f'{task_identifier} = BT.Task(name="{name}", action={call_identifier})'
    )
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{task_identifier}.set_decorators({decorator_identifier})')
    return task_identifier


class SubTree(Node):
  """A BT node of type SubTree for behavior_tree_pb2.SubTreeNode.

  This node is usually used to group components into a subtree.

  Attributes:
    behavior_tree: The subtree, a BehaviorTree object.
    name: The name of the subtree node.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      behavior_tree: Optional[Union['Node', 'BehaviorTree']] = None,
      name: Optional[str] = None,
  ):
    """Creates a SubTree node.

    Args:
      behavior_tree: behavior tree or root node of a tree for this subtree. If
        passing a root node you must also provide the name argument.
      name: name of the behavior tree, if behavior_tree is a node, i.e., a root
        node of a tree; otherwise, the name of this node.
    """
    self.behavior_tree: Optional['BehaviorTree'] = None
    self._decorators = None
    self._name = None
    self._node_id = None
    if behavior_tree is not None:
      self.set_behavior_tree(behavior_tree, name)
    else:
      self._name = name
    super().__init__()

  def set_behavior_tree(
      self,
      behavior_tree: Union['Node', 'BehaviorTree'],
      name: Optional[str] = None,
  ) -> 'SubTree':
    """Sets the subtree's behavior tree.

    Args:
      behavior_tree: behavior tree or root node of a tree for this subtree. If
        passing a root node you must also provide the name argument.
      name: name of the behavior tree, if behavior_tree is a node, i.e., a root
        node of a tree; otherwise, the name of this node.

    Returns:
      self for chaining.
    """
    if isinstance(behavior_tree, BehaviorTree):
      self.behavior_tree = behavior_tree
      self._name = name
    elif isinstance(behavior_tree, Node):
      if name is None:
        raise ValueError(
            'You must give a name when passing a root node for a tree.'
        )
      self.behavior_tree = BehaviorTree(name=name, root=behavior_tree)
    else:
      raise TypeError('Given behavior_tree is not a BehaviorTree.')
    return self

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    if not self.behavior_tree:
      return f'{type(self).__name__}({self._name_repr()})'
    else:
      return f'{type(self).__name__}({self._name_repr()}behavior_tree={repr(self.behavior_tree)})'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self.behavior_tree is None:
      raise ValueError(
          'A SubTree node has not been set. Please call '
          'sub_tree_node_instance.set_behavior_tree(tree_instance).'
      )
    proto_object.sub_tree.tree.CopyFrom(self.behavior_tree.proto)
    return proto_object

  @property
  def node_type(self) -> str:
    return 'sub_tree'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.SubtreeNode
  ) -> 'SubTree':
    return cls(behavior_tree=BehaviorTree.create_from_proto(proto_object.tree))

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    """Converts the given subtree into a graphviz dot graph.

    The edge goes from parent to the root node of the subtree.

    Args:
      node_id_suffix: A little string with the suffix to make the given node
        unique in the dot graph.

    Returns:
      A tuple of graphviz dot graph representation of the full subtree and
      the name of the subtree's root node.
    """
    child_dot_graph = None
    child_node_name = ''
    if self.behavior_tree is not None and self.behavior_tree.root is not None:
      child_dot_graph, child_node_name = self.behavior_tree.root.dot_graph(
          node_id_suffix + '_0'
      )
    else:
      return super().dot_graph(node_id_suffix)

    box_dot_graph = _dot_wrap_in_box(
        child_graph=child_dot_graph,
        name=self.behavior_tree.name,
        label=self.behavior_tree.name,
    )
    return box_dot_graph, child_node_name

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    tree_identifier = self.behavior_tree.root.print_python_code(
        identifiers, skills=skills
    )
    name = self._name if hasattr(self, '_name') and self._name else 'subtree'
    identifier = _generate_unique_identifier(name, identifiers)
    print(
        f"{identifier} = BT.SubTree(name='{name or tree_identifier}',"
        f' behavior_tree={tree_identifier})'
    )
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.behavior_tree is not None:
      self.behavior_tree.visit(callback)


class Fail(Node):
  """A BT node of type Fail for behavior_tree_pb2.BehaviorTree.FailNode.

  A node that can be used to signal a failure. Most used to direct the control
  flow of execution, in combination with a failure handling strategy.

  Attributes:
    failure_message: A string that gives more information about the failure,
      mostly for the user's convenience.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(self, failure_message: str = '', name: Optional[str] = None):
    self._decorators = None
    self.failure_message: str = failure_message
    self._name = name
    self._node_id = None
    super().__init__()

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    rep = f'{type(self).__name__}({self._name_repr()}'
    if self.failure_message:
      rep += f'failure_message="{self.failure_message}"'
    rep += ')'
    return rep

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    proto_object.fail.failure_message = self.failure_message
    return proto_object

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def node_type(self) -> str:
    return 'fail'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.FailNode
  ) -> 'Fail':
    return cls(proto_object.failure_message)

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    return super().dot_graph(node_id_suffix=node_id_suffix, name=self._name)

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    identifier = _generate_unique_identifier(
        self._name or 'fail_node', identifiers
    )
    failure = ''
    if self.failure_message:
      failure = f', failure_message="{self.failure_message}"'
    print(f'{identifier} = BT.Fail(name="{self._name or identifier}"{failure})')
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier


class NodeWithChildren(Node):
  """A parent class for any behavior tree node that has self.children.

  Attributes:
    children: The list of child nodes of the given node.
    proto: The proto representation of the node.
  """

  def __init__(
      self,
      children: Optional[SequenceType[Union['Node', actions.ActionBase]]],
  ):
    if not children:
      self.children = []
    else:
      self.children: List['Node'] = [  # pytype: disable=annotation-type-mismatch  # always-use-return-annotations
          _transform_to_optional_node(x) for x in children
      ]
    super().__init__()

  def set_children(self, *children: 'Node') -> 'Node':
    if isinstance(children[0], list):
      self.children = [_transform_to_optional_node(x) for x in children[0]]  # pytype: disable=annotation-type-mismatch  # always-use-return-annotations
    else:
      self.children = [_transform_to_optional_node(x) for x in children]  # pytype: disable=annotation-type-mismatch  # always-use-return-annotations

    return self

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    representation = f'{type(self).__name__}({self._name_repr()}children=['
    representation += ', '.join(map(str, self.children))
    representation += '])'
    return representation

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    dot_graph, node_name = super().dot_graph(
        node_id_suffix=node_id_suffix, name=self.name
    )
    _dot_append_children(dot_graph, node_name, self.children, node_id_suffix, 0)
    box_dot_graph = _dot_wrap_in_box(
        child_graph=dot_graph,
        name=(self.name or '') + node_id_suffix,
        label=self.name or '',
    )
    return box_dot_graph, node_name

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    name = self.name if self.name else self.node_type
    identifier = _generate_unique_identifier(name, identifiers)
    children_identifier = [
        c.print_python_code(identifiers, skills) for c in self.children
    ]
    print(
        f'{identifier} ='
        f' BT.{self.node_type}(name="{name}",'
        f' children=[{", ".join(children_identifier)}])'
    )
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    for child in self.children:
      child.visit(containing_tree, callback)


class Sequence(NodeWithChildren):
  """A BT node of type Sequence.

  Represented in the proto as behavior_tree_pb2.BehaviorTree.SequenceNode.

  The child nodes are executed sequentially. If any of the children fail,
  the node fails. If all the children succeed, the node succeeds.

  Attributes:
    children: The list of child nodes of the given node, inherited from the
      parent class.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      children: Optional[
          SequenceType[Union['Node', actions.ActionBase]]
      ] = None,
      name: Optional[str] = None,
  ):
    super().__init__(children=children)
    self._decorators = None
    self._name = name
    self._node_id = None

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self.children:
      for child in self.children:
        proto_object.sequence.children.append(child.proto)
    else:
      proto_object.sequence.CopyFrom(
          behavior_tree_pb2.BehaviorTree.SequenceNode()
      )
    return proto_object

  @property
  def node_type(self) -> str:
    return 'Sequence'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.SequenceNode
  ) -> 'Sequence':
    node = cls()
    for child_node_proto in proto_object.children:
      node.children.append(Node.create_from_proto(child_node_proto))
    return node


class Parallel(NodeWithChildren):
  """BT node of type Parallel for behavior_tree_pb2.BehaviorTree.ParallelNode.

  The child nodes are all executed in parallel. Once all the children finish
  successfully, the node succeeds as well. If any of the children fail, the
  node fails.

  Attributes:
    failure_behavior: Enum specifying how the node should fail.
    children: The list of child nodes of the given node, inherited from the
      parent class.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  class FailureBehavior(enum.IntEnum):
    """Specifies how a parallel node should fail.

    See intrinsic_proto.executive.BehaviorTree.ParallelNode.FailureBehavior
    for details.
    """

    DEFAULT = behavior_tree_pb2.BehaviorTree.ParallelNode.DEFAULT
    WAIT_FOR_REMAINING_CHILDREN = (
        behavior_tree_pb2.BehaviorTree.ParallelNode.WAIT_FOR_REMAINING_CHILDREN
    )

  failure_behavior: FailureBehavior

  def __init__(
      self,
      children: Optional[
          SequenceType[Union['Node', actions.ActionBase]]
      ] = None,
      failure_behavior: FailureBehavior = FailureBehavior.DEFAULT,
      name: Optional[str] = None,
  ):
    super().__init__(children)
    self._decorators = None
    self._name = name
    self._node_id = None
    self.failure_behavior = failure_behavior

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self.children:
      for child in self.children:
        proto_object.parallel.children.append(child.proto)
    else:
      proto_object.parallel.CopyFrom(
          behavior_tree_pb2.BehaviorTree.ParallelNode()
      )

    proto_object.parallel.failure_behavior = self.failure_behavior.value
    return proto_object

  @property
  def node_type(self) -> str:
    return 'Parallel'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.ParallelNode
  ) -> 'Parallel':
    node = cls(
        failure_behavior=cls.FailureBehavior(proto_object.failure_behavior),
    )
    for child_node_proto in proto_object.children:
      node.children.append(Node.create_from_proto(child_node_proto))
    return node


class Selector(NodeWithChildren):
  """BT node of type Selector for behavior_tree_pb2.BehaviorTree.SelectorNode.

  The child nodes get executed in a sequence until any one of them succeeds.
  That is, first, the first child is executed, if that one fails, the next one
  is executed, and so on. Once any of the children succeed, the node succeeds.
  If all the children fail, the node fails.

  Attributes:
    children: The list of child nodes of the given node, inherited from the
      parent class.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      children: Optional[
          SequenceType[Union['Node', actions.ActionBase]]
      ] = None,
      name: Optional[str] = None,
  ):
    super().__init__(children=children)
    self._decorators = None
    self._name = name
    self._node_id = None

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self.children:
      for child in self.children:
        proto_object.selector.children.append(child.proto)
    else:
      proto_object.selector.CopyFrom(
          behavior_tree_pb2.BehaviorTree.SelectorNode()
      )
    return proto_object

  @property
  def node_type(self) -> str:
    return 'Selector'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.SelectorNode
  ) -> 'Selector':
    node = cls()
    for child_node_proto in proto_object.children:
      node.children.append(Node.create_from_proto(child_node_proto))
    return node


class Retry(Node):
  """BT node of type Retry for behavior_tree_pb2.BehaviorTree.RetryNode.

  Runs the child node and retries if the child fails. After the given number
  of retries, the failure gets propagated up.

  Attributes:
    child: The child node of this node that is to be retried upon failure.
    recovery: An optional sub-tree that is executed if the child fails and there
      are still tries left to be performed. If the recovery fails, the retry
      node will fail immediately irrespective of the number of tries left.
    max_tries: Maximal number of times to execute the child before propagating
      the failure up.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
    retry_counter: The key to access the retry counter on the blackboard, only
      available while inside the retry node.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]
  child: Optional['Node']
  recovery: Optional['Node']
  max_tries: int

  def __init__(
      self,
      max_tries: int = 0,
      child: Optional[Union['Node', actions.ActionBase]] = None,
      recovery: Optional[Union['Node', actions.ActionBase]] = None,
      name: Optional[str] = None,
      retry_counter_key: Optional[str] = None,
  ):
    self._decorators = None
    self.child = _transform_to_optional_node(child)
    self.recovery = _transform_to_optional_node(recovery)
    self.max_tries = max_tries
    self._name = name
    self._node_id = None
    self._retry_counter_key = retry_counter_key or 'retry_counter_' + str(
        uuid.uuid4()
    ).replace('-', '_')
    super().__init__()

  def set_child(self, child: Union['Node', actions.ActionBase]) -> 'Retry':
    self.child = _transform_to_optional_node(child)
    return self

  def set_recovery(
      self, recovery: Union['Node', actions.ActionBase]
  ) -> 'Retry':
    self.recovery = _transform_to_optional_node(recovery)
    return self

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    recovery_str = f', recovery={str(self.recovery)}'
    return (
        f'{type(self).__name__}({self._name_repr()}max_tries={self.max_tries},'
        f' child={str(self.child)}{recovery_str})'
    )

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    proto_object.retry.max_tries = self.max_tries
    if self.child is None:
      raise ValueError(
          'A Retry node has to have a child node but currently '
          'it is not set. Please call '
          'retry_node_instance.set_child(bt_node_instance).'
      )
    proto_object.retry.child.CopyFrom(self.child.proto)
    if self.recovery is not None:
      proto_object.retry.recovery.CopyFrom(self.recovery.proto)
    proto_object.retry.retry_counter_blackboard_key = self._retry_counter_key
    return proto_object

  @property
  def retry_counter(self) -> str:
    return self._retry_counter_key

  @property
  def node_type(self) -> str:
    return 'retry'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.RetryNode
  ) -> 'Retry':
    retry = cls(
        max_tries=proto_object.max_tries,
        child=Node.create_from_proto(proto_object.child),
    )
    if proto_object.HasField('recovery'):
      retry.recovery = Node.create_from_proto(proto_object.recovery)
    retry._retry_counter_key = proto_object.retry_counter_blackboard_key
    return retry

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    dot_graph, node_name = super().dot_graph(
        node_id_suffix, 'retry ' + str(self.max_tries), self._name
    )
    if self.child is not None:
      _dot_append_child(
          dot_graph, node_name, self.child, node_id_suffix + '_child'
      )
    if self.recovery is not None:
      _dot_append_child(
          dot_graph,
          node_name,
          self.recovery,
          node_id_suffix + '_recovery',
          edge_label='Recovery',
      )
    box_dot_graph = _dot_wrap_in_box(
        child_graph=dot_graph,
        name=(self._name or '') + node_id_suffix,
        label=self._name or '',
    )
    return box_dot_graph, node_name

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    child_identifier = self.child.print_python_code(identifiers, skills)
    recovery_identifier = None
    if self.recovery is not None:
      recovery_identifier = self.recovery.print_python_code(identifiers, skills)
    name = self._name if self._name else 'retry'
    identifier = _generate_unique_identifier(name, identifiers)
    print(
        f'{identifier} = BT.Retry(name="{name}",'
        f' child={child_identifier}, recovery={recovery_identifier},'
        f' max_tries={self.max_tries},'
        f' retry_counter_key="{self._retry_counter_key}")'
    )
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.child is not None:
      self.child.visit(containing_tree, callback)
    if self.recovery is not None:
      self.recovery.visit(containing_tree, callback)


class Fallback(NodeWithChildren):
  """BT node of type Fallback for behavior_tree_pb2.BehaviorTree.FallbackNode.

  A fallback node will try a number of actions until one succeeds, or all
  fail. It can be used to implement trees that try a number of options.

  Attributes:
    children: The list of child nodes of the given node, inherited from the
      parent class.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      children: Optional[
          SequenceType[Union['Node', actions.ActionBase]]
      ] = None,
      name: Optional[str] = None,
  ):
    super().__init__(children=children)
    self._decorators = None
    self._name = name
    self._node_id = None

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    proto_object = super().proto
    if self.children:
      for child in self.children:
        proto_object.fallback.children.append(child.proto)
    else:
      proto_object.fallback.CopyFrom(
          behavior_tree_pb2.BehaviorTree.FallbackNode()
      )
    return proto_object

  @property
  def node_type(self) -> str:
    return 'Fallback'

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.FallbackNode
  ) -> 'Fallback':
    node = cls()
    for child_node_proto in proto_object.children:
      node.children.append(Node.create_from_proto(child_node_proto))
    return node


class Loop(Node):
  """BT node of type Loop for behavior_tree_pb2.BehaviorTree.LoopNode.

  The loop node provides the ability to run a subtree repeatedly. It supports
  different bounding conditions: run until failure, run while a condition
  holds (while loop), or run a maximum number of times (for loops with break
  on error).

  When selected and a `while` condition is set, the condition is immediately
  evaluated. If it is satisfied, or if no `while` condition is given, the `do`
  child is executed. If `max_times` is not given or zero, the parameter is
  ignored.

  Additionally, if no `while` condition is added, the loop will run
  indefinitely until the child `do` child fails (taking on the semantics of a
  for-loop). If `max_times` is set, the loop will end after the given number
  of iterations, or if the `do` child fails.

  Attributes:
    do_child: The child node of this node that is to be run repeatedly.
    max_times: Maximal number of times to execute the child.
    while_condition: condition which indicates whether do should be executed.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
    loop_counter: The key to access the loop counter on the blackboard, only
      available while inside the loop.
    for_each_protos: List of pre-defined protos to iterate over.
    for_each_value_key: The key to access the current value on the blackboard
      during for each loops.
    for_each_value: BlackboardValue that refers to the current iteration value.
      Only available when for_each_generator_cel_expression was set from a
      BlackboardValue via set_for_each_generator.
    for_each_generator_cel_expression: CEL expression to generate a list of
      protos. The loop iterates over the result of this list.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]
  _for_each_value_key: Optional[str]
  _for_each_value: Optional[blackboard_value.BlackboardValue]
  _for_each_protos: Optional[List[protobuf_message.Message]]
  _for_each_generator_cel_expression: Optional[str]

  def __init__(
      self,
      max_times: int = 0,
      do_child: Optional[Union['Node', actions.ActionBase]] = None,
      while_condition: Optional['Condition'] = None,
      name: Optional[str] = None,
      loop_counter_key: Optional[str] = None,
      *,
      for_each_value_key: Optional[str] = None,
      for_each_protos: Optional[
          List[Union[protobuf_message.Message, skill_utils.MessageWrapper]]
      ] = None,
      for_each_generator_cel_expression: Optional[str] = None,
  ):
    self._decorators = None

    self.do_child: Optional['Node'] = _transform_to_optional_node(do_child)
    self.max_times: int = max_times
    self.while_condition: Optional['Condition'] = while_condition
    self._loop_counter_key = loop_counter_key or 'loop_counter_' + str(
        uuid.uuid4()
    ).replace('-', '_')
    self._name = name
    self._node_id = None
    self._for_each_value_key = for_each_value_key
    self._for_each_value = None
    self._for_each_protos = Loop._for_each_proto_input_to_protos(
        for_each_protos
    )
    self._for_each_generator_cel_expression = for_each_generator_cel_expression
    if (
        self._for_each_protos is not None
        or self._for_each_generator_cel_expression is not None
    ):
      self._ensure_for_each_value_key()
    self._check_consistency()
    super().__init__()

  def set_do_child(self, do_child: Union['Node', actions.ActionBase]) -> 'Loop':
    self.do_child = _transform_to_optional_node(do_child)
    return self

  def set_while_condition(self, while_condition: 'Condition') -> 'Loop':
    """Sets the while condition for the loop.

    Setting it will make this loop node work as a while loop.

    Args:
      while_condition: The condition to set.

    Returns:
      The modified loop node.
    """
    self.while_condition = while_condition
    self._check_consistency()
    return self

  def set_for_each_value_key(self, key: Optional[str]) -> 'Loop':
    """Sets the blackboard key for the current value of a for each loop.

    Setting it anything other than 'None', will make this loop node work as a
    for each loop.

    Args:
      key: The blackboard key to set. Use 'None' to unset this property.

    Returns:
      The modified loop node.
    """
    self._for_each_value_key = key
    if self._for_each_value is not None:
      self._for_each_value.set_root_value_access_path(key)
    self._check_consistency()
    return self

  def set_for_each_protos(
      self,
      protos: Optional[
          List[
              Union[
                  protobuf_message.Message,
                  skill_utils.MessageWrapper,
                  object_world_resources.WorldObject,
                  object_world_resources.Frame,
              ]
          ]
      ],
  ) -> 'Loop':
    """Sets the messages to iterate over in a for each loop.

    The proto messages are packed into Any protos when the loop node is
    represented as a proto unless they are already an Any proto, in which case
    they are taken as is.
    Setting this make the loop node work as a for each loop.

    Args:
      protos: A list of protos to iterate over. If the list contains
        WorldObjects or Frames these are converted to a proto referencing the
        WorldObject or Frame.

    Returns:
      The modified loop node.
    """
    self._for_each_protos = Loop._for_each_proto_input_to_protos(protos)
    self._check_consistency()
    self._ensure_for_each_value_key()
    return self

  def set_for_each_generator(
      self, generator_value: blackboard_value.BlackboardValue
  ) -> 'Loop':
    """Sets the value to generate protos from to loop over in a for each loop.

    The passed in value must refer to a list of protos to iterate over in this
    for each loop. A common example is a repeated field in a skill result.
    When the loop node is selected for execution the list of protos is copied
    from the referred value and then the loop node is cycled for each of the
    values in the list.
    The value can also result in an AnyList proto, in which case the loop node
    iterates over each entry in the AnyList items field.
    Setting it anything other than 'None', will make this loop node work as a
    for each loop.

    Args:
      generator_value: The value to iterate over.

    Returns:
      The modified loop node.
    """
    self.set_for_each_generator_cel_expression(
        generator_value.value_access_path()
    )
    self._for_each_value = generator_value[0]
    self._for_each_value.set_root_value_access_path(self._for_each_value_key)
    return self

  def set_for_each_generator_cel_expression(
      self, cel_expression: Optional[str]
  ) -> 'Loop':
    """Sets the CEL expression to generate protos for a for each loop.

    When this loop node is selected for execution this CEL expression will be
    evaluated and it must either result in a list of protos to iterate over or
    an AnyList proto.
    Setting it anything other than 'None', will make this loop node work as a
    for each loop.

    Args:
      cel_expression: The expression to generate protos to loop over.

    Returns:
      The modified loop node.
    """
    self._for_each_generator_cel_expression = cel_expression
    self._check_consistency()
    self._ensure_for_each_value_key()
    return self

  @classmethod
  def _for_each_proto_input_to_protos(
      cls,
      inputs: Optional[
          List[
              Union[
                  protobuf_message.Message,
                  skill_utils.MessageWrapper,
                  object_world_resources.WorldObject,
                  object_world_resources.Frame,
              ]
          ]
      ],
  ) -> Optional[List[protobuf_message.Message]]:
    """Converts a list of possible inputs for the protos list to protos.

    For each loop nodes can only iterate over protos. It is often convenient
    to accept things like WorldObjects directly without the user having to
    convert this into a reference proto manually. Also protos in the solutions
    API are represented by MessageWrapper objects that are not directly a
    proto, but contain/wrap one.
    This functions performs the necessary conversions to proto when necessary.

    Args:
      inputs: List of values that can either be a proto message directly or a
        MessageWrapper. WorldObjects and Frames are also accepted and
        automatically converted to a proto referencing the WorldObject or Frame.

    Returns:
      A list of protos converted from the list of mixed inputs.
    """
    if inputs is None:
      return None
    if not inputs:
      raise solutions_errors.InvalidArgumentError(
          'Loop for_each protos cannot be empty'
      )
    protos: List[protobuf_message.Message] = []
    for value in inputs:
      if isinstance(value, protobuf_message.Message):
        protos.append(value)
      elif isinstance(value, skill_utils.MessageWrapper):
        if value.wrapped_message is not None:
          protos.append(value.wrapped_message)  # pytype: disable=container-type-mismatch
      elif isinstance(value, object_world_resources.WorldObject):
        wo: object_world_resources.WorldObject = value
        protos.append(wo.reference)
      elif isinstance(value, object_world_resources.Frame):
        frame: object_world_resources.Frame = value
        protos.append(frame.reference)
      else:
        raise solutions_errors.InvalidArgumentError(
            f'Cannot set for_each proto "{str(value)}". Only protos or world'
            ' objects or frames are supported.'
        )
    return protos  # pytype: disable=bad-return-type

  def _ensure_for_each_value_key(self):
    """Ensures that a _for_each_value_key is present.

    If a key is already set, nothing is done. Otherwise a key with a random
    UUID is created.
    """
    if not self._for_each_value_key:
      self._for_each_value_key = 'for_each_value_' + str(uuid.uuid4()).replace(
          '-', '_'
      )

  def validate(self):
    """Validates the current loop node.

    Checks that the loop node is properly defined, i.e., there are no
    inconsistent properties set and all required fields are set.

    Raises:
      InvalidArgumentError: raised if the node is in a state that cannot be
        converted to a valid proto.
    """
    self._check_consistency()
    if (
        self._for_each_value_key is not None
        and self._for_each_generator_cel_expression is None
        and self._for_each_protos is None
    ):
      raise solutions_errors.InvalidArgumentError(
          'Loop node defines a for_each_value_key, but no way to generate'
          ' values to iterate over. Set either for_each_protos or'
          ' for_each_generator_cel_expression.'
      )

  def _check_consistency(self):
    """Checks necessary invariants of the loop node.

    This function only determines if fields are set that are inconsistent with
    each other, but not if all required fields are set.

    Raises:
      InvalidArgumentError: raised if the node is in a state that cannot be
        converted to a valid proto.
    """
    for_each_set_fields = []
    if self._for_each_value_key is not None:
      for_each_set_fields.append('for_each_value_key')
    if self._for_each_protos is not None:
      for_each_set_fields.append('for_each_protos')
    if self._for_each_generator_cel_expression is not None:
      for_each_set_fields.append('for_each_generator_cel_expression')
    if for_each_set_fields and self.while_condition is not None:
      raise solutions_errors.InvalidArgumentError(
          'Loop node defines for each properties'
          f' ({", ".join(for_each_set_fields)}) and a while condition. Only'
          ' one of these can be set at a time.'
      )
    if (
        self._for_each_protos is not None
        and self._for_each_generator_cel_expression is not None
    ):
      raise solutions_errors.InvalidArgumentError(
          'Loop node with for each defines both for_each_protos and a'
          ' for_each_generator_cel_expression. Exactly one must be defined.'
      )

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    representation = f'{type(self).__name__}'
    if self._for_each_generator_cel_expression is not None:
      representation += f' over {self._for_each_generator_cel_expression}'
    if self._for_each_protos is not None:
      representation += f' over {len(self._for_each_protos)} protos'
    representation += f'({self._name_repr()}'
    if self.while_condition is not None:
      representation += f'while_condition={repr(self.while_condition)}, '
    if self.max_times != 0:
      representation += f'max_times={self.max_times}, '
    representation += f'do_child={repr(self.do_child)})'
    return representation

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    self.validate()
    proto_object = super().proto
    if self.while_condition is not None:
      condition = getattr(proto_object.loop, 'while')
      condition.CopyFrom(self.while_condition.proto)
    if self._for_each_value_key is not None:
      proto_object.loop.for_each.value_blackboard_key = self._for_each_value_key
    if self._for_each_generator_cel_expression is not None:
      proto_object.loop.for_each.generator_cel_expression = (
          self._for_each_generator_cel_expression
      )
    if self._for_each_protos:
      any_list = getattr(proto_object.loop.for_each, 'protos')
      for proto in self._for_each_protos:
        if proto.DESCRIPTOR.full_name == 'google.protobuf.Any':
          any_proto = any_list.items.add()
          any_proto.CopyFrom(proto)
        else:
          any_proto = any_list.items.add()
          any_proto.Pack(proto)

    proto_object.loop.max_times = self.max_times
    if self.do_child is None:
      raise ValueError(
          'A Loop node has to have a do child node but currently '
          'it is not set. Please call '
          'loop_node_instance.set_do_child(bt_node_instance).'
      )
    proto_object.loop.do.CopyFrom(self.do_child.proto)
    proto_object.loop.loop_counter_blackboard_key = self._loop_counter_key
    return proto_object

  @property
  def loop_counter(self) -> str:
    return self._loop_counter_key

  @property
  def for_each_value_key(self) -> Optional[str]:
    return self._for_each_value_key

  @property
  def for_each_value(self) -> blackboard_value.BlackboardValue:
    if self._for_each_value is None:
      raise ValueError(
          'for_each_value is only available, when the for each loop was'
          ' configured with set_for_each_generator().'
      )
    return self._for_each_value

  @property
  def for_each_protos(self) -> Optional[List[protobuf_message.Message]]:
    return self._for_each_protos

  @property
  def for_each_generator_cel_expression(self) -> Optional[str]:
    return self._for_each_generator_cel_expression

  @property
  def node_type(self) -> str:
    return 'loop'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.LoopNode
  ) -> 'Loop':
    """Created a Loop node class from a LoopNode proto."""
    condition = None
    if proto_object.HasField('while'):
      condition = Condition.create_from_proto(getattr(proto_object, 'while'))

    for_each_value_key = None
    for_each_protos = None
    for_each_generator_cel_expression = None
    if proto_object.HasField('for_each'):
      for_each_field = proto_object.for_each
      if for_each_field.value_blackboard_key:
        for_each_value_key = for_each_field.value_blackboard_key
      if for_each_field.HasField('protos'):
        for_each_protos = [proto for proto in for_each_field.protos.items]
      if (
          for_each_field.HasField('generator_cel_expression')
          and for_each_field.generator_cel_expression
      ):
        for_each_generator_cel_expression = (
            for_each_field.generator_cel_expression
        )

    loop = cls(
        max_times=proto_object.max_times,
        do_child=Node.create_from_proto(proto_object.do),
        while_condition=condition,
        loop_counter_key=proto_object.loop_counter_blackboard_key,
        for_each_value_key=for_each_value_key,
        for_each_protos=for_each_protos,
        for_each_generator_cel_expression=for_each_generator_cel_expression,
    )
    return loop

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    label = 'loop'
    if self.max_times:
      label += ' ' + str(self.max_times)
    if self.while_condition:
      label += ' + while condition'
    if (
        self._for_each_generator_cel_expression is not None
        or self._for_each_protos is not None
    ):
      label += ' + for_each'

    dot_graph, node_name = super().dot_graph(node_id_suffix, label, self._name)
    if self.do_child is not None:
      _dot_append_child(
          dot_graph, node_name, self.do_child, node_id_suffix + '_0'
      )

    box_dot_graph = _dot_wrap_in_box(
        child_graph=dot_graph,
        name=(self._name or '') + node_id_suffix,
        label=self._name or '',
    )
    return box_dot_graph, node_name

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    child_identifier = self.do_child.print_python_code(identifiers, skills)
    condition_string = ''
    if self.while_condition:
      condition_identifier = self.while_condition.print_python_code(
          identifiers, skills
      )
      condition_string = ', while_condition=' + condition_identifier
    for_each_string = ''
    if self._for_each_value_key:
      for_each_string += f', for_each_value_key="{self._for_each_value_key}"'
    if self._for_each_generator_cel_expression:
      for_each_string += (
          f', for_each_generator_cel_expression={self._for_each_generator_cel_expression}'
      )
    if self._for_each_protos:
      for_each_string += ', for_each_protos=['
      for proto in self._for_each_protos:
        any_proto = any_pb2.Any()
        if isinstance(proto, any_pb2.Any):
          any_proto = proto
        else:
          any_proto.Pack(proto)
        for_each_string += (
            f'any_pb2.Any(type_url="{any_proto.type_url}",'
            f' value={any_proto.value}), '
        )
      for_each_string += ']'
    name = self._name if self._name else 'loop'
    identifier = _generate_unique_identifier(name, identifiers)
    print(
        f'{identifier} = BT.Loop(name="{name}",'
        f' do_child={child_identifier}, max_times={self.max_times},'
        f' loop_counter_key="{self._loop_counter_key}"{condition_string}{for_each_string})'
    )
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.while_condition is not None:
      self.while_condition.visit(containing_tree, callback)
    if self.do_child is not None:
      self.do_child.visit(containing_tree, callback)


class Branch(Node):
  """BT node of type Branch for behavior_tree_pb2.BehaviorTree.BranchNode.

  A branch node has a condition and two designated children. On selection, it
  evaluates the condition. If the condition is satisfied, the `then` child is
  selected, otherwise the `else` child is selected.

  Attributes:
    if_condition: condition which indicates which child should be executed.
    then_child: Child to execute if the condition succeeds.
    else_child: Child to execute if the condition fails.
    proto: The proto representation of the node.
    node_type: A string label of the node type.
  """

  _decorators: Optional['Decorators']
  _name: Optional[str]
  _node_id: Optional[int]

  def __init__(
      self,
      if_condition: Optional['Condition'] = None,
      then_child: Optional[Union['Node', actions.ActionBase]] = None,
      else_child: Optional[Union['Node', actions.ActionBase]] = None,
      name: Optional[str] = None,
  ):
    self._decorators = None
    self.then_child: Optional['Node'] = _transform_to_optional_node(then_child)
    self.else_child: Optional['Node'] = _transform_to_optional_node(else_child)
    self.if_condition: Optional['Condition'] = if_condition
    self._name = name
    self._node_id = None
    super().__init__()

  def set_then_child(
      self, then_child: Union['Node', actions.ActionBase]
  ) -> 'Branch':
    self.then_child = _transform_to_optional_node(then_child)
    return self

  def set_else_child(
      self, else_child: Union['Node', actions.ActionBase]
  ) -> 'Branch':
    self.else_child = _transform_to_optional_node(else_child)
    return self

  def set_if_condition(self, if_condition: 'Condition') -> 'Branch':
    self.if_condition = if_condition
    return self

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    representation = f'{type(self).__name__}({self._name_repr()}'
    if self.if_condition is not None:
      representation += f'if_condition={repr(self.if_condition)}, '
    if self.then_child is not None:
      representation += f'then_child={repr(self.then_child)}, '
    if self.else_child is not None:
      representation += f'else_child={repr(self.else_child)}'
    representation += ')'
    return representation

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    if self.if_condition is None:
      raise ValueError(
          'A Branch node has to have a if condition but currently '
          'it is not set. Please call '
          'branch_node_instance.set_if_condition(condition_instance).'
      )
    if self.then_child is None and self.else_child is None:
      raise ValueError(
          'Branch node has neither a then nor an else child set. Please set '
          'at least one of them.'
      )

    proto_message = super().proto
    condition = getattr(proto_message.branch, 'if')
    condition.CopyFrom(self.if_condition.proto)

    if self.then_child is not None:
      proto_message.branch.then.CopyFrom(self.then_child.proto)
    if self.else_child is not None:
      else_proto = getattr(proto_message.branch, 'else')
      else_proto.CopyFrom(self.else_child.proto)
    return proto_message

  @property
  def node_type(self) -> str:
    return 'branch'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.BranchNode
  ) -> 'Branch':
    """Creates a Branch node class from a BranchNode proto."""
    then_child = None
    else_child = None
    if proto_object.HasField('then'):
      then_child = Node.create_from_proto(proto_object.then)
    if proto_object.HasField('else'):
      else_child = Node.create_from_proto(getattr(proto_object, 'else'))
    branch = cls(
        if_condition=Condition.create_from_proto(getattr(proto_object, 'if')),
        then_child=then_child,
        else_child=else_child,
    )
    return branch

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    dot_graph, node_name = super().dot_graph(
        node_id_suffix=node_id_suffix, name=self._name
    )
    if self.then_child is not None:
      _dot_append_child(
          dot_graph,
          node_name,
          self.then_child,
          node_id_suffix + '_1',
          edge_label='then',
      )
    if self.else_child is not None:
      _dot_append_child(
          dot_graph,
          node_name,
          self.else_child,
          node_id_suffix + '_2',
          edge_label='else',
      )
    box_dot_graph = _dot_wrap_in_box(
        child_graph=dot_graph,
        name=(self._name or '') + node_id_suffix,
        label=self._name or '',
    )
    return box_dot_graph, node_name

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    name = self._name if self._name else 'branch'
    identifier = _generate_unique_identifier(name, identifiers)
    condition_identifier = self.if_condition.print_python_code(
        identifiers, skills
    )
    code = (
        f'{identifier} = BT.Branch(name="{name}", '
        f' if_condition={condition_identifier}'
    )
    if self.then_child is not None:
      then_child_identifier = self.then_child.print_python_code(
          identifiers, skills
      )
      code += f', then_child={then_child_identifier}'
    if self.else_child is not None:
      else_child_identifier = self.else_child.print_python_code(
          identifiers, skills
      )
      code += f', else_child={else_child_identifier}'
    print(f'{code})')
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier

  def visit(
      self,
      containing_tree: 'BehaviorTree',
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', 'Node', 'Condition']], None
      ],
  ) -> None:
    super().visit(containing_tree, callback)
    if self.if_condition is not None:
      self.if_condition.visit(containing_tree, callback)
    if self.then_child is not None:
      self.then_child.visit(containing_tree, callback)
    if self.else_child is not None:
      self.else_child.visit(containing_tree, callback)


class Data(Node):
  """BT node of type Data for behavior_tree_pb2.DataNode.

  A data node can be used to create, update, or remove data from the
  blackboard. Information stored there can be created by a CEL expression, a
  specific proto or a list of protos, or from a world query.

  Attributes:
    blackboard_key: blackboard key the node operates on
    cel_expression: CEL expression for create or update operation
    world_query: World query for create or update operation
    input_proto: Proto for create or update operation
    input_protos: Protos for create or update operation
    operation: describing the operation the data node will perform
    proto: The proto representation of the node.
    node_type: A string label of the node type.
    result: blackboard value to pass on the modified blackboard key.
  """

  _blackboard_key: str
  _operation: 'Data.OperationType'
  _cel_expression: Optional[str]
  _world_query: Optional[WorldQuery]
  _proto: Optional[protobuf_message.Message]
  _protos: Optional[List[protobuf_message.Message]]
  _name: Optional[str]
  _node_id: Optional[int]
  _decorators: Optional['Decorators']

  class OperationType(enum.Enum):
    """Defines the kind of operation to perform for the data node."""

    CREATE_OR_UPDATE = 1
    REMOVE = 2

  def __init__(
      self,
      *,
      blackboard_key: str = '',
      operation: 'Data.OperationType' = OperationType.CREATE_OR_UPDATE,
      cel_expression: Optional[str] = None,
      world_query: Optional[WorldQuery] = None,
      proto: Optional[protobuf_message.Message] = None,
      protos: Optional[List[protobuf_message.Message]] = None,
      name: Optional[str] = None,
  ):
    self._decorators = None
    self._blackboard_key = blackboard_key
    self._operation = operation
    self._cel_expression = cel_expression
    self._world_query = world_query
    self._proto = proto
    self._protos = protos
    self._name = name
    self._node_id = None

    super().__init__()

  def __repr__(self) -> str:
    """Returns a compact, human-readable string representation."""
    return (
        f'{type(self).__name__}({self._name_repr()},'
        f' blackboard_key="{self.blackboard_key}")'
    )

  @property
  def name(self) -> Optional[str]:
    return self._name

  @name.setter
  def name(self, value: str):
    self._name = value

  @property
  def node_id(self) -> Optional[int]:
    return self._node_id

  @node_id.setter
  def node_id(self, value: int):
    self._node_id = value

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree.Node:
    self.validate()

    if self._blackboard_key is None or not self._blackboard_key:
      raise solutions_errors.InvalidArgumentError(
          'Data node requires the blackboard_key argument as non-empty string'
      )

    proto_message = super().proto
    if self._operation == Data.OperationType.CREATE_OR_UPDATE:
      proto_message.data.create_or_update.blackboard_key = self._blackboard_key

      if self._cel_expression is not None:
        proto_message.data.create_or_update.cel_expression = (
            self._cel_expression
        )

      if self._world_query is not None:
        proto_message.data.create_or_update.from_world.proto.Pack(
            self._world_query.proto
        )
        for assignment in self._world_query.assignments:
          proto_message.data.create_or_update.from_world.assign.append(
              assignment
          )

      if self._proto is not None:
        proto_message.data.create_or_update.proto.Pack(self._proto)

      if self._protos is not None:
        for p in self._protos:
          proto_message.data.create_or_update.protos.items.add().Pack(p)

    elif self._operation == Data.OperationType.REMOVE:
      proto_message.data.remove.blackboard_key = self._blackboard_key

    else:
      raise solutions_errors.InvalidArgumentError(
          'Data node has no operation type set'
      )

    return proto_message

  @property
  def node_type(self) -> str:
    return 'data'

  def set_decorators(self, decorators: Optional['Decorators']) -> 'Node':
    """Sets decorators for this node."""
    self._decorators = decorators
    return self

  @property
  def decorators(self) -> Optional['Decorators']:
    return self._decorators

  def validate(self) -> None:
    """Validates the current input.

    This checks if one and only one input is set for the Data node.

    Raises:
      InvalidArgumentError: raised if the node is in a state that could not be
        converted to a valid proto.
    """
    if self._operation is None:
      raise solutions_errors.InvalidArgumentError(
          'Data node has no operation mode specified'
      )

    num_inputs = 0
    if self._cel_expression is not None:
      num_inputs += 1
    if self._world_query is not None:
      num_inputs += 1
    if self._proto is not None:
      num_inputs += 1
    if self._protos is not None:
      num_inputs += 1

    if (
        self._operation == Data.OperationType.CREATE_OR_UPDATE
        and num_inputs != 1
    ):
      raise solutions_errors.InvalidArgumentError(
          'Data node for create or update requires exactly 1 input'
          f' element, got {num_inputs}'
      )

  @property
  def result(self) -> Optional[blackboard_value.BlackboardValue]:
    """Gets blackboard value to pass on the modified blackboard key.

    Only valid for create or update nodes, not when removing a key.

    Returns:
      Blackboard value for create_or_update node, None otherwise.
    """
    self.validate()
    if self._operation == Data.OperationType.CREATE_OR_UPDATE:
      if self._world_query is not None:
        return blackboard_value.BlackboardValue(
            any_list_pb2.AnyList.DESCRIPTOR.fields_by_name,
            self._blackboard_key,
            any_list_pb2.AnyList,
            None,
        )

      if self._proto is not None:
        return blackboard_value.BlackboardValue(
            self._proto.DESCRIPTOR.fields_by_name,
            self._blackboard_key,
            self._proto.__class__,
            None,
        )

      if self._protos is not None:
        return blackboard_value.BlackboardValue(
            any_list_pb2.AnyList.DESCRIPTOR.fields_by_name,
            self._blackboard_key,
            any_list_pb2.AnyList,
            None,
        )

    return None

  @property
  def blackboard_key(self) -> Optional[str]:
    return self._blackboard_key

  def set_blackboard_key(self, blackboard_key: str) -> 'Data':
    """Sets the blackboard key for this operation.

    Args:
      blackboard_key: blackboard key by which the value can be accessed in other
        nodes.

    Returns:
      self (for builder pattern)
    """
    self._blackboard_key = blackboard_key
    return self

  @property
  def operation(self) -> 'Data.OperationType':
    return self._operation

  def set_operation(self, operation: OperationType) -> 'Data':
    """Sets the mode of the performed operation.

    Args:
      operation: operation to perform, see enum.

    Returns:
      self (for builder pattern)
    """
    self._operation = operation
    if operation == Data.OperationType.REMOVE:
      self._cel_expression = None
      self._world_query = None
      self._proto = None
      self._protos = None
    return self

  @property
  def cel_expression(self) -> Optional[str]:
    return self._cel_expression

  def set_cel_expression(self, cel_expression: str) -> 'Data':
    """Sets the CEL expression to create or update a blackboard value.

    Args:
      cel_expression: CEL expression that may reference other blackboard values.

    Returns:
      self (for builder pattern)
    """
    if self._operation != Data.OperationType.CREATE_OR_UPDATE:
      raise solutions_errors.InvalidArgumentError(
          'Cannot set cel_expression on data node without operation'
          ' CREATE_OR_UPDATE'
      )
    self._cel_expression = cel_expression
    return self

  @property
  def world_query(self) -> Optional[WorldQuery]:
    return self._world_query

  def set_world_query(self, world_query: WorldQuery) -> 'Data':
    if self._operation != Data.OperationType.CREATE_OR_UPDATE:
      raise solutions_errors.InvalidArgumentError(
          'Cannot set world_query on data node without operation'
          ' CREATE_OR_UPDATE'
      )
    self._world_query = world_query
    return self

  @property
  def input_proto(self) -> Optional[protobuf_message.Message]:
    return self._proto

  def set_input_proto(self, proto: protobuf_message.Message) -> 'Data':
    """Sets a specific proto for creating or updating a blackboard value.

    Args:
      proto: The proto to store in the blackboard

    Returns:
      self (for builder pattern)
    """
    if self._operation != Data.OperationType.CREATE_OR_UPDATE:
      raise solutions_errors.InvalidArgumentError(
          'Cannot set input proto on data node without operation'
          ' CREATE_OR_UPDATE'
      )
    self._proto = proto
    return self

  @property
  def input_protos(self) -> Optional[List[protobuf_message.Message]]:
    return self._protos

  def set_input_protos(self, protos: List[protobuf_message.Message]) -> 'Data':
    """Sets list of specific protos for creating or updating a blackboard value.

    Args:
      protos: The protos to store in the blackboard (will be wrapped in an
        intrinsic_proto.executive.AnyList.

    Returns:
      self (for builder pattern)
    """
    if self._operation != Data.OperationType.CREATE_OR_UPDATE:
      raise solutions_errors.InvalidArgumentError(
          'Cannot set input protos on data node without operation'
          ' CREATE_OR_UPDATE'
      )
    self._protos = protos
    return self

  @classmethod
  def _create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree.DataNode
  ) -> 'Data':
    """Creates a new instances from data in a proto.

    Args:
      proto_object: Proto to import from.

    Returns:
      Instance of Data.

    Raises:
      InvalidArgumentError: if passed Node proto does not have the data field
        set to a valid configuration.
    """
    operation = Data.OperationType.CREATE_OR_UPDATE
    cel_expression = None
    world_query = None
    proto = None
    protos = None

    if proto_object.HasField('create_or_update'):
      create_or_update = proto_object.create_or_update

      blackboard_key = create_or_update.blackboard_key
      if create_or_update.HasField('cel_expression'):
        cel_expression = create_or_update.cel_expression
      if create_or_update.HasField('from_world'):
        world_query_proto = world_query_pb2.WorldQuery()
        create_or_update.from_world.proto.Unpack(world_query_proto)
        world_query = WorldQuery.create_from_proto(world_query_proto)
      if create_or_update.HasField('proto'):
        proto = create_or_update.proto
      protos = None
      if create_or_update.HasField('protos'):
        protos = [p for p in create_or_update.protos.items]

    elif proto_object.HasField('remove'):
      operation = Data.OperationType.REMOVE
      blackboard_key = proto_object.remove.blackboard_key
    else:
      raise solutions_errors.InvalidArgumentError(
          'Data node proto does not have any operation set'
      )

    data = cls(
        blackboard_key=blackboard_key,
        operation=operation,
        cel_expression=cel_expression,
        world_query=world_query,
        proto=proto,
        protos=protos,
    )

    data.validate()
    return data

  def dot_graph(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self, node_id_suffix: str = ''
  ) -> Tuple[graphviz.Digraph, str]:
    """Converts this node suitable for inclusion in a dot graph.

    Args:
      node_id_suffix: A little string of form `_1_2`, which is just a suffix to
        make a unique node name in the graph. If the node names clash within the
        graph, they are merged into one, and we do not want to merge unrelated
        nodes.

    Returns:
      Dot graph representation for this node.
    """
    return super().dot_graph(node_id_suffix=node_id_suffix, name=self._name)

  def print_python_code(
      self, identifiers: List[str], skills: providers.SkillProvider
  ) -> str:
    """Prints Python code suitable to recreate the node.

    Args:
      identifiers: list of already assigned identifiers.
      skills: skill provider to retrieve skill info from (unused).

    Returns:
      Identifier created for this node.
    """

    name = self._name if self._name else 'data'
    identifier = _generate_unique_identifier(name, identifiers)

    args = [
        f'name="{name}"',
        f'operation={self._operation}',
        f'blackboard_key="{self._blackboard_key}"',
    ]

    if self._operation == Data.OperationType.CREATE_OR_UPDATE:
      if self._cel_expression is not None:
        args.append(f'cel_expression="{self._cel_expression}"')
      if self._world_query is not None:
        args.append(f'world_query={self._world_query}')
      if self._proto is not None:
        args.append(
            f'proto=text_format.Parse("""{self._proto}""",'
            f' {self._proto.DESCRIPTOR.full_name}())'
        )
      if self._protos is not None:
        proto_strs = []
        for p in self._protos:
          proto_strs.append(f'''text_format.Parse("""{p}
""", {p.DESCRIPTOR.full_name}())''')

        args.append(f'protos=[{", ".join(proto_strs)}]')

    print(f'{identifier} = BT.Data({", ".join(args)})')
    if self.decorators:
      decorator_identifier = self.decorators.print_python_code(
          identifiers, skills
      )
      if decorator_identifier:
        print(f'{identifier}.set_decorators({decorator_identifier})')
    return identifier


class IdRecorder:
  """A visitor callable object that records tree ids and node ids."""

  def __init__(self):
    self.tree_to_node_id_to_nodes: Mapping[
        BehaviorTree, Mapping[int, list[Node]]
    ] = collections.defaultdict(lambda: collections.defaultdict(list))
    self.tree_id_to_trees: Mapping[str, list[BehaviorTree]] = (
        collections.defaultdict(list)
    )

  def __call__(
      self,
      containing_tree: 'BehaviorTree',
      tree_object: Union['BehaviorTree', Node, Condition],
  ):
    if isinstance(tree_object, Node) and tree_object.node_id is not None:
      self.tree_to_node_id_to_nodes[containing_tree][
          tree_object.node_id
      ].append(tree_object)
    if (
        isinstance(tree_object, BehaviorTree)
        and tree_object.tree_id is not None
    ):
      self.tree_id_to_trees[tree_object.tree_id].append(tree_object)


class BehaviorTree:
  # pyformat: disable
  """Python wrapper around behavior_tree_pb2.BehaviorTree proto.

  Attributes:
    name: Name of this behavior tree.
    tree_id: A unique ID for this behavior tree.
    root: The root node of the tree of type Node.
    proto: The proto representation of the BehaviorTree.
    dot_graph: The graphviz dot representation of the BehaviorTree.

  Example usage:
    bt = behavior_tree.BehaviorTree('my_behavior_tree_name')
    bt.set_root(behavior_tree.Sequence()
      .set_children(behavior_tree.Task(some_skill_action),
    behavior_tree.Task(some_other_skill_action)))
    print(bt.proto)   # prints the proto
    print(bt)         # prints a readable pseudo-code version of the instance
    bt.show()         # calling this in Jupyter would visualize the tree
  """
  # pyformat: enable

  tree_id: Optional[str]

  def __init__(
      self,
      name: Optional[str] = None,
      root: Optional[Union['Node', actions.ActionBase]] = None,
      bt: Union['BehaviorTree', behavior_tree_pb2.BehaviorTree, None] = None,
  ):
    """Creates an empty object or an object from another object / a plan proto.

    In all cases, __init__ creates a copy (not a reference) of the given BT.

    Args:
      name: the name of the behavior tree, which defaults to 'behavior_tree',
      root: a node of type Node to be set as the root of this tree,
      bt: BehaviorTree instance or BehaviorTree proto. The value of the `name`
        argument overwrites the value from the `bt` proto argument, if set.
    """
    root: Optional['Node'] = _transform_to_optional_node(root)
    self.tree_id = None
    if bt is not None:
      bt_copy = None
      if isinstance(bt, BehaviorTree):
        bt_copy = self.create_from_proto(bt.proto)
      elif isinstance(bt, behavior_tree_pb2.BehaviorTree):
        bt_copy = self.create_from_proto(bt)
      else:
        raise TypeError
      name = name or bt_copy.name
      root = root or bt_copy.root
      self.tree_id = bt_copy.tree_id

    self.name: str = name or ''
    self.root: Optional[Node] = root
    self._description = None

  def __repr__(self) -> str:
    """Converts a BT into a compact, human-readable string representation.

    Returns:
      A behavior tree formatted as string using Python syntax.
    """
    return f'BehaviorTree({self._name_repr()}root={repr(self.root)})'

  def _name_repr(self) -> str:
    """Returns a snippet for the name attribute to be used in __repr__."""
    name_snippet = ''
    if self.name:
      name_snippet = f'name="{self.name}", '
    return name_snippet

  def set_root(self, root: Union['Node', actions.ActionBase]) -> 'Node':
    """Sets the root member to the given Node instance."""
    self.root = _transform_to_node(root)
    return self.root

  @property
  def proto(self) -> behavior_tree_pb2.BehaviorTree:
    """Converts the given instance into the corresponding proto object."""
    if self.root is None:
      raise ValueError(
          'A behavior tree has to have a root node but currently '
          'it is not set. Please call `bt.root = bt_node` or '
          'bt.set_root(bt_node)`.'
      )
    proto_object = behavior_tree_pb2.BehaviorTree(name=self.name)
    proto_object.root.CopyFrom(self.root.proto)
    if self.tree_id:
      proto_object.tree_id = self.tree_id
    if self._description is not None:
      proto_object.description.CopyFrom(self._description)
    return proto_object

  @classmethod
  def create_from_proto(
      cls, proto_object: behavior_tree_pb2.BehaviorTree
  ) -> 'BehaviorTree':
    """Instantiates a behavior tree from a proto."""
    if cls != BehaviorTree:
      raise TypeError(
          'create_from_proto can only be called on the BehaviorTree class'
      )
    bt = cls()
    bt.name = proto_object.name
    if proto_object.HasField('tree_id'):
      bt.tree_id = proto_object.tree_id
    bt.root = Node.create_from_proto(proto_object.root)
    return bt

  def generate_and_set_unique_id(self) -> str:
    """Generates a unique tree id and sets it for this tree."""
    if self.tree_id is not None:
      print(
          'Warning: Creating a new unique id, but this tree already had an id'
          f' ({self.tree_id})'
      )
    self.tree_id = str(uuid.uuid4())
    return self.tree_id

  def visit(
      self,
      callback: Callable[
          ['BehaviorTree', Union['BehaviorTree', Node, Condition]], None
      ],
  ) -> None:
    """Visits this BehaviorTree recursively.

    All objects in the BehaviorTree are visited and the callback is called on
    every one. Objects can be
      * BehaviorTree objects, e.g., the tree itself, sub trees, or behavior
        trees in conditions
      * Node objects, e.g., Task or Sequence nodes
      * Condition objects, e.g., AllOf, Not or SubTreeCondition

    The callback is called for every object. For example, when called on a tree
    the callback is first called with the tree itself, when called on a
    SubtreeNode it is first called on the SubTreeNode and then on the sub-tree,
    when called on a SubTreeCondition it is first called on the condition and
    then on the tree within that condition.

    Callbacks are performed in an natural order for the different objects. For
    example, for a sequence node, its children are visited as in the node's
    order; for a loop node first its while condition is visited, then its
    do_child; a retry node first visits its child and then the recovery.

    Args:
      callback: Function (or any callable) to be called. This first argument
        will be the BehaviorTree containing the object in question, the second
        argument is the object itself, i.e., a BehaviorTree, Node or Condition.
    """
    callback(self, self)
    if self.root is not None:
      self.root.visit(self, callback)

  def validate_id_uniqueness(self) -> None:
    """Validates if all ids in the tree are unique.

    The current BehaviorTree object is checked recursively and any non-unique
    ids are highlighted. The function only works locally, i.e., only this tree
    and its SubTrees, Conditions, etc. are verified, but not the uniqueness of
    any referred PBTs or uniqueness across any other tree ids currently loaded
    in the executive.

    Raises:
      solution_errors.InvalidArgumentError if uniqueness is violated. The error
      message gives further information on which ids are non-consistent.
    """

    def tree_object_string(tree_object: Union['BehaviorTree', Node]):
      """Creates a string representation that helps identifying the object."""

      tree_object_str = (
          # pylint:disable-next=protected-access
          f'{tree_object.__class__.__name__}({tree_object._name_repr()})'
      )
      if (
          isinstance(tree_object, BehaviorTree)
          and tree_object.tree_id is not None
      ):
        tree_object_str += f' [tree_id="{tree_object.tree_id}"]'
      if isinstance(tree_object, Node) and tree_object.node_id is not None:
        tree_object_str += f' [node_id="{tree_object.node_id}"]'
      else:
        tree_object_str += ' [<unknown-id>]'
      return tree_object_str

    id_recorder = IdRecorder()
    self.visit(id_recorder)

    violations = []
    for tree, node_id_to_nodes in id_recorder.tree_to_node_id_to_nodes.items():
      for node_id, nodes in node_id_to_nodes.items():
        if len(nodes) > 1:
          violation_explanation = (
              f'  * {tree_object_string(tree)} contains'
              f' {len(nodes)} nodes with id {node_id}: '
          )
          violation_explanation += ', '.join(map(tree_object_string, nodes))
          violations.append(violation_explanation)
    for tree_id, trees in id_recorder.tree_id_to_trees.items():
      if len(trees) > 1:
        violation_explanation = (
            f'  * The tree contains {len(trees)} trees with id "{tree_id}": '
        )
        violation_explanation += ', '.join(map(tree_object_string, trees))
        violations.append(violation_explanation)
    if violations:
      violation_msg = (
          'The BehaviorTree violates uniqueness of tree ids or node ids'
          ' (per tree):\n'
      ) + '\n'.join(violations)
      raise solutions_errors.InvalidArgumentError(violation_msg)

  def dot_graph(self) -> graphviz.Digraph:
    """Converts the given behavior tree into a graphviz dot representation.

    Returns:
      An instance of graphviz.Digraph, which is a tree-shaped directed graph.
    """
    dot_graph = graphviz.Digraph()
    dot_graph.name = self.name
    dot_graph.graph_attr = {'label': self.name if self.name else '<unnamed>'}
    dot_graph.graph_attr.update(_SUBTREE_DOT_ATTRIBUTES)
    if self.root is not None:
      subtree_dot_graph, _ = self.root.dot_graph()
      dot_graph.subgraph(subtree_dot_graph)
    return dot_graph

  def show(self) -> None:
    return ipython.display_if_ipython(self.dot_graph())

  def print_python_code(
      self,
      skills: providers.SkillProvider,
      identifiers: Optional[List[str]] = None,
  ) -> None:
    if identifiers is None:
      identifiers = []
    child_identifier = self.root.print_python_code(
        identifiers=identifiers, skills=skills
    )
    identifier = _generate_unique_identifier('tree', identifiers)
    print(
        f"{identifier} = BT.BehaviorTree(name='{self.name}',"
        f' root={child_identifier})'
    )
