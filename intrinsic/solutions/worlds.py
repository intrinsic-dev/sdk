# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Extends the general ObjectWorldClient with Workcell API specific features."""

from typing import List, Optional, Union

import grpc
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.kinematics.ik.constrained import constrained_ik_pb2
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
    return cls(world_id, stub)

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


class PointConstraint:
  """Class used to represent a constraint where only the position is defined.

  PointConstraint has two required parameters: tool and frame. If only those two
  are specified, the target is interpreted as "move tool to the same position as
  frame". Please note that the frames are not aligned with respect to their
  orientation. The frames are considered successfully aligned if their positions
  match.

  Optionally, you can also provide an offset position vector, which introduces a
  local transform between the frame and tool target.

  The tool frame origin will be located at world_p_target, computed as:
    world_p_target = world_t_frame * p_offset_in_frame

  Examples 1: Move gripper to the position of a desired_frame:
    constraint_1 = PointConstraint(tool = world.gripper, frame = desired_frame)

  Example 2: Move the gripper to a location 10 cm shifted along the x-axis in
  the desired_frame.
    constraint_2 = PointConstraint(tool = world.gripper, frame = desired_frame,
    p_offset_in_frame=[0.1,0,0])

  Example 3: Move the gripper 10cm forward along z-axis in its own coordinate
  frame:
    constraint_3 = PointConstraint (tool = world.gripper, frame = world.gripper,
    p_offset_in_frame = [0,0,0.1])


  Attributes:
    tool: World Object or Frame that defines the tool we want to move.
    frame: World Object or Frame which to align the tool.
    p_offset_in_frame: Optional position offset between frame and tool.
    max_position_error: Optional maximum allowed position error, in meters,
      i.e., max l1-norm error, defaults to 1e-4.
    proto: Represent as motion_target_pb2.PointConstraint proto
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      p_offset_in_frame: Optional[data_types.VECTOR_TYPE] = None,
      max_position_error: Optional[float] = None,
  ):
    """Construct a point constraint for a tool frame.

    Args:
      tool: World Object or Frame corresponding to the robot link/object whose
        position you wish to specify.
      frame: World Object or Frame that specifies the position you would like to
        move to.
      p_offset_in_frame: Optional position offset allowing to specify a local
        offset between the frame and tool position.
      max_position_error: Optional maximum allowed position error, in meters,
        i.e., max l1-norm error, defaults to 1e-4.
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    if p_offset_in_frame is None:
      self.p_offset_in_frame = []
    else:
      self.p_offset_in_frame = data_types.vector_util.as_vector3(
          p_offset_in_frame,
          dtype=data_types.np.float64,
          err_msg="p_offset_in_frame vector in PointConstraint",
      ).copy()
    self.max_position_error: Optional[float] = max_position_error

  @property
  def proto(self) -> motion_target_pb2.PointConstraint:
    """Returns a proto constructed from PointConstraint object.

    Returns:
      Constructed motion_target_pb2.PointConstraint proto.
    """
    constraint_proto = motion_target_pb2.PointConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
    )
    if self.p_offset_in_frame.__len__() > 0:
      constraint_proto.p_offset_in_frame.CopyFrom(
          math_proto_conversion.ndarray_to_point_proto(self.p_offset_in_frame)
      )
    if self.max_position_error is not None:
      constraint_proto.max_position_error = self.max_position_error
    return constraint_proto

  @classmethod
  def from_proto(
      cls, constraint_proto: motion_target_pb2.PointConstraint
  ) -> "PointConstraint":
    """Constructs a PointConstraint class from a proto representation.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      PointConstraint from a proto representation.
    """

    p_offset_in_frame = None
    if constraint_proto.HasField("p_offset_in_frame"):
      p_offset_in_frame = math_proto_conversion.ndarray_from_point_proto(
          constraint_proto.p_offset_in_frame
      )
    max_position_error = None
    if constraint_proto.max_position_error:
      max_position_error = constraint_proto.max_position_error
    return cls(
        tool=constraint_proto.tool,
        frame=constraint_proto.frame,
        p_offset_in_frame=p_offset_in_frame,
        max_position_error=max_position_error,
    )


