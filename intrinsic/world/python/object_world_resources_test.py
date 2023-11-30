# Copyright 2023 Intrinsic Innovation LLC

"""Tests for object_world_resources."""

from unittest import mock

import grpc  # pylint: disable=unused-import
import numpy as np
from numpy import testing as np_testing

from intrinsic.icon.proto import cart_space_pb2
from intrinsic.kinematics.types import joint_limits_pb2
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources
from google.protobuf import text_format
from absl.testing import absltest


class ObjectWorldResourcesTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._stub = mock.MagicMock()

  def _create_world_object_proto(
      self,
      *,
      name: str = '',
      object_id: str = '',
      object_type: object_world_service_pb2.ObjectType = object_world_service_pb2.PHYSICAL_OBJECT,
  ) -> object_world_service_pb2.Object:
    return object_world_service_pb2.Object(
        name=name,
        id=object_id,
        object_component=object_world_service_pb2.ObjectComponent(),
        type=object_type,
    )

  def _create_world_object(
      self, object_proto: object_world_service_pb2.Object
  ) -> object_world_resources.WorldObject:
    return object_world_resources.WorldObject(object_proto, self._stub)

  def _create_frame(
      self, frame_proto: object_world_service_pb2.Frame
  ) -> object_world_service_pb2.Frame:
    return object_world_resources.Frame(frame_proto, self._stub)

  def test_object_name(self):
    object_proto = self._create_world_object_proto(name='example')

    self.assertEqual(
        self._create_world_object(object_proto).name,
        object_world_ids.WorldObjectName('example'),
    )

  def test_object_id(self):
    object_proto = self._create_world_object_proto(object_id='5')

    self.assertEqual(
        self._create_world_object(object_proto).id,
        object_world_ids.ObjectWorldResourceId('5'),
    )

  def test_get_world_id(self):
    object_proto = self._create_world_object_proto()
    object_proto.world_id = 'world'

    self.assertEqual(self._create_world_object(object_proto).world_id, 'world')

  def test_create_world_object_without_object_component_raises_error(self):
    with self.assertRaises(ValueError) as e:
      self._create_world_object(object_world_service_pb2.Object())

    self.assertIn('object_component', str(e.exception))

  def test_list_frame_names_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(name='frame_1'))
    object_proto.frames.append(object_world_service_pb2.Frame(name='frame_2'))

    self.assertCountEqual(
        self._create_world_object(object_proto).frame_names,
        [
            object_world_ids.FrameName('frame_1'),
            object_world_ids.FrameName('frame_2'),
        ],
    )

  def test_frame_ids_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.extend([
        object_world_service_pb2.Frame(id='12'),
        object_world_service_pb2.Frame(id='13'),
    ])

    self.assertCountEqual(
        self._create_world_object(object_proto).frame_ids,
        [
            object_world_ids.ObjectWorldResourceId('12'),
            object_world_ids.ObjectWorldResourceId('13'),
        ],
    )

  def test_list_frames_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.extend([
        object_world_service_pb2.Frame(name='frame_1'),
        object_world_service_pb2.Frame(name='frame_2'),
    ])

    frame_names = [
        frame.name for frame in self._create_world_object(object_proto).frames
    ]
    self.assertCountEqual(frame_names, ['frame_1', 'frame_2'])

  def test_child_frame_names_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(name='frame_1'))
    object_proto.frames.append(
        object_world_service_pb2.Frame(
            name='frame_2',
            parent_frame=object_world_service_pb2.IdAndName(
                id='some_id', name='some_name'
            ),
        )
    )

    self.assertCountEqual(
        self._create_world_object(object_proto).child_frame_names,
        [object_world_ids.FrameName('frame_1')],
    )

  def test_child_frame_ids_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(id='id1'))
    object_proto.frames.append(
        object_world_service_pb2.Frame(
            id='id2',
            parent_frame=object_world_service_pb2.IdAndName(
                id='some_id', name='some_name'
            ),
        )
    )

    self.assertCountEqual(
        self._create_world_object(object_proto).child_frame_ids,
        [object_world_ids.ObjectWorldResourceId('id1')],
    )

  def test_child_frames_of_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(name='name1'))
    object_proto.frames.append(
        object_world_service_pb2.Frame(
            name='name2',
            parent_frame=object_world_service_pb2.IdAndName(
                id='some_id', name='some_name'
            ),
        )
    )

    frame_names = [
        frame.name
        for frame in self._create_world_object(object_proto).child_frames
    ]
    self.assertCountEqual(frame_names, ['name1'])

  def test_get_example_frame(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(name='frame_1'))
    object_proto.frames.append(object_world_service_pb2.Frame(name='example'))

    self.assertEqual(
        self._create_world_object(object_proto).get_frame('example').name,
        object_world_ids.FrameName('example'),
    )

  def test_get_parent_name(self):
    object_proto = self._create_world_object_proto()
    object_proto.parent.name = 'parent_object'

    parent_name = self._create_world_object(object_proto).parent_name

    self.assertIs(type(parent_name), object_world_ids.WorldObjectName)
    self.assertEqual(
        parent_name, object_world_ids.WorldObjectName('parent_object')
    )

  def test_get_parent_id(self):
    object_proto = self._create_world_object_proto()
    object_proto.parent.id = '5'

    parent_id = self._create_world_object(object_proto).parent_id

    self.assertIs(type(parent_id), object_world_ids.ObjectWorldResourceId)
    self.assertEqual(parent_id, object_world_ids.ObjectWorldResourceId('5'))

  def test_get_child_names(self):
    object_proto = self._create_world_object_proto()
    object_proto.children.extend([
        object_world_service_pb2.IdAndName(name='object_1'),
        object_world_service_pb2.IdAndName(name='object_2'),
    ])

    child_names = self._create_world_object(object_proto).child_names

    for child_name in child_names:
      self.assertIs(type(child_name), object_world_ids.WorldObjectName)
    self.assertCountEqual(
        child_names,
        [
            object_world_ids.WorldObjectName('object_1'),
            object_world_ids.WorldObjectName('object_2'),
        ],
    )

  def test_get_child_ids(self):
    object_proto = self._create_world_object_proto()
    object_proto.children.extend([
        object_world_service_pb2.IdAndName(id='5'),
        object_world_service_pb2.IdAndName(id='6'),
    ])

    child_ids = self._create_world_object(object_proto).child_ids

    for child_id in child_ids:
      self.assertIs(type(child_id), object_world_ids.ObjectWorldResourceId)
    self.assertCountEqual(
        self._create_world_object(object_proto).child_ids,
        [
            object_world_ids.ObjectWorldResourceId('5'),
            object_world_ids.ObjectWorldResourceId('6'),
        ],
    )

  def test_print_object_with_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.name = 'my_object'
    object_proto.id = '15'
    object_proto.children.append(
        object_world_service_pb2.IdAndName(id='18', name='my_child_object')
    )

    self.assertEqual(
        self._create_world_object(object_proto).__str__(),
        """\
my_object: WorldObject(id=15)
 |=> my_child_object (id=18)\
""",
    )

  def test_print_object_with_frames(self):
    object_proto = self._create_world_object_proto()
    object_proto.name = 'my_object'
    object_proto.id = '15'
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='frame_1', id='16')
    )
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='frame_2', id='17')
    )

    self.assertEqual(
        self._create_world_object(object_proto).__str__(),
        """\
my_object: WorldObject(id=15)
 |-> frame_1: Frame(id=16)
 |-> frame_2: Frame(id=17)\
""",
    )

  def test_print_object_with_frames_and_object(self):
    object_proto = self._create_world_object_proto()
    object_proto.name = 'my_object'
    object_proto.id = '15'
    object_proto.children.append(
        object_world_service_pb2.IdAndName(id='18', name='my_child_object')
    )
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='frame_1', id='16')
    )
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='frame_2', id='17')
    )

    self.assertEqual(
        self._create_world_object(object_proto).__str__(),
        """\
my_object: WorldObject(id=15)
 |=> my_child_object (id=18)
 |-> frame_1: Frame(id=16)
 |-> frame_2: Frame(id=17)\
""",
    )

  def test_world_object_representation(self):
    object_proto = self._create_world_object_proto(
        name='my_object', object_id='15'
    )

    object_representation = self._create_world_object(object_proto).__repr__()

    self.assertIn('WorldObject', object_representation)
    self.assertIn('name=my_object', object_representation)
    self.assertIn('id=15', object_representation)

  def test_get_unknown_frame_raises_value_error(self):
    with self.assertRaises(ValueError) as e:
      self._create_world_object(
          self._create_world_object_proto(name='test_object')
      ).get_frame('unknown')

    self.assertIn('unknown', str(e.exception))
    self.assertIn('test_object', str(e.exception))

  def test_get_example_frame_attribute(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(object_world_service_pb2.Frame(name='frame_1'))
    object_proto.frames.append(object_world_service_pb2.Frame(name='example'))

    self.assertEqual(
        self._create_world_object(object_proto).example.name,
        object_world_ids.FrameName('example'),
    )

  def test_object_getter(self):
    object_proto = self._create_world_object_proto()
    object_proto.children.append(
        object_world_service_pb2.IdAndName(name='child_object', id='child_id')
    )

    child_proto = self._create_world_object_proto(name='child_object')
    self._stub.GetObject.return_value = child_proto

    self.assertEqual(
        self._create_world_object(object_proto).child_object.name,
        'child_object',
    )

  def test_get_unknown_frame_attribute_raises_attribute_error(self):
    with self.assertRaises(AttributeError) as e:
      _ = self._create_world_object(self._create_world_object_proto()).unknown

    self.assertIn('unknown', str(e.exception))

  def test_object__dir__returns_frame_and_child_names(self):
    object_proto = self._create_world_object_proto()
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='child_frame_1')
    )
    object_proto.frames.append(
        object_world_service_pb2.Frame(name='child_frame_2')
    )
    object_proto.children.append(
        object_world_service_pb2.IdAndName(name='child_object_1')
    )
    object_proto.children.append(
        object_world_service_pb2.IdAndName(name='child_object_2')
    )

    self.assertEqual(
        self._create_world_object(object_proto).__dir__(),
        [
            'child_frame_1',
            'child_frame_2',
            'child_frame_ids',
            'child_frame_names',
            'child_frames',
            'child_ids',
            'child_names',
            'child_object_1',
            'child_object_2',
            'frame_ids',
            'frame_names',
            'frames',
            'get_frame',
            'id',
            'name',
            'parent',
            'parent_id',
            'parent_name',
            'parent_t_this',
            'proto',
            'reference',
            'transform_node_reference',
            'world_id',
        ],
    )

  def test_frame_id(self):
    frame_proto = object_world_service_pb2.Frame(id='5')

    self.assertEqual(
        self._create_frame(frame_proto).id,
        object_world_ids.ObjectWorldResourceId('5'),
    )

  def test_frame_name(self):
    frame_proto = object_world_service_pb2.Frame(name='example')

    self.assertEqual(
        self._create_frame(frame_proto).name,
        object_world_ids.FrameName('example'),
    )

  def test_frame_parent_object_name(self):
    frame_proto = object_world_service_pb2.Frame()
    frame_proto.object.name = 'example'

    self.assertEqual(
        self._create_frame(frame_proto).object_name,
        object_world_ids.WorldObjectName('example'),
    )

  def test_frame_parent_object_id(self):
    frame_proto = object_world_service_pb2.Frame()
    frame_proto.object.id = '5'

    self.assertEqual(
        self._create_frame(frame_proto).object_id,
        object_world_ids.ObjectWorldResourceId('5'),
    )

  def test_frame_parent_frame_id_empty(self):
    frame_proto = object_world_service_pb2.Frame()

    self.assertIsNone(self._create_frame(frame_proto).parent_frame_id)

  def test_frame_parent_frame_id(self):
    frame_proto = object_world_service_pb2.Frame()
    frame_proto.parent_frame.id = 'some_id'

    self.assertEqual(
        self._create_frame(frame_proto).parent_frame_id,
        object_world_ids.ObjectWorldResourceId('some_id'),
    )

  def test_frame_parent_frame_name_empty(self):
    frame_proto = object_world_service_pb2.Frame()

    self.assertIsNone(self._create_frame(frame_proto).parent_frame_name)

  def test_frame_parent_frame_name(self):
    frame_proto = object_world_service_pb2.Frame()
    frame_proto.parent_frame.name = 'some_name'

    self.assertEqual(
        self._create_frame(frame_proto).parent_frame_name,
        object_world_ids.FrameName('some_name'),
    )

  def test_frame_child_frame_ids(self):
    frame_proto = object_world_service_pb2.Frame(
        child_frames=[
            object_world_service_pb2.IdAndName(id='id1'),
            object_world_service_pb2.IdAndName(id='id2'),
        ]
    )

    self.assertEqual(
        self._create_frame(frame_proto).child_frame_ids,
        [
            object_world_ids.ObjectWorldResourceId('id1'),
            object_world_ids.ObjectWorldResourceId('id2'),
        ],
    )

  def test_frame_child_frame_names(self):
    frame_proto = object_world_service_pb2.Frame(
        child_frames=[
            object_world_service_pb2.IdAndName(name='name1'),
            object_world_service_pb2.IdAndName(name='name2'),
        ]
    )

    self.assertEqual(
        self._create_frame(frame_proto).child_frame_names,
        [
            object_world_ids.FrameName('name1'),
            object_world_ids.FrameName('name2'),
        ],
    )

  def test_print_frame(self):
    frame_proto_string = """
      object: {id: '15' name: 'my_object'}
      name: 'my_frame'
      id: '14'
    """
    frame_string = object_world_resources.Frame(
        text_format.Parse(frame_proto_string, object_world_service_pb2.Frame()),
        self._stub,
    ).__str__()

    self.assertEqual(
        frame_string,
        'Frame(name=my_frame, id=14, object_name=my_object, object_id=15)',
    )

  def test_frame_representation(self):
    frame_proto_string = """
      object: {id: '15' name: 'my_object'}
      name: 'my_frame'
      id: '14'
    """
    frame_string = object_world_resources.Frame(
        text_format.Parse(frame_proto_string, object_world_service_pb2.Frame()),
        self._stub,
    ).__repr__()

    self.assertEqual(
        frame_string,
        '<Frame(name=my_frame, id=14, object_name=my_object, object_id=15)>',
    )

  def test_object_to_transform_node_reference(self):
    transform_node_reference = object_world_resources.WorldObject(
        object_world_service_pb2.Object(
            name='my_object',
            id='my_id',
            object_component={},
            object_full_path=object_world_service_pb2.ObjectFullPath(
                object_names=['my_object']
            ),
        ),
        self._stub,
    ).transform_node_reference

    transform_node_proto_string = """
      id: 'my_id'
      debug_hint: "Created from path world.my_object"
    """
    self.assertEqual(
        transform_node_reference,
        text_format.Parse(
            transform_node_proto_string,
            object_world_refs_pb2.TransformNodeReference(),
        ),
    )

  def test_object_to_reference(self):
    object_reference = object_world_resources.WorldObject(
        object_world_service_pb2.Object(
            name='my_object',
            id='my_id',
            object_component={},
            object_full_path=object_world_service_pb2.ObjectFullPath(
                object_names=['my_grandparent', 'my_parent', 'my_object']
            ),
        ),
        self._stub,
    ).reference

    object_reference_string = """
      id: 'my_id'
      debug_hint: "Created from path world.my_grandparent.my_parent.my_object"
    """

    self.assertEqual(
        object_reference,
        text_format.Parse(
            object_reference_string, object_world_refs_pb2.ObjectReference()
        ),
    )

  def test_frame_to_transform_node_reference(self):
    frame_proto_string = """
      name: 'my_frame'
      id: 'my_id'
      object: {name: 'my_object'}
      object_full_path: {
          object_names: 'my_object'
      }
    """
    transform_node_reference = object_world_resources.Frame(
        text_format.Parse(frame_proto_string, object_world_service_pb2.Frame()),
        self._stub,
    ).transform_node_reference

    transform_node_proto_string = """
      id: 'my_id'
      debug_hint: "Created from path world.my_object.my_frame"
    """
    self.assertEqual(
        transform_node_reference,
        text_format.Parse(
            transform_node_proto_string,
            object_world_refs_pb2.TransformNodeReference(),
        ),
    )

  def test_frame_to_frame_reference(self):
    frame_proto_string = """
      name: 'my_frame'
      id: 'my_id'
      object: {name: 'my_object'}
      object_full_path: {
          object_names: 'my_object'
      }
    """
    frame_reference = object_world_resources.Frame(
        text_format.Parse(frame_proto_string, object_world_service_pb2.Frame()),
        self._stub,
    ).reference

    frame_reference_string = """
      id: 'my_id'
      debug_hint: "Created from path world.my_object.my_frame"
    """
    self.assertEqual(
        frame_reference,
        text_format.Parse(
            frame_reference_string, object_world_refs_pb2.FrameReference()
        ),
    )

  def test_get_parent_t_this(self):
    object_proto_string = """
    object_component: {
      parent_t_this:{
        position{
          x: 1
          y: 2
          z: 3
        }
      }
    }
    """
    my_object = object_world_resources.WorldObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    np_testing.assert_allclose(
        my_object.parent_t_this.translation, np.array([1, 2, 3])
    )

  def test_create_world_object_with_auto_type(self):
    my_object = object_world_resources.create_object_with_auto_type(
        self._create_world_object_proto(), self._stub
    )

    self.assertIs(type(my_object), object_world_resources.WorldObject)

  def test_create_kinematic_object_with_auto_type(self):
    my_object = object_world_resources.create_object_with_auto_type(
        object_world_service_pb2.Object(
            type=object_world_service_pb2.ObjectType.KINEMATIC_OBJECT,
            object_component={},
            kinematic_object_component={},
        ),
        self._stub,
    )

    self.assertIs(type(my_object), object_world_resources.KinematicObject)

  def test_create_root_object(self):
    root_object = self._create_world_object(
        object_world_service_pb2.Object(
            type=object_world_service_pb2.ObjectType.ROOT
        )
    )

    np_testing.assert_array_almost_equal(
        root_object.parent_t_this.rotation.quaternion.xyzw,
        np.array([0, 0, 0, 1]),
    )

  def test_object_reference(self):
    my_object = self._create_world_object(
        self._create_world_object_proto(object_id='15')
    )

    self.assertEqual(my_object.reference.id, '15')

  def test_frame_reference(self):
    my_frame = self._create_frame(object_world_service_pb2.Frame(id='17'))

    self.assertEqual(my_frame.reference.id, '17')

  def test_frames_equal_raises_error(self):
    my_frame = self._create_frame(object_world_service_pb2.Frame(id='17'))
    my_other_frame = self._create_frame(object_world_service_pb2.Frame(id='17'))

    with self.assertRaises(NotImplementedError):
      _ = my_frame == my_other_frame

  def test_objects_equal_raises_error(self):
    my_object = self._create_world_object(
        self._create_world_object_proto(object_id='15')
    )
    my_other_object = self._create_world_object(
        self._create_world_object_proto(object_id='15')
    )

    with self.assertRaises(NotImplementedError):
      _ = my_object == my_other_object

  def test_frame_has_proto(self):
    my_frame = self._create_frame(object_world_service_pb2.Frame(id='17'))

    self.assertIs(type(my_frame.proto), object_world_service_pb2.Frame)

  def test_object_has_proto(self):
    my_object = self._create_world_object(
        self._create_world_object_proto(object_id='15')
    )

    self.assertIs(type(my_object.proto), object_world_service_pb2.Object)


