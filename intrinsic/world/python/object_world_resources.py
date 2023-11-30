# Copyright 2023 Intrinsic Innovation LLC

"""Defines the resources used for the object world python api."""

import abc
from typing import Dict, List, Optional

from intrinsic.icon.proto import cart_space_pb2
from intrinsic.kinematics.types import joint_limits_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.util.grpc import error_handling
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.proto import object_world_service_pb2
from intrinsic.world.proto import object_world_service_pb2_grpc
from intrinsic.world.proto import object_world_updates_pb2
from intrinsic.world.python import object_world_ids


def _list_public_methods(instance: object) -> List[str]:
  """Returns all public methods of the given instance.

  Args:
    instance: Any class instance.
  """
  return [
      method for method in dir(instance.__class__) if not method.startswith('_')
  ]


class TransformNode(metaclass=abc.ABCMeta):
  """Abstract base class of all transform nodes in the object world.

  Attributes:
    id: The unique id of the frame in the world.
    transform_node_reference: The object_world_refs_pb2.TransformNodeReference
      that uniquely identifies the frame in the world as a TransformNode.
    parent: The parent node of this TransformNode. None if this is the root.
    world_id: The id of the world in which the object resides.
    proto: The underlying proto data structure.
  """

  def __init__(
      self, stub: object_world_service_pb2_grpc.ObjectWorldServiceStub
  ):
    # The stub is needed for __getattr__ so that auto completion and addressing
    # with chained . operators can be supported.
    # Refrain from using the stub apart from __getattr__ or its helpers.
    self._stub = stub
    # child classes depending on the class type.
    self._proto = None

  @property
  @abc.abstractmethod
  def id(self) -> object_world_ids.ObjectWorldResourceId:
    return NotImplemented

  @property
  @abc.abstractmethod
  def transform_node_reference(
      self,
  ) -> object_world_refs_pb2.TransformNodeReference:
    return NotImplemented

  @property
  @abc.abstractmethod
  def parent(self) -> Optional['TransformNode']:
    return NotImplemented

  @abc.abstractmethod
  def __getattr__(self, name: str) -> 'TransformNode':
    return NotImplemented

  @property
  def world_id(self) -> str:
    return self._proto.world_id

  @property
  @abc.abstractmethod
  def proto(self) -> None:
    """Returns the underying proto data structure.

    Overwrite this method in child classes with a proper return type.
    """
    return NotImplemented

  # Disable hashing because __eq__ is disabled.
  __hash__ = None

  def __eq__(self, other: 'TransformNode') -> bool:
    raise NotImplementedError(
        'TransformNodes represent local snapshots of world resources at '
        'specific points in time and cannot be compared directly. To check '
        'whether two instances represent the same world resource compare the '
        "'id' or 'name' properties. To compare two snapshots of the same "
        'world resource use other properties selectively or compare the '
        "'proto' property as a whole."
    )