class PoseConstraint:
  """Class used to represent a Cartesian pose as a constraint.

  The pose constraint has two required parameters: tool and frame. If only
  those two are specified, the target is interpreted as "align the
  tool with frame".

  Optionally, you can also provide an offset, which introduces
  a local transform between frame and tool target.

  The tool will be aligned with a transform from to target,
  world_t_target, computed as:
       world_t_target = world_t_frame * offset_in_frame
  where offset will be the identy transform if left undefined.

  Example 1: Align gripper with awesome_frame:
    target_1 = PoseConstraint(tool=gripper, frame=awesome_frame)

  Example 2: Place the gripper 10cm shifted along to the x-axis
  of awesome_frame:
    target_2 = PoseConstraint(
      tool=gripper, frame=awesome_frame,
      offset_in_frame=Pose3(translation=[0.1, 0, 0]))

  Example 3: Move the gripper 10cm forward (along z-axis) in its
  own coordinate frame:
    target_2 = PoseConstraint(
      tool=gripper, frame=gripper,
      offset_in_frame=Pose3(translation=[0, 0, 0.1]))


  Attributes:
    tool: World Object or Frame that defines the tool whose pose this target
      specifies.
    frame: World Object or Frame which to align the tool.
    offset_in_frame: Optional offset transfrom between frame and tool pose.
    max_position_error: Optional maximum allowed position error, in meters,
      i.e., max l1-norm error, defaults to 1e-4.
    max_rotational_error: Optional  maximum angle (in radians) between the
      orientation of the tip and the orientation of the target pose.
    proto: Represent as motion_target_pb2.PoseConstraint proto.
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      offset_in_frame: Optional[data_types.Pose3] = None,
      max_position_error: Optional[float] = None,
      max_rotational_error: Optional[float] = None,
  ):
    """Construct a pose constraint for a tool object.

    Args:
      tool: World Object or Frame corresponding to the robot link / object whose
        pose you wish to specify.
      frame: The target Object or Frame.
      offset_in_frame: Optional transform allowing to specify a local offset
        between the frame and tool.
      max_position_error: Optional maximum allowed position error
      max_rotational_error: Optional  maximum angle (in radians) between the
        orientation of the tip and the orientation of the target pose.
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.offset_in_frame: data_types.Pose3 = (
        offset_in_frame or data_types.Pose3()
    )
    self.max_position_error: Optional[float] = max_position_error
    self.max_rotational_error: Optional[float] = max_rotational_error

  @property
  def proto(self) -> motion_target_pb2.PoseConstraint:
    """Returns a proto constructed from PoseConstraint object.

    Returns:
      Constructed motion_target_pb2.PoseConstraint proto.
    """
    constraint_proto = motion_target_pb2.PoseConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        offset_in_frame=math_proto_conversion.pose_to_proto(
            self.offset_in_frame
        ),
    )
    if self.max_position_error is not None:
      constraint_proto.max_position_error = self.max_position_error
    if self.max_rotational_error is not None:
      constraint_proto.max_angle_deviation = self.max_rotational_error
    return constraint_proto

  @classmethod
  def from_proto(
      cls, target: motion_target_pb2.PoseConstraint
  ) -> "PoseConstraint":
    """Constructs a PoseConstraint class from a proto representation.

    Args:
       target: proto to be converted.

    Returns:
     PoseConstraint from a proto representation.
    """

    offset_in_frame = None
    if target.offset_in_frame:
      offset_in_frame = math_proto_conversion.pose_from_proto(
          target.offset_in_frame
      )
    max_position_error = None
    if target.max_position_error:
      max_position_error = target.max_position_error
    max_angle_deviation = None
    if target.max_angle_deviation:
      max_angle_deviation = target.max_angle_deviation
    return cls(
        tool=target.tool,
        frame=target.frame,
        offset_in_frame=offset_in_frame,
        max_position_error=max_position_error,
        max_rotational_error=max_angle_deviation,
    )


