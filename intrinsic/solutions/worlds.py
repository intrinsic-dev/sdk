# Copyright 2023 Intrinsic Innovation LLC

"""Extends the general ObjectWorldClient with Workcell API specific features."""

from typing import Optional, Union

import grpc
from intrinsic.geometry.service import geometry_service_pb2_grpc
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.motion_planning.proto import motion_target_pb2
from intrinsic.solutions import ppr
from intrinsic.solutions import utils
from intrinsic.world.proto import collision_settings_pb2
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.proto import object_world_service_pb2_grpc
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources

TransformNodeTypes = Union[
    object_world_resources.TransformNode,
    object_world_refs_pb2.ObjectReference,
    object_world_refs_pb2.FrameReference,
    object_world_refs_pb2.TransformNodeReference,
]


def _object_world_resource_to_transform_node_reference(
    field: TransformNodeTypes,
) -> object_world_refs_pb2.TransformNodeReference:
  """Maps a object world resource to a TransformNodeReference."""
  if isinstance(field, object_world_resources.TransformNode):
    return field.transform_node_reference
  elif isinstance(field, object_world_refs_pb2.ObjectReference):
    if field.WhichOneof("object_reference") == "id":
      return object_world_refs_pb2.TransformNodeReference(id=field.id)
    if field.WhichOneof("object_reference") == "by_name":
      return object_world_refs_pb2.TransformNodeReference(
          by_name=object_world_refs_pb2.TransformNodeReferenceByName(
              object=field.by_name
          )
      )
  elif isinstance(field, object_world_refs_pb2.FrameReference):
    if field.WhichOneof("frame_reference") == "id":
      return object_world_refs_pb2.TransformNodeReference(id=field.id)
    if field.WhichOneof("frame_reference") == "by_name":
      return object_world_refs_pb2.TransformNodeReference(
          by_name=object_world_refs_pb2.TransformNodeReferenceByName(
              frame=field.by_name
          )
      )
  elif isinstance(field, object_world_refs_pb2.TransformNodeReference):
    return field
  raise ValueError(
      f"{field} cannot be converted to a "
      "object_world_refs_pb2.TransformNodeReference"
  )


class ObjectWorldExternal(object_world_client.ObjectWorldClient):
  """Extends an ObjectWorldClient with a connect method."""

  @classmethod
  def connect(
      cls,
      world_id: str,
      grpc_channel: grpc.Channel,
  ) -> "ObjectWorldExternal":
    stub = object_world_service_pb2_grpc.ObjectWorldServiceStub(grpc_channel)
    geometry_stub = geometry_service_pb2_grpc.GeometryServiceStub(grpc_channel)
    return cls(world_id, stub, geometry_stub)

  def create_object_from_product_part(  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
      self,
      *,
      part: ppr.ProductPart,
      object_name: object_world_ids.WorldObjectName,
      parent: Optional[object_world_resources.WorldObject] = None,
      parent_object_t_created_object: Optional[
          data_types.Pose3
      ] = data_types.Pose3(),
  ) -> None:
    """Adds a product part as object to the world.

    Arguments:
      part: The ProductPart to add.
      object_name: The name of the newly created object.
      parent: The parent object the new product object will be attached to.
      parent_object_t_created_object: The transform between the parent object
        and the new product object.
    """
    super().create_object_from_product_part(
        product_part_name=part.name,
        object_name=object_name,
        parent=parent,
        parent_object_t_created_object=parent_object_t_created_object,
    )


ObjectWorld = ObjectWorldExternal


class CollisionSettings:
  """Class used to represent the settings used for collision checking.

  This class can be used to disable collision checking.

  Example: Return an instance of CollistionSettings with collision checking
      disabled:

    disabled_collision_checking = CollisionSettings.disabled
  """

  def __init__(self, disable_collision_checking: bool = False):
    """Construct a CollisionSettings class.

    Args:
      disable_collision_checking: Whether collision checking is disabled.
    """
    self.disable_collision_checking: bool = disable_collision_checking

  @property
  def proto(self) -> collision_settings_pb2.CollisionSettings:
    """Returns a proto constructed from CollisionSettings object.

    Returns:
      constructed collision_settings_pb2.CollisionSettings proto
    """
    return collision_settings_pb2.CollisionSettings(
        disable_collision_checking=self.disable_collision_checking
    )

  @utils.classproperty
  def disabled(cls) -> "CollisionSettings":  # pylint:disable=no-self-argument
    """Returns a CollisionSettings object where disable_collision_checking=True.

    Since disabling collision checking is fairly common, this method is provided
    for convenience.

    Returns:
     CollisionObject with disable_collision_checking=True.
    """
    return CollisionSettings(disable_collision_checking=True)


class CartesianMotionTarget:
  """Represents motion targets in Cartesian space.

  The target has two required parameters: tool and frame. If only
  those two are specified, the target is interpreted as "align the
  tool with frame".

  Optionally, you can also provide offset, which introduces
  a local transform between frame and tool target.

  The tool will be aligned with a transform from to target,
  world_t_target, computed as:
       world_t_target = world_t_frame * offset
  where offset will be the identity transform if left undefined.

  Example 1: Align gripper with awesome_frame:
    target_1 = CartesianMotionTarget(tool=gripper, frame=awesome_frame)

  Example 2: Place the gripper 10cm shifted along to the x-axis
  of awesome_frame:
    target_2 = CartesianMotionTarget(
      tool=gripper, frame=awesome_frame,
      offset=Pose3(translation=[0.1, 0, 0]))

  Example 3: Move the gripper 10cm forward (along z-axis) in its
  own coordinate frame:
    target_2 = CartesianMotionTarget(
      tool=gripper, frame=gripper,
      offset=Pose3(translation=[0, 0, 0.1]))

  Attributes:
    tool: World resource of the tool whose pose this target specifies.
    frame: World resource of the frame with which to align the tool.
    offset: Optional offset between frame and tool pose.
    proto: Representation as motion_planner_service_pb2.CartesianMotionTarget
      proto.
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      offset: Optional[data_types.Pose3] = None,
  ):
    """Constructs a motion target in Cartesian space.

    Args:
      tool: World Object or Frame corresponding to the robot link / object whose
        pose you wish to specify.
      frame: The target Object or Frame.
      offset: Optional transform allowing to specify a local offset between the
        frame and tool.
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.offset: data_types.Pose3 = offset or data_types.Pose3()

  @property
  def proto(self) -> motion_target_pb2.CartesianMotionTarget:
    """Returns a proto constructed from CartesianMotionTarget object.

    Returns:
      Constructed motion_planner_service_pb2.CartesianMotionTarget proto
    """
    motion_target_proto = motion_target_pb2.CartesianMotionTarget(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        offset=math_proto_conversion.pose_to_proto(self.offset),
    )
    return motion_target_proto

  @classmethod
  def from_proto(
      cls, target: motion_target_pb2.CartesianMotionTarget
  ) -> "CartesianMotionTarget":
    return cls(
        tool=target.tool,
        frame=target.frame,
        offset=math_proto_conversion.pose_from_proto(target.offset),
    )