class Frame(TransformNode):
  """A local copy of a frame in a world.

  A frame represents a pose relative to an object. If the parent object is the
  root object, the frame is a "global frame", otherwise the frame is a "local
  frame".

  Attributes:
    name: The object-wide unique human-readable name of the frame.
    object_id: The id of the WorldObject the Frame is attached to.
    object_name: The name of the WorldObject the Frame is attached to.
    parent_frame_id: The optional id of the parent frame. If None, the frame is
      attached directly to one of the links of the parent object.
    parent_frame_name: The optional name of the parent frame. If None, the frame
      is attached directly to one of the links of the parent object
    child_frame_ids: Ids of child frames which have this frame as their parent
      frame and which are not attached directly to the parent object.
    child_frame_names: Names of child frames which have this frame as their
      parent frame and which are not attached directly to the parent object.
    parent_t_this: Pose of this frame in the space of the parent object.
    reference: The object_world_refs_pb2.FrameReference that uniquely identifies
      the frame in the world based on the ID.
  """

  def __init__(
      self,
      world_frame: object_world_service_pb2.Frame,
      stub: object_world_service_pb2_grpc.ObjectWorldServiceStub,
  ):
    super().__init__(stub)
    self._proto: object_world_service_pb2.Frame = world_frame

  @property
  def id(self) -> object_world_ids.ObjectWorldResourceId:
    return object_world_ids.ObjectWorldResourceId(self._proto.id)

  @property
  def name(self) -> object_world_ids.FrameName:
    return object_world_ids.FrameName(self._proto.name)

  @property
  def object_id(self) -> object_world_ids.ObjectWorldResourceId:
    return object_world_ids.ObjectWorldResourceId(self._proto.object.id)

  @property
  def object_name(self) -> object_world_ids.WorldObjectName:
    return object_world_ids.WorldObjectName(self._proto.object.name)

  @property
  def parent_frame_id(self) -> Optional[object_world_ids.ObjectWorldResourceId]:
    return (
        object_world_ids.ObjectWorldResourceId(self._proto.parent_frame.id)
        if self._proto.HasField('parent_frame')
        else None
    )

  @property
  def parent_frame_name(self) -> Optional[object_world_ids.FrameName]:
    return (
        object_world_ids.FrameName(self._proto.parent_frame.name)
        if self._proto.HasField('parent_frame')
        else None
    )

  @property
  def child_frame_ids(self) -> List[object_world_ids.ObjectWorldResourceId]:
    return [
        object_world_ids.ObjectWorldResourceId(id_and_name.id)
        for id_and_name in self._proto.child_frames
    ]

  @property
  def child_frame_names(self) -> List[object_world_ids.FrameName]:
    return [
        object_world_ids.FrameName(id_and_name.name)
        for id_and_name in self._proto.child_frames
    ]

  def __repr__(self):
    return f'<Frame(name={self.name}, id={self.id}, ' + (
        f'object_name={self.object_name}, object_id={self.object_id})>'
    )

  def __str__(self):
    return f'Frame(name={self.name}, id={self.id}, ' + (
        f'object_name={self.object_name}, object_id={self.object_id})'
    )

  def _debug_hint(self) -> str:
    return 'Created from path {}'.format(
        '.'.join(
            ['world']
            + list(self._proto.object_full_path.object_names)
            + [self.name]
        )
    )

  @property
  def reference(self) -> object_world_refs_pb2.FrameReference:
    return object_world_refs_pb2.FrameReference(
        id=self.id, debug_hint=self._debug_hint()
    )
  @property
  def transform_node_reference(
      self,
  ) -> object_world_refs_pb2.TransformNodeReference:
    return object_world_refs_pb2.TransformNodeReference(
        id=self.id, debug_hint=self._debug_hint()
    )

  @property
  def parent(self) -> Optional[TransformNode]:
    if self.parent_frame_id is not None:
      get_frame_request = object_world_service_pb2.GetFrameRequest(
          world_id=self._proto.world_id,
          frame=object_world_refs_pb2.FrameReference(id=self.parent_frame_id),
      )
      frame_proto = self._stub.GetFrame(get_frame_request)
      return Frame(frame_proto, self._stub)

    get_object_request = object_world_service_pb2.GetObjectRequest(
        world_id=self._proto.world_id,
        object=object_world_refs_pb2.ObjectReference(id=self.object_id),
        view=object_world_updates_pb2.ObjectView.FULL,
    )
    object_proto = self._stub.GetObject(get_object_request)
    return WorldObject(object_proto, self._stub)

  @property
  def parent_t_this(self) -> data_types.Pose3:
    return math_proto_conversion.pose_from_proto(self._proto.parent_t_this)

  def __getattr__(self, name: str) -> TransformNode:
    raise NotImplementedError()

  @property
  def proto(self) -> object_world_service_pb2.Frame:
    return self._proto