class PoseWithFreeAxisConstraint:
  """Class used to represent a pose constraints with a free rotation axis.

  Equality constraint that allows to define the position and orientation with a
  free rotation about a user-defined axis. The PoseWithFreeAxisConstraint() has
  three required parameters: tool, frame, and target_axis_in_frame. If only
  those three are specified, the target is interpreted as "align tool with
  frame, but allow for rotation around the target_axis", i.e., tool frame can
  freely rotate around target_axis.

  Optionally, you can also provide an offset, which introduces a local transform
  between frame and target target frame.

  Optionally, you can also provide a max_rotational_error and tolerance_rad. The
  max_position_error defines the maximum allowed position l1-norm error in
  meters. Tolerance_rad defines the maximum allowed angle between the two axis,
  the target_axis in the frame defined by world_t_frame * offset_in_frame *
  target_axis_in_frame and the target_axis in tool frame.

  Example 1: Define a motion target that moves the gripper frame to the
    awesome_frame, but that does allows free rotation around the z-axis.
    target_1 = PoseWithFreeAxisConstraint(tool=gripper, frame=awesome_frame,
      target_axis_in_frame=[0,0,1])

  Example 2: Define a motion target that moves the gripper to a location 5 cm
    in z-direction in front of object. Allow free rotation around the z-axis.
    target_2 = PoseWithFreeAxisConstraint(tool=gripper, frame=object,
      target_axis_in_frame=[0,0,1],
      offset_in_frame=Pose3(tranlation=[0,0,0.05]))

  Attributes:
    tool: World Object or Frame that defines the tool whose pose this target
      specifies.
    frame: World Object or Frame which to align the tool.
    target_axis_in_frame: Unit vector that describes the free axis in the frame.
    offset_in_frame: Optional offset transform between frame and tool pose.
    max_position_error: Optional maximum allowed position error, in meters,
      i.e., max l1-norm error, defaults to 1e-4.
    max_rotational_error: Optional maximum allowed angle between the two axes.
    proto: Representation as motion_target_pb2.PoseWithFreeAxisConstraint
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      target_axis_in_frame: data_types.VECTOR_TYPE,
      offset_in_frame: Optional[data_types.Pose3] = None,
      max_position_error: Optional[float] = None,
      max_rotational_error: Optional[float] = None,
  ):
    """Construct a PoseFreeAxisConstraint object.

    Args:
      tool: World Object or Frame that defines the tool whose pose this target
        specifies.
      frame: World Object or Frame which to align the tool.
      target_axis_in_frame: Unit vector that describes the free axis in the
        frame.
      offset_in_frame: Optional offset transform between frame and tool pose.
      max_position_error: Optional maximum allowed position error, in meters,
        i.e., max l1-norm error, defaults to 1e-4.
      max_rotational_error: Optional maximum allowed angle between the two axes.
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.target_axis_in_frame = data_types.vector_util.as_vector3(
        target_axis_in_frame,
        dtype=data_types.np.float64,
        err_msg="target_axis_in_frame vector in PoseWithFreeAxisConstraint",
    ).copy()
    self.offset_in_frame: data_types.Pose3 = (
        offset_in_frame or data_types.Pose3()
    )
    self.max_position_error: Optional[float] = max_position_error
    self.max_rotational_error: Optional[float] = max_rotational_error

  @property
  def proto(self) -> motion_target_pb2.PoseWithFreeAxisConstraint:
    """Returns a proto constructed from PoseWithFreeAxisConstraint object.

    Returns:
      Constructed motion_target_pb2.PoseWithFreeAxisConstraint proto.
    """
    constraint_proto = motion_target_pb2.PoseWithFreeAxisConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        target_axis_in_frame=math_proto_conversion.ndarray_to_point_proto(
            self.target_axis_in_frame
        ),
    )
    if self.offset_in_frame is not None:
      constraint_proto.offset_in_frame.CopyFrom(
          math_proto_conversion.pose_to_proto(self.offset_in_frame)
      )
    if self.max_position_error is not None:
      constraint_proto.max_position_error = self.max_position_error
    if self.max_rotational_error is not None:
      constraint_proto.tolerance_rad = self.max_rotational_error
    return constraint_proto

  @classmethod
  def from_proto(
      cls, constraint_proto: motion_target_pb2.PoseWithFreeAxisConstraint
  ) -> "PoseWithFreeAxisConstraint":
    """Constructs a PoseWithFreeAxisConstraint class from a proto.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      PoseWithFreeAxisConstraint from a proto representation.
    """

    target_axis_in_frame = math_proto_conversion.ndarray_from_point_proto(
        constraint_proto.target_axis_in_frame
    )
    offset_in_frame = None
    if constraint_proto.offset_in_frame:
      offset_in_frame = math_proto_conversion.pose_from_proto(
          constraint_proto.offset_in_frame
      )
    max_position_error = None
    if constraint_proto.max_position_error:
      max_position_error = constraint_proto.max_position_error
    tolerance_rad = None
    if constraint_proto.tolerance_rad:
      tolerance_rad = constraint_proto.tolerance_rad
    return cls(
        tool=constraint_proto.tool,
        frame=constraint_proto.frame,
        target_axis_in_frame=target_axis_in_frame,
        offset_in_frame=offset_in_frame,
        max_position_error=max_position_error,
        max_rotational_error=tolerance_rad,
    )