class KinematicObjectTests(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._stub = mock.MagicMock()

  def _create_kinematic_object(
      self, kinematic_object_proto: object_world_service_pb2.Object
  ) -> object_world_resources.KinematicObject:
    return object_world_resources.KinematicObject(
        kinematic_object_proto, self._stub
    )

  def test_create_kinematic_object(self):
    object_proto_string = """
      name: 'my_object'
      object_component: {}
      kinematic_object_component: {}
    """
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(kinematic_object.name, 'my_object')

  def test_create_kinematic_object_without_component_raises_error(self):
    with self.assertRaises(ValueError) as e:
      self._create_kinematic_object(object_world_service_pb2.Object())

    self.assertIn('kinematic_object_component', str(e.exception))

  def test_get_joint_entity_ids_and_names(self):
    joint_entity_proto_string_1 = """
      {world_id: "my_world"
      id: "eid_1"
      name: "joint_1"}
    """
    joint_entity_proto_string_2 = """
      {world_id: "my_world"
      id: "eid_2"
      name: "joint_2"}
    """

    object_proto_string = """
      name: 'my_object'
      object_component: {{}}
      kinematic_object_component: {{
        joint_positions: [1.0, 2.0]
        joint_entity_ids: ["eid_1", "eid_2"]
      }}
      entities: [
          {{
            key: "eid_1" value: {joint_entity_1}
          }},
          {{
            key: "eid_2" value: {joint_entity_2}
          }}
      ]
    """.format(
        joint_entity_1=joint_entity_proto_string_1,
        joint_entity_2=joint_entity_proto_string_2,
    )
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )
    self.assertEqual(kinematic_object.joint_entity_ids, ['eid_1', 'eid_2'])
    self.assertEqual(
        kinematic_object.joint_entity_names, ['joint_1', 'joint_2']
    )

  def test_get_joint_positions(self):
    object_proto_string = """
      name: 'my_object'
      object_component: {}
      kinematic_object_component: {
        joint_positions: [1.0, 2.0, 3.0]
      }
    """
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(kinematic_object.joint_positions, [1.0, 2.0, 3.0])

  def test_get_joint_application_limits(self):
    limits_proto_string = """
      min_position { values: -1 values: -1 values: -1 }
      max_position { values: 1 values: 1 values: 1 }
      max_velocity { values: 2 values: 2 values: 2 }
      max_acceleration { values: 3 values: 3 values: 3 }
      max_jerk { values: 4 values: 4 values: 4 }
    """
    object_proto_string = """
      name: 'my_object'
      object_component: {{}}
      kinematic_object_component: {{
        joint_application_limits: {{
          {limits}
        }}
      }}
    """.format(limits=limits_proto_string)
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(
        kinematic_object.joint_application_limits,
        text_format.Parse(limits_proto_string, joint_limits_pb2.JointLimits()),
    )

  def test_get_joint_system_limits(self):
    limits_proto_string = """
      min_position { values: -1 values: -1 values: -1 }
      max_position { values: 1 values: 1 values: 1 }
      max_velocity { values: 2 values: 2 values: 2 }
      max_acceleration { values: 3 values: 3 values: 3 }
      max_jerk { values: 4 values: 4 values: 4 }
    """
    object_proto_string = """
      name: 'my_object'
      object_component: {{}}
      kinematic_object_component: {{
        joint_system_limits: {{
          {limits}
        }}
      }}
    """.format(limits=limits_proto_string)
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(
        kinematic_object.joint_system_limits,
        text_format.Parse(limits_proto_string, joint_limits_pb2.JointLimits()),
    )

  def test_cartesian_limits(self):
    limits_proto_string = """
      min_translational_velocity: -1
      min_translational_velocity: -1
      min_translational_velocity: -1
      max_translational_velocity: 1
      max_translational_velocity: 1
      max_translational_velocity: 1
      min_translational_acceleration: -10
      min_translational_acceleration: -10
      min_translational_acceleration: -10
      max_translational_acceleration: 10
      max_translational_acceleration: 10
      max_translational_acceleration: 10
      min_translational_jerk: 0
      min_translational_jerk: 0
      min_translational_jerk: 0
      max_translational_jerk: 0
      max_translational_jerk: 0
      max_translational_jerk: 0
      min_translational_position: -100
      min_translational_position: -100
      min_translational_position: -100
      max_translational_position: 100
      max_translational_position: 100
      max_translational_position: 100
    """
    object_proto_string = """
      name: 'my_object'
      object_component: {{}}
      kinematic_object_component: {{
        cartesian_limits: {{
          {limits}
        }}
      }}
    """.format(limits=limits_proto_string)
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(
        kinematic_object.cartesian_limits,
        text_format.Parse(
            limits_proto_string, cart_space_pb2.CartesianLimits()
        ),
    )

  def test_get_iso_flange_frames(self):
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            """
            world_id: "my_world"
            id: "some_id"
            name: "some_name"
            parent: { id: "parent_id" name: "parent_name" }
            frames: {
              world_id: "my_world"
              id: "another_frame_id"
              name: "another_frame"
              object: { id: "some_id" name: "some_name" }
              parent_t_this: { orientation: { w: 1 } }
            }
            frames: {
              world_id: "my_world"
              id: "flange_frame_id"
              name: "flange"
              object: { id: "some_id" name: "some_name" }
              parent_t_this: { orientation: { w: 1 } }
            }
            object_component: {}
            kinematic_object_component: {
              iso_flange_frames { id: "flange_frame_id" name: "flange" }
            }""",
            object_world_service_pb2.Object(),
        ),
        self._stub,
    )

    self.assertEqual(
        kinematic_object.iso_flange_frame_ids,
        [object_world_ids.ObjectWorldResourceId('flange_frame_id')],
    )
    self.assertEqual(
        kinematic_object.iso_flange_frame_names,
        [object_world_ids.FrameName('flange')],
    )
    frame_names = [frame.name for frame in kinematic_object.iso_flange_frames]
    self.assertEqual(frame_names, [object_world_ids.FrameName('flange')])
    self.assertEqual(
        kinematic_object.get_single_iso_flange_frame().name,
        object_world_ids.FrameName('flange'),
    )

  def test_get_single_iso_flange_frame_fails_if_no_flange_frame(self):
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            """
            world_id: "my_world"
            id: "some_id"
            name: "some_name"
            parent: { id: "parent_id" name: "parent_name" }
            object_component: {}
            kinematic_object_component: {}""",
            object_world_service_pb2.Object(),
        ),
        self._stub,
    )

    with self.assertRaises(LookupError) as e:
      kinematic_object.get_single_iso_flange_frame()

    self.assertIn('does not have any flange frame', str(e.exception))

  def test_get_single_iso_flange_frame_fails_if_multiple_flange_frames(self):
    kinematic_object = object_world_resources.KinematicObject(
        text_format.Parse(
            """
            world_id: "my_world"
            id: "some_id"
            name: "some_name"
            parent: { id: "parent_id" name: "parent_name" }
            frames: {
              world_id: "my_world"
              id: "flange_frame_1_id"
              name: "flange1"
              object: { id: "some_id" name: "some_name" }
              parent_t_this: { orientation: { w: 1 } }
            }
            frames: {
              world_id: "my_world"
              id: "flange_frame_2_id"
              name: "flange2"
              object: { id: "some_id" name: "some_name" }
              parent_t_this: { orientation: { w: 1 } }
            }
            object_component: {}
            kinematic_object_component: {
              iso_flange_frames { id: "flange_frame_1_id" name: "flange1" }
              iso_flange_frames { id: "flange_frame_2_id" name: "flange2" }
            }""",
            object_world_service_pb2.Object(),
        ),
        self._stub,
    )

    with self.assertRaises(LookupError) as e:
      kinematic_object.get_single_iso_flange_frame()

    self.assertIn('has more than one flange frame', str(e.exception))

  def test_get_motion_target(self):
    object_proto_string = """
      name: 'my_robot'
      object_component: {}
      kinematic_object_component: {
        named_joint_configurations:
          {
            name: 'my_motion_target',
            joint_positions: [1.0, 2.0, 3.0],
          },
      }
    """
    my_robot = object_world_resources.KinematicObject(
        text_format.Parse(
            object_proto_string, object_world_service_pb2.Object()
        ),
        self._stub,
    )

    self.assertEqual(
        my_robot.joint_configurations.my_motion_target.joint_position,
        [1.0, 2.0, 3.0],
    )


class JointConfigurationTest(absltest.TestCase):

  def test_construction(self):
    joint_position = mock.Mock()
    motion_target = object_world_resources.JointConfiguration(
        joint_position=joint_position
    )
    self.assertEqual(motion_target.joint_position, joint_position)


class RobotConfigurationsTest(absltest.TestCase):

  def test_has_motion_target_attr(self):
    my_robot_motion_targets = object_world_resources.JointConfigurations({
        'my_motion_target': object_world_resources.JointConfiguration(
            [1.0, 2.0, 3.0]
        )
    })

    self.assertIsInstance(
        my_robot_motion_targets.my_motion_target,
        object_world_resources.JointConfiguration,
    )
    self.assertEqual(
        my_robot_motion_targets.my_motion_target.joint_position, [1.0, 2.0, 3.0]
    )


if __name__ == '__main__':
  absltest.main()