class WorldObject(TransformNode):
  """A local copy of an object in a world.

  Represents an object in the object-world. It wraps a proto and provides
  conversions to appropriate Python types.

  Attributes:
    id: The unique id of the object in the world.
    name: The human-readable name of the object which is unique in the world.
    frame_ids: A list with the ids of all frames under this object, including
      ones that are attached indirectly to this object via another frame.
    frame_names: A list with the names of all frames under this object,
      including ones that are attached indirectly to this object via another
      frame.
    frames: A list with all frames under this object, including ones that are
      attached indirectly to this object via another frame.
    child_frame_ids: A list with the ids of all immediate child frames of this
      object, excluding ones that are attached indirectly to this object via
      another frame.
    child_frame_names: A list with the names of all immediate child frames of
      this object, excluding ones that are attached indirectly to this object
      via another frame.
    child_frames: A list with all immediate child frames of this object,
      excluding ones that are attached indirectly to this object via another
      frame.
    parent_name: The name of the parent object.
    parent_id: The id of the parent object in the world.
    child_ids: A list with the ids of all child objects.
    child_names: A list with the names of all child objects.
    parent_t_this: Transform between the parent object and this frame.
    reference: The object_world_refs_pb2.ObjectReference that uniquely
      identifies the object in the world based on the ID.
    transform_node_reference: The object_world_refs_pb2.TransformNodeReference
      that uniquely identifies the object in the world as a TransformNode.
  """

  def __init__(
      self,
      world_object: object_world_service_pb2.Object,
      stub: object_world_service_pb2_grpc.ObjectWorldServiceStub,
  ):
    super().__init__(stub)
    if world_object.type == object_world_service_pb2.ObjectType.ROOT:
      world_object.object_component.CopyFrom(
          object_world_service_pb2.ObjectComponent()
      )
    if not world_object.HasField('object_component'):
      raise ValueError(
          'The world_object proto is missing the field "object_component". '
          f'Cannot create a {self.__class__.__name__} without this field.'
      )
    self._proto: object_world_service_pb2.Object = world_object

  @property
  def id(self) -> object_world_ids.ObjectWorldResourceId:
    return object_world_ids.ObjectWorldResourceId(self._proto.id)

  @property
  def name(self) -> object_world_ids.WorldObjectName:
    return object_world_ids.WorldObjectName(self._proto.name)

  @property
  def frame_ids(self) -> List[object_world_ids.ObjectWorldResourceId]:
    return [
        object_world_ids.ObjectWorldResourceId(frame.id)
        for frame in self._proto.frames
    ]

  @property
  def frame_names(self) -> List[object_world_ids.FrameName]:
    return [
        object_world_ids.FrameName(frame.name) for frame in self._proto.frames
    ]

  @property
  def frames(self) -> List[Frame]:
    return [
        Frame(frame_proto, self._stub) for frame_proto in self._proto.frames
    ]

  @property
  def child_frame_ids(self) -> List[object_world_ids.ObjectWorldResourceId]:
    return [
        object_world_ids.ObjectWorldResourceId(frame.id)
        for frame in self._proto.frames
        if not frame.HasField('parent_frame')
    ]

  @property
  def child_frame_names(self) -> List[object_world_ids.FrameName]:
    return [
        object_world_ids.FrameName(frame.name)
        for frame in self._proto.frames
        if not frame.HasField('parent_frame')
    ]

  @property
  def child_frames(self) -> List[Frame]:
    return [
        Frame(frame_proto, self._stub)
        for frame_proto in self._proto.frames
        if not frame_proto.HasField('parent_frame')
    ]

  def get_frame(self, frame_name: object_world_ids.FrameName) -> Frame:
    """Returns an frame by its object-wide unique name.

    Args:
      frame_name: The name of the frame.

    Returns:
      A frame belonging to the object.
    """
    for frame_proto in self._proto.frames:
      if object_world_ids.FrameName(frame_proto.name) == frame_name:
        return Frame(frame_proto, self._stub)
    raise ValueError(
        f'Frame with name "{frame_name}" attached to the object'
        f'{self.name}" does not exist.'
    )

  def _get_child_object(
      self, child_name: object_world_ids.WorldObjectName
  ) -> TransformNode:
    return create_object_with_auto_type(
        self._get_child_proto(child_name), self._stub
    )

  @error_handling.retry_on_grpc_unavailable
  def _get_child_proto(
      self, child_name: object_world_ids.WorldObjectName
  ) -> object_world_service_pb2.Object:
    """Returns the child object by its object-wide unique name.

    Args:
      child_name: The name of the child

    Returns:
      The child with child_name that belongs to the object
    """
    child_id = next(
        child.id for child in self._proto.children if child.name == child_name
    )
    request = object_world_service_pb2.GetObjectRequest(
        world_id=self._proto.world_id,
        object=object_world_refs_pb2.ObjectReference(id=child_id),
        view=object_world_updates_pb2.ObjectView.FULL,
    )
    return self._stub.GetObject(request)

  @property
  def parent_name(self) -> object_world_ids.WorldObjectName:
    return object_world_ids.WorldObjectName(self._proto.parent.name)

  @property
  def parent_id(self) -> object_world_ids.ObjectWorldResourceId:
    return object_world_ids.ObjectWorldResourceId(self._proto.parent.id)

  @property
  def child_ids(self) -> List[object_world_ids.ObjectWorldResourceId]:
    return [
        object_world_ids.ObjectWorldResourceId(child.id)
        for child in self._proto.children
    ]

  @property
  def child_names(self) -> List[object_world_ids.WorldObjectName]:
    return [
        object_world_ids.WorldObjectName(child.name)
        for child in self._proto.children
    ]

  def _debug_hint(self) -> str:
    if self.id == object_world_ids.ROOT_OBJECT_ID:
      return ''
    return 'Created from path {}'.format(
        '.'.join(['world'] + list(self._proto.object_full_path.object_names))
    )

  @property
  def reference(self) -> object_world_refs_pb2.ObjectReference:
    if self._proto.name_is_global_alias:
      return object_world_refs_pb2.ObjectReference(
          by_name=object_world_refs_pb2.ObjectReferenceByName(
              object_name=self.name
          )
      )
    return object_world_refs_pb2.ObjectReference(
        id=self.id, debug_hint=self._debug_hint()
    )

  @property
  def transform_node_reference(
      self,
  ) -> object_world_refs_pb2.TransformNodeReference:
    if self._proto.name_is_global_alias:
      return object_world_refs_pb2.TransformNodeReference(
          by_name=object_world_refs_pb2.TransformNodeReferenceByName(
              object=object_world_refs_pb2.ObjectReferenceByName(
                  object_name=self.name
              )
          )
      )
    return object_world_refs_pb2.TransformNodeReference(
        id=self.id, debug_hint=self._debug_hint()
    )

  @property
  def parent(self) -> Optional['WorldObject']:
    if self._proto.type == object_world_service_pb2.ObjectType.ROOT:
      return None

    request = object_world_service_pb2.GetObjectRequest(
        world_id=self._proto.world_id,
        object=object_world_refs_pb2.ObjectReference(id=self.parent_id),
        view=object_world_updates_pb2.ObjectView.FULL,
    )
    object_proto = self._stub.GetObject(request)
    return WorldObject(object_proto, self._stub)

  @property
  def parent_t_this(self) -> data_types.Pose3:
    return math_proto_conversion.pose_from_proto(
        self._proto.object_component.parent_t_this
    )

  def __getattr__(self, child_name: str) -> TransformNode:
    if object_world_ids.WorldObjectName(child_name) in self.child_names:
      return self._get_child_object(
          object_world_ids.WorldObjectName(child_name)
      )
    elif object_world_ids.FrameName(child_name) in self.frame_names:
      return self.get_frame(object_world_ids.FrameName(child_name))

    raise AttributeError(
        f'{self.__repr__()} does not have a child frame, child object  or '
        f'member with name "{child_name}".'
    )

  def __dir__(self) -> List[str]:
    return sorted(
        list(self.frame_names)
        + list(self.child_names)
        + _list_public_methods(self)
    )

  def __repr__(self):
    return f'<{self.__class__.__name__}(name={self.name}, id={self.id})>'

  def __str__(self):
    lines: List[str] = []
    lines.append(f'{self.name}: {self.__class__.__name__}(id={self.id})')
    lines += [
        f' |=> {child_name} (id={child_id})'
        for child_name, child_id in zip(self.child_names, self.child_ids)
    ]
    lines += [
        f' |-> {frame.name}: Frame(id={frame.id})' for frame in self.frames
    ]
    return '\n'.join(lines)

  @property
  def proto(self) -> object_world_service_pb2.Object:
    return self._proto