class PoseConeConstraint:
  """Representation of a motion target as a pose cone constraint.

  A PoseConeConstraint aligns a user-defined axis of a tool frame with the
  target frame within the defined cone. The PoseConeConstraint() has four
  required parameters: tool, frame, cone_axis_in_frame, and
  cone_opening_half_angle_rad. If only those are specified, the target is
  interpreted as "align tool with frame" but allow a deviation of the tool
  cone_axis from the frame cone axis by cone_opening_half_angle_rad.

  Optionally, you can also provide an offset, which introduces a local transform
  between frame and tool target. If the cone_opening_half_angle is set to zero
    world_t_tool*cone_axis = world_t_frame * offset_in_frame * cone_axis

  Optionally, you can also provide a max_position_error and max_rotational_error
  . The max_position_error defines the maximum allowed position l1-norm error in
  meters. Tolerance_rad defines the maximum allowed angle between the two axis,
  the target_axis in the frame defined by world_t_frame * offset_in_frame *
  target_axis_in_frame and the target_axis in tool frame.

  Attributes:
    tool: World Object or Frame that defines the tool whose pose this target
      specifies.
    frame: World Object or Frame which to align the tool.
    cone_axis_in_frame: Unit vector that describes the free axis in the frame.
    cone_opening_half_angle_rad: Opening half-angle of the cone in radians
    offset_in_frame: Optional offset transform between frame and tool pose.
    max_position_error: Optional maximum allowed position error, in meters,
      i.e., max l1-norm error, defaults to 1e-4.
    max_rotational_error: Optional maximum allowed angle between the two axes.
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      cone_axis_in_frame: data_types.VECTOR_TYPE,
      cone_opening_half_angle_rad: float,
      offset_in_frame: Optional[data_types.Pose3] = None,
      max_position_error: Optional[float] = None,
      max_rotational_error: Optional[float] = None,
  ):
    """Construct a PoseConeConstraint to define motion targt constraints.

    Args:
      tool: World Object or Frame corresponding to the robot link/object whose
        pose this target specifies.
      frame: World Object or Frame which to align the tool.
      cone_axis_in_frame: Unit vector that describes the free axis in the frame.
      cone_opening_half_angle_rad: Opening half-angle of the cone in radians
      offset_in_frame: Optional offset transform between frame and tool pose.
      max_position_error: Optional maximum allowed position error, in meters,
        i.e., max l1-norm error, defaults to 1e-4.
      max_rotational_error: Optional maximum allowed angle between the two axes.
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.cone_axis_in_frame = data_types.vector_util.as_vector3(
        cone_axis_in_frame,
        dtype=data_types.np.float64,
        err_msg="cone_axis_in_frame vector in PoseConeConstraint",
    ).copy()
    self.cone_opening_half_angle_rad: float = cone_opening_half_angle_rad
    self.offset_in_frame: data_types.Pose3 = (
        offset_in_frame or data_types.Pose3()
    )
    self.max_position_error: Optional[float] = max_position_error
    self.max_rotational_error: Optional[float] = max_rotational_error

  @property
  def proto(self) -> motion_target_pb2.PoseConeConstraint:
    """Returns a proto constructed from PoseConeConstraint object.

    Returns:
      Constructed motion_target_pb2.PoseConeConstraint proto.
    """
    constraint_proto = motion_target_pb2.PoseConeConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        cone_axis_in_frame=math_proto_conversion.ndarray_to_point_proto(
            self.cone_axis_in_frame
        ),
        cone_opening_half_angle_rad=self.cone_opening_half_angle_rad,
    )
    if self.offset_in_frame is not None:
      constraint_proto.offset_in_frame.CopyFrom(
          math_proto_conversion.pose_to_proto(self.offset_in_frame)
      )
    if self.max_position_error is not None:
      constraint_proto.max_position_error = self.max_position_error
    if self.max_rotational_error is not None:
      constraint_proto.tolerance_rad = self.max_rotational_error
    return constraint_proto

  @classmethod
  def from_proto(
      cls, constraint_proto: motion_target_pb2.PoseConeConstraint
  ) -> "PoseConeConstraint":
    """Constructs a PoseConeConstraint class from a proto representation.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      PoseConeConstraint from a proto representation.
    """

    cone_axis_in_frame = math_proto_conversion.ndarray_from_point_proto(
        constraint_proto.cone_axis_in_frame
    )
    cone_opening_half_angle_rad = constraint_proto.cone_opening_half_angle_rad
    offset_in_frame = None
    if constraint_proto.offset_in_frame:
      offset_in_frame = math_proto_conversion.pose_from_proto(
          constraint_proto.offset_in_frame
      )
    max_position_error = None
    if constraint_proto.max_position_error:
      max_position_error = constraint_proto.max_position_error
    tolerance_rad = None
    if constraint_proto.tolerance_rad:
      tolerance_rad = constraint_proto.tolerance_rad
    return cls(
        tool=constraint_proto.tool,
        frame=constraint_proto.frame,
        cone_axis_in_frame=cone_axis_in_frame,
        cone_opening_half_angle_rad=cone_opening_half_angle_rad,
        offset_in_frame=offset_in_frame,
        max_position_error=max_position_error,
        max_rotational_error=tolerance_rad,
    )


class PositionEllipsoidConstraint:
  """Represents a ellipsoid position constraint for a tool entity.

  A PositionEllipsoidConstraint can be used to represent a motion target as a
  point constraint that enforces the tool position to be within an ellipsoid.
  The PositionEllipsoidConstraint has four required parameters: tool, frame,
  frame_t_ellipsoid_center, and the ellipsoid half-axes in the ellipse frame
  (rx,ry,rz). If only those are specified, the target is interpreted as move
  tool frame to a position within the ellipsoid centered at
  world_t_frame*frame_t_ellipsoid_center.

  Optionally, you can also provide a position offset in the tool frame, which
  introduces a local transform between tool origin and the position that will be
  aligned with the target. If this optional parameter is specified, a joint
  configuration of the robot is chosen for which the position defined by
    world_p_tcp = world_t_tool * p_offset_in_tool
  is within the ellipsoid.

  Optionally, you can also provide a max_position_error parameter that specifies
  the max allowed position deviation from the ellipsoid.

  Attributes:
    tool: World Object or Frame that defines the tool whose pose this target
      specifies.
    frame: World Object or Frame which to align the tool.
    frame_t_ellipsoid_center: Transform that describes the offset of the
      ellipsoid center relative the reference object or frame.
    rx: Ellipsoid half-axis in x dimension in the frame of the ellipse.
    ry: Elliposid half-axis in y dimension in the frame of the ellipse.
    rz: Ellipsoid half-axis in z dimension in the frame of the ellipse.
    p_offset_in_tool: Optional position offset between the tool and the point
      that has to fulfill the constraint.
    max_position_error: Optional maximum position deviation in [m].
    proto: motion_target_pb2.PoseConstraint proto representation of this
      constraint.
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      frame_t_ellipsoid_center: data_types.Pose3,
      rx: float,
      ry: float,
      rz: float,
      p_offset_in_tool: Optional[data_types.VECTOR_TYPE] = None,
      max_position_error: Optional[float] = None,
  ):
    """Construct a PositionEllipsoidConstraint.

    Args:
      tool: World Object or Frame corresponding to the robot link / object whose
        pose this target specifies.
      frame: The reference Object or Frame for the target ellipsoid.
      frame_t_ellipsoid_center: Transform that describes the offset of the
        ellipsoid center relative the reference object or frame.
      rx: Ellipsoid half-axis in x dimension in the frame of the ellipse.
      ry: Elliposid half-axis in y dimension in the frame of the ellipse.
      rz: Ellipsoid half-axis in z dimension in the frame of the ellipse.
      p_offset_in_tool: Optional position offset between the tool and the point
        that has to fulfill the constraint.
      max_position_error: Optional maximum position deviation in [m].
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.frame_t_ellipsoid_center: data_types.Pose3 = frame_t_ellipsoid_center
    self.rx: float = rx
    self.ry: float = ry
    self.rz: float = rz
    if p_offset_in_tool is None:
      self.p_offset_in_tool = []
    else:
      self.p_offset_in_tool = data_types.vector_util.as_vector3(
          p_offset_in_tool,
          dtype=data_types.np.float64,
          err_msg="p_offset_in_tool in PositionEllipsoidConstraint",
      ).copy()
    self.max_position_error: Optional[float] = max_position_error

  @property
  def proto(self) -> motion_target_pb2.PositionEllipsoidConstraint:
    """Returns a proto constructed from PositionEllipsoidConstraint object.

    Returns:
      Constructed motion_target_pb2.PositionEllipsoidConstraint proto.
    """
    constraint_proto = motion_target_pb2.PositionEllipsoidConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        frame_t_ellipsoid_center=math_proto_conversion.pose_to_proto(
            self.frame_t_ellipsoid_center
        ),
        rx=self.rx,
        ry=self.ry,
        rz=self.rz,
    )
    if self.p_offset_in_tool.__len__() > 0:
      constraint_proto.p_offset_in_tool.CopyFrom(
          math_proto_conversion.ndarray_to_point_proto(self.p_offset_in_tool)
      )
    if self.max_position_error is not None:
      constraint_proto.tolerance = self.max_position_error

    return constraint_proto

  @classmethod
  def from_proto(
      cls, constraint_proto: motion_target_pb2.PositionEllipsoidConstraint
  ) -> "PositionEllipsoidConstraint":
    """Constructs a PositionEllipsoidConstraint class from a proto.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      PositionEllipsoidConstraint from a proto representation.
    """

    frame_t_ellipsoid_center = math_proto_conversion.pose_from_proto(
        constraint_proto.frame_t_ellipsoid_center
    )
    p_offset_in_tool = None
    if constraint_proto.HasField("p_offset_in_tool"):
      p_offset_in_tool = math_proto_conversion.ndarray_from_point_proto(
          constraint_proto.p_offset_in_tool
      )
    tolerance = None
    if constraint_proto.tolerance:
      tolerance = constraint_proto.tolerance
    return cls(
        tool=constraint_proto.tool,
        frame=constraint_proto.frame,
        frame_t_ellipsoid_center=frame_t_ellipsoid_center,
        rx=constraint_proto.rx,
        ry=constraint_proto.ry,
        rz=constraint_proto.rz,
        p_offset_in_tool=p_offset_in_tool,
        max_position_error=tolerance,
    )