class JointConfiguration:
  """Represents configurations in joint space.

  Attributes:
    joint_position: [float] storing the joint position values.
  """

  def __init__(self, joint_position: List[float]):
    self.joint_position: List[float] = joint_position


class JointConfigurations:
  """Manages joint configurations for a specific robot.

  JointConfigurations has named motion targets as attributes which are created
  after the creation.

  Attributes:
    joint_configuration_name: A JointConfiguration.
  """

  def __init__(self, joint_motion_targets: Dict[str, JointConfiguration]):
    for name, target in joint_motion_targets.items():
      setattr(self, name, target)


class KinematicObject(WorldObject):
  """A local copy of a kinematic object in the world.

  Subtype for physical objects that have moveable joints (prismatic or
  revolute). This includes not only robots but also, e.g., finger grippers or
  fixtures with moveable clamps.

  Attributes:
    joint_positions: The joint positions in radians (for revolute joints) or
      meters (for prismatic joints).
    joint_entity_ids: The IDs of the joint entities of this kinematic object.
    joint_entity_names: The names of the joint entities of this kinematic
      object.
    joint_application_limits: The joint application limits. The field
      JointLimits.max_effort is currently not supported and will always contain
      zeroes.
    joint_system_limits: The joint system limits. The field
      JointLimits.max_effort is currently not supported and will always contain
      zeroes.
    cartesian_limits: The cartesian limits for this kinematic object.
    iso_flange_frame_ids: Ids of the frames on this kinematic object which mark
      flanges according to the ISO 9787 standard. Not every kinematic object has
      flange frames, but callers can expect this method to return one flange
      frame for every "robot arm" contained in the kinematic object.
    iso_flange_frame_names: Names of flange frames (see 'frame_ids').
    iso_flange_frames: Flange frames (see 'frame_ids').
    joint_configurations: Joint configurations belonging to this kinematic
      object.
  """

  def __init__(
      self,
      world_object: object_world_service_pb2.Object,
      stub: object_world_service_pb2_grpc.ObjectWorldServiceStub,
  ):
    if not world_object.HasField('kinematic_object_component'):
      raise ValueError(
          'The world_object proto is missing the field '
          '"kinematic_object_component". Cannot create a '
          f'{self.__class__.__name__} without this field.'
      )
    super().__init__(world_object, stub)

  @property
  def joint_positions(self) -> List[float]:
    return [
        float(joint_position)
        for joint_position in self._proto.kinematic_object_component.joint_positions
    ]

  @property
  def joint_entity_ids(self) -> List[str]:
    return [
        str(joint_entity_id)
        for joint_entity_id in self._proto.kinematic_object_component.joint_entity_ids
    ]

  @property
  def joint_entity_names(self) -> List[str]:
    return [
        self._proto.entities[joint_entity_id].name
        for joint_entity_id in self._proto.kinematic_object_component.joint_entity_ids
    ]

  @property
  def joint_application_limits(self) -> joint_limits_pb2.JointLimits:
    return self._proto.kinematic_object_component.joint_application_limits

  @property
  def joint_system_limits(self) -> joint_limits_pb2.JointLimits:
    return self._proto.kinematic_object_component.joint_system_limits

  @property
  def cartesian_limits(self) -> cart_space_pb2.CartesianLimits:
    return self._proto.kinematic_object_component.cartesian_limits

  @property
  def iso_flange_frame_ids(
      self,
  ) -> List[object_world_ids.ObjectWorldResourceId]:
    return [
        object_world_ids.ObjectWorldResourceId(id_and_name.id)
        for id_and_name in self._proto.kinematic_object_component.iso_flange_frames
    ]

  @property
  def iso_flange_frame_names(self) -> List[object_world_ids.FrameName]:
    return [
        object_world_ids.FrameName(id_and_name.name)
        for id_and_name in self._proto.kinematic_object_component.iso_flange_frames
    ]

  @property
  def iso_flange_frames(self) -> List[Frame]:
    flanges = self.iso_flange_frame_ids
    return [
        Frame(frame, self._stub)
        for frame in self._proto.frames
        if frame.id in flanges
    ]

  def get_single_iso_flange_frame(self) -> Frame:
    """Returns the single flange frame of this kinematic object.

    If 'self.iso_flange_frames' contains exactly one flange frame, returns this
    flange frame.

    Raises:
      LookupError: If there are zero or more than one flange frames.
    """
    frames = self.iso_flange_frames
    if not frames:
      raise LookupError(
          f'Kinematic object "{self.name}" does not have any flange '
          'frame configured, but exactly one was expected.'
      )
    elif len(frames) > 1:
      flange_frame_names = ', '.join([frame.name for frame in frames])
      raise LookupError(
          f'Kinematic object "{self.name}" has more than one flange frame '
          'configured, but exactly one was expected. The available flange '
          f'frames are: {flange_frame_names}.'
      )
    return frames[0]

  @property
  def joint_configurations(self) -> JointConfigurations:
    return JointConfigurations({
        target.name: JointConfiguration(list(target.joint_positions))
        for target in self._proto.kinematic_object_component.named_joint_configurations
    })


def create_object_with_auto_type(
    object_proto: object_world_service_pb2.Object,
    stub: object_world_service_pb2_grpc.ObjectWorldServiceStub,
) -> WorldObject:
  """Creates an object from a object proto.

  The type of the object is determined by the proto attribute and the
  corresponding Python object is returned.

  Args:
    object_proto: The object proto.
    stub:  The object world service stub.

  Returns:
    An object in the world.
  """
  if object_proto.type == object_world_service_pb2.ObjectType.KINEMATIC_OBJECT:
    return KinematicObject(object_proto, stub)
  else:
    return WorldObject(object_proto, stub)