class PositionPlaneConstraint:
  """Constraint that enforces the tool frame to stay on one side of a plane.

  A PositionPlaneConstraint enforces the tool position to stay on one side of
  the defined plane. The PositionPlaneConstraint has four required parameters:
  tool, frame, frame_p_point_on_plane, and plane_normal_in_frame. If only those
  three are specified, the target is interpreted as "move tool frame to a
  position located on the side of the plane specified by the direction of the
  plane_normal."

  Optionally, you can also provide a position offset in the tool frame, which
  introduces a local transform between tool origin and the position that will be
  aligned with the target.

  Optionally, you can also provide a max_position_error parameter that specifies
  the max allowed position deviation from the plane side.

  Example 1: Move the position of the gripper to a position one meter above the
    ground.
    target_1 = PositionPlaneConstraint(tool=gripper, frame=world.root,
      frame_p_point_on_plane=[0,0,1], plane_normal_in_frame=[0,0,1])

  Example 2: Move the position of a tcp located 5 cm in z direction in front of
    the gripper to a location 1.5 meters above the ground.
    target_2 = PositionPlaneConstraint(tool=gripper, frame=world.root,
      frame_p_point_on_plane=[0,0,1], plane_normal_in_frame=[0,0,1],
      p_offset_in_tool=[0,0,0.05])

  Attributes:
    tool: World Object or Frame that defines the tool whose pose this target
      specifies.
    frame: World Object or Frame which to align the tool.
    frame_p_point_on_plane: Vector that defines the point on the plane.
    plane_normal_in_frame: Unit vector that defines the normal of the plane.
    p_offset_in_tool: Optional position offset between the tool and the point
      that has to fulfill the constraint.
    max_position_error: Optional maximum position deviation in [m].
    proto: Represents a PositionPlaneConstraint as
      motion_target_pb2.PositionPlaneConstraint proto.
  """

  def __init__(
      self,
      tool: TransformNodeTypes,
      frame: TransformNodeTypes,
      frame_p_point_on_plane: data_types.VECTOR_TYPE,
      plane_normal_in_frame: data_types.VECTOR_TYPE,
      p_offset_in_tool: Optional[data_types.VECTOR_TYPE] = None,
      max_position_error: Optional[float] = None,
  ):
    """Construct a position plane constraint.

    Args:
      tool: World Object or Frame that defines the tool whose pose this target
        specifies.
      frame: World Object or Frame which to align the tool.
      frame_p_point_on_plane: Vector that defines the point on the plane.
      plane_normal_in_frame: Unit vector that defines the normal of the plane.
      p_offset_in_tool: Optional position offset between the tool and the point
        that has to fulfill the constraint.
      max_position_error: Optional maximum position deviation in [m].
    """
    self.tool: TransformNodeTypes = tool
    self.frame: TransformNodeTypes = frame
    self.frame_p_point_on_plane: data_types.VECTOR_TYPE = (
        data_types.vector_util.as_vector3(
            frame_p_point_on_plane,
            dtype=data_types.np.float64,
            err_msg="frame_p_point_on_plane in PositionPlaneConstraint",
        ).copy()
    )
    self.plane_normal_in_frame: data_types.VECTOR_TYPE = (
        data_types.vector_util.as_vector3(
            plane_normal_in_frame,
            dtype=data_types.np.float64,
            err_msg="plane_normal_in_frame in PositionPlaneConstraint",
        ).copy()
    )
    if p_offset_in_tool is None:
      self.p_offset_in_tool = []
    else:
      self.p_offset_in_tool = data_types.vector_util.as_vector3(
          p_offset_in_tool,
          dtype=data_types.np.float64,
          err_msg="p_offset_in_tool in PositionPlaneConstraint",
      ).copy()
    self.max_position_error: Optional[float] = max_position_error

  @property
  def proto(self) -> motion_target_pb2.PositionPlaneConstraint:
    """Returns a proto constructed from PositionPlaneConstraint object.

    Returns:
      Constructed motion_target_pb2.PositionPlaneConstraint proto.
    """
    constraint_proto = motion_target_pb2.PositionPlaneConstraint(
        tool=_object_world_resource_to_transform_node_reference(self.tool),
        frame=_object_world_resource_to_transform_node_reference(self.frame),
        plane_normal_in_frame=math_proto_conversion.ndarray_to_point_proto(
            self.plane_normal_in_frame
        ),
        frame_p_point_on_plane=math_proto_conversion.ndarray_to_point_proto(
            self.frame_p_point_on_plane
        ),
    )
    if self.p_offset_in_tool.__len__() > 0:
      constraint_proto.p_offset_in_tool.CopyFrom(
          math_proto_conversion.ndarray_to_point_proto(self.p_offset_in_tool)
      )
    if self.max_position_error is not None:
      constraint_proto.tolerance = self.max_position_error
    return constraint_proto

  @classmethod
  def from_proto(
      cls, constraint_proto: motion_target_pb2.PositionPlaneConstraint
  ) -> "PositionPlaneConstraint":
    """Constructs a PositionPlaneConstraint class from a proto representation.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      PositionPlaneConstraint from a proto representation.
    """

    frame_p_point_on_plane = math_proto_conversion.ndarray_from_point_proto(
        constraint_proto.frame_p_point_on_plane
    )
    plane_normal_in_frame = math_proto_conversion.ndarray_from_point_proto(
        constraint_proto.plane_normal_in_frame
    )
    p_offset_in_tool = None
    if constraint_proto.HasField("p_offset_in_tool"):
      p_offset_in_tool = math_proto_conversion.ndarray_from_point_proto(
          constraint_proto.p_offset_in_tool
      )
    tolerance = None
    if constraint_proto.tolerance:
      tolerance = constraint_proto.tolerance
    return cls(
        tool=constraint_proto.tool,
        frame=constraint_proto.frame,
        frame_p_point_on_plane=frame_p_point_on_plane,
        plane_normal_in_frame=plane_normal_in_frame,
        p_offset_in_tool=p_offset_in_tool,
        max_position_error=tolerance,
    )


class JointPositionLimitsConstraint:
  """Class used to impose limits to the configurations of a kinematic chain.

  The JointPositionLimitsConstraint has two required arguments: lower_limits and
  upper_limits. They represent the lower and upper joint limits of the kinematic
  chain. If defined, the algorithm will find an IK solution within those limits
  and return an error if this is not possible. The motion planning algorithm
  will return an error if a joint position limits constraint is defined that
  exceeds the system limits of the robot.

  Attributes:
    lower_limits: [float] storing the lower joint position limits.
    upper_limits: [float] storing the upper joint position limits.
    proto: Represents the JointPositionLimitsConstraint as a
      constrained_ik_pb2.JointPositionLimitsConstraint proto.
  """

  def __init__(self, lower_limits: List[float], upper_limits: List[float]):
    self.lower_limits: List[float] = lower_limits
    self.upper_limits: List[float] = upper_limits

  @property
  def proto(self) -> constrained_ik_pb2.JointPositionLimitsConstraint:
    """Returns a proto constructed from JointPositionLimitsConstraint object.

    Returns:
      Constructed constrained_ik_pb2.JointPositionLimitsConstraint proto.
    """
    return constrained_ik_pb2.JointPositionLimitsConstraint(
        lower_limits=joint_space_pb2.JointVec(joints=self.lower_limits),
        upper_limits=joint_space_pb2.JointVec(joints=self.upper_limits),
    )

  @classmethod
  def from_proto(
      cls, constraint_proto: constrained_ik_pb2.JointPositionLimitsConstraint
  ) -> "JointPositionLimitsConstraint":
    """Constructs a JointPositionLimitsConstraint class from a proto representation.

    Args:
      constraint_proto: proto to be converted.

    Returns:
      JointPositionLimitsConstraint from a proto representation.
    """
    lower_limits = []
    for value in constraint_proto.lower_limits.joints:
      lower_limits.append(value)
    upper_limits = []
    for value in constraint_proto.upper_limits.joints:
      upper_limits.append(value)
    return cls(lower_limits=lower_limits, upper_limits=upper_limits)


class Constraint:
  """Class of all constraints for motion targets.

  Attributes:
    constraint_name: The name of the constraint in the world
    target_constraint: The point and/or orientation constraint that specifies
      the Cartesian motion target.
    proto: The proto of the constraint.
  """

  def __init__(
      self,
      constraint_name: str,
      target_constraint: Union[
          PointConstraint,
          PoseConstraint,
          PoseWithFreeAxisConstraint,
          PoseConeConstraint,
          PositionEllipsoidConstraint,
          PositionPlaneConstraint,
          JointPositionLimitsConstraint,
      ],
  ):
    """Construct a Cartesian motion target as general constraint.

    Args:
      constraint_name: The name of the constraint.
      target_constraint: The point and/or orientation constraint that specifies
        the Cartesian motion target.
    """
    self.constraint_name: str = constraint_name
    self.target_constraint: Union[
        PointConstraint,
        PoseConstraint,
        PoseWithFreeAxisConstraint,
        PoseConeConstraint,
        PositionEllipsoidConstraint,
        PositionPlaneConstraint,
        JointPositionLimitsConstraint,
    ] = target_constraint

  @property
  def proto(self) -> motion_target_pb2.Constraint:
    """Returns a proto constructed from a ConstraintType object.

    Returns:
      Constructed motion_target_pb2.Constraint proto.
    """
    constraint_proto = motion_target_pb2.Constraint(name=self.constraint_name)
    if isinstance(self.target_constraint, PointConstraint):
      constraint_proto.point_constraint.CopyFrom(self.target_constraint.proto)
      return constraint_proto
    elif isinstance(self.target_constraint, PoseConstraint):
      constraint_proto.pose_constraint.CopyFrom(self.target_constraint.proto)
      return constraint_proto
    elif isinstance(self.target_constraint, PositionEllipsoidConstraint):
      constraint_proto.position_ellipsoid_constraint.CopyFrom(
          self.target_constraint.proto
      )
      return constraint_proto
    elif isinstance(self.target_constraint, PositionPlaneConstraint):
      constraint_proto.plane_constraint.CopyFrom(self.target_constraint.proto)
      return constraint_proto
    elif isinstance(self.target_constraint, PoseWithFreeAxisConstraint):
      constraint_proto.orientation_free_axis_constraint.CopyFrom(
          self.target_constraint.proto
      )
      return constraint_proto
    elif isinstance(self.target_constraint, PoseConeConstraint):
      constraint_proto.orientation_cone_constraint.CopyFrom(
          self.target_constraint.proto
      )
      return constraint_proto
    elif isinstance(self.target_constraint, JointPositionLimitsConstraint):
      constraint_proto.joint_position_limits_constraint.CopyFrom(
          self.target_constraint.proto
      )
      return constraint_proto
    raise TypeError(
        f"{self.target_constraint} cannot be used to construct a "
        "motion_target_pb2.Constraint"
    )

  @classmethod
  def from_proto(cls, target: motion_target_pb2.Constraint) -> "Constraint":
    """Constructs a Constraint flass from a proto representation.

    Args:
      target: proto to be converted.

    Returns:
      Constraint form a proto representation.
    """
    constraint_type = target.WhichOneof("constraint")
    if constraint_type == "point_constraint":
      point_constraint = PointConstraint.from_proto(target.point_constraint)
      return cls(target.name, point_constraint)
    elif constraint_type == "pose_constraint":
      pose_constraint = PoseConstraint.from_proto(target.pose_constraint)
      return cls(target.name, pose_constraint)
    elif constraint_type == "plane_constraint":
      plane_constraint = PositionPlaneConstraint.from_proto(
          target.plane_constraint
      )
      return cls(target.name, plane_constraint)
    elif constraint_type == "position_ellipsoid_constraint":
      ellipsoid_constraint = PositionEllipsoidConstraint.from_proto(
          target.position_ellipsoid_constraint
      )
      return cls(target.name, ellipsoid_constraint)
    elif constraint_type == "orientation_free_axis_constraint":
      free_axis_constraint = PoseWithFreeAxisConstraint.from_proto(
          target.orientation_free_axis_constraint
      )
      return cls(target.name, free_axis_constraint)
    elif constraint_type == "orientation_cone_constraint":
      cone_constraint = PoseConeConstraint.from_proto(
          target.orientation_cone_constraint
      )
      return cls(target.name, cone_constraint)
    elif constraint_type == "joint_position_limits_constraint":
      joint_position_limits_constraint = (
          JointPositionLimitsConstraint.from_proto(
              target.joint_position_limits_constraint
          )
      )
      return cls(target.name, joint_position_limits_constraint)
    raise ValueError(
        f"{constraint_type} cannot be converted to a Constraint type "
    )


class ConstrainedMotionTarget:
  """Represent a cartesian motion target as a constraint.

  The Constrained motion target consists of a list of constraints that define
  the Cartesian position/pose of one or multiple frames of the robot. It is
  possible to either constraint only the position of one frame of the robot or
  to set a set of constraints that can effect different frames of the robot. In
  addition, it is also possible to limit the joint position limits of the robot
  with respect to resulting joint configuration that fulfills the specified
  constraints. However, these modified limits will not take effect on the motion
  generated to get to this solution.

  Example 1: Specify a 3d pose constraint that aligns the gripper frame with
    awesome_frame, but that allows to keep the rotation around the z-axis of the
    target frame free. In addition, this example also specifies alternative
    joint position limits for the allowed joint configuration.
    target_1 = ConstrainedMotionTarget([
      Constraint("free_axis constraint",
        PoseFreeAxisConstraint(tool=gripper, frame=awesome_frame,
        free_axis_in_frame=[0,0,1])),
      Constraint("joint position limits constraint",
        JointPositionLimitsConstraint(lower_limit=[-1,-0.5,-1,-1,-1,-2],
        upper_limit=[1,2,1,3,3,1]))])

  Example 2: Specify a position constraint that allows to move the gripper frame
    by 3 cm into its z-direction. Allow arbitrary rotation changes.
    targe_2 = ConstrainedMotionTarget([Constraint("point_constraint",
      PointConstraint(tool=gripper, frame=gripper, p_offset_in_frame=[0,0,0.03])
      )])

  Attributes:
    constraints: constraint that defines the position/pose and joint limits.
    proto: Represents the ConstrainedMotionTarget as
      motion_target_pb2.ConstrainedMotionTarget proto.
  """

  def __init__(self, constraints: List[Constraint]):
    """Constructs a constrained motion target.

    Args:
      constraints: List of cartesian motion target constraints.
    """
    self.constraints: List[Constraint] = constraints

  @property
  def proto(self) -> motion_target_pb2.ConstrainedMotionTarget:
    """Returns a proto constructed from ConstrainedMotionTarget object.

    Returns:
      Constructed motion_target_pb2.ConstrainedMotionTarget proto.
    """
    motion_target_proto = motion_target_pb2.ConstrainedMotionTarget()
    for constraint in self.constraints:
      motion_target_proto.constraints.append(constraint.proto)
    return motion_target_proto

  @classmethod
  def from_proto(
      cls, target_proto: motion_target_pb2.ConstrainedMotionTarget
  ) -> "ConstrainedMotionTarget":
    """Constructs a ConstrainedMotionTarget class from a proto representation.

    Args:
       target_proto: proto to be converted.

    Returns:
      ConstrainedMotionTarget from a proto representation.
    """
    constraints = []
    for constraint in target_proto.constraints:
      constraints.append(Constraint.from_proto(constraint))
    return cls(constraints=constraints)
