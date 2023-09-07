# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides state variable path builder functions for all parts.

This module provides state variable path builder functions to conveniently
create the state variable path string for all available part status or safety
fields that can be used in an ICON reaction.
"""
import enum
from typing import List, Optional, Tuple

_STATE_VARIABLE_PATH_PREFIX = "@"
_STATE_VARIABLE_PATH_SEPARATOR = "."

_ARM_TYPE_NODE_NAME = "ArmPart"
_FT_TYPE_NODE_NAME = "ForceTorqueSensorPart"
_ADIO_TYPE_NODE_NAME = "ADIOPart"
_GRIPPER_TYPE_NODE_NAME = "GripperPart"
_RANGEFINDER_TYPE_NODE_NAME = "RangefinderPart"

_SAFETY_TYPE_NODE_NAME = "Safety"


# Arm part related nodes.
_SENSED_POSITION_NODE_NAME = "sensed_position"
_SENSED_VELOCITY_NODE_NAME = "sensed_velocity"
_SENSED_ACCELERATION_NODE_NAME = "sensed_acceleration"
_SENSED_TORQUE_NODE_NAME = "sensed_torque"
_BASE_TWIST_TIP_SENSED_NODE_NAME = "base_twist_tip_sensed"
_BASE_LINEAR_VELOCITY_TIP_SENSED_NODE_NAME = "base_linear_velocity_tip_sensed"
_BASE_ANGULAR_VELOCITY_TIP_SENSED_NODE_NAME = "base_angular_velocity_tip_sensed"
_CURRENT_CONTROL_MODE_NODE_NAME = "current_control_mode"

# Force torque sensor part related nodes.
_WRENCH_NODE_NAME = "wrench_at_tip"
_FORCE_MAGNITUDE_NODE_NAME = "force_magnitude_at_tip"
_TORQUE_MAGNITUDE_NODE_NAME = "torque_magnitude_at_tip"

# Simple gripper part related nodes.
_GRIPPER_STATUS_NODE_NAME = "sensed_state"
_GRIPPER_OPENING_WIDTH_NODE_NAME = "opening_width"

# ADIO part related nodes.
_DIGITAL_INPUT_NODE_NAME = "di"
_DIGITAL_OUTPUT_NODE_NAME = "do"
_ANALOG_INPUT_NODE_NAME = "ai"

# Rangefinder part related nodes.
_RANGEFINDER_DISTANCE_NODE_NAME = "distance"

# Safety part related nodes.
_ENABLE_BUTTON_STATUS_NODE_NAME = "enable_button_status"


class _StateVariablePathBuilder:
  """Helps building state variable paths by adding nodes that construct in the end the complete path.

  A state variable path is used to address fields in the robot part status such
  as
  joint positions or force values.
  The order of adding nodes is the order of nodes in the path.
  An example path looks as follows: `@arm.L1ArmPart.sensed_position[0]`
  """

  def __init__(self):
    self._nodes: list[Tuple[str, Optional[int]]] = []

  def add_node_with_index(
      self, node_name: str, index: int
  ) -> "_StateVariablePathBuilder":
    """Adds a single node with the given `node_name` and an array index to the path.

    Args:
      node_name: Name of the node.
      index: Index in the array to address.

    Returns:
      Itself for convenient path building using a fluent interface.
    """
    self._nodes.append((node_name, index))
    return self

  def add_nodes(self, node_names: List[str]) -> "_StateVariablePathBuilder":
    """Adds multiple nodes with the given `node_names` to the path.

    Args:
      node_names: List of node names.

    Returns:
      Itself for convenient path building using a fluent interface.
    """
    for node_name in node_names:
      self._nodes.append((node_name, None))
    return self

  def build(self) -> str:
    """Builds the final state variable path string based on the previous add-calls.

    Returns:
      The final state variable path in the format:
      {_STATE_VARIABLE_PATH_PREFIX}<first_node>{_STATE_VARIABLE_PATH_SEPARATOR}<...more
      nodes>{_STATE_VARIABLE_PATH_SEPARATOR}<last_node>.

      A single node consists of the node name and an optional array index: e.g.
      my_field[123]
    """
    if not self._nodes:
      raise ValueError("No path nodes were added. Cannot build a path!")

    node_strings = []
    for node_name, node_index in self._nodes:
      node_string = node_name
      if node_index is not None:
        node_string += "[%d]" % node_index
      node_strings.append(node_string)
    return _STATE_VARIABLE_PATH_PREFIX + str(
        _STATE_VARIABLE_PATH_SEPARATOR
    ).join(node_strings)


class StateVariablePath:
  """Groups all state variable path generator functions."""

  class Arm:
    """Groups all state variable path generator functions for the arm part."""

    @classmethod
    def sensed_position(
        cls,
        part_name: str,
        joint_index: int,
    ) -> str:
      """Generates a state variable path for a single sensed joint position.

      Field type: double

      Args:
        part_name: Name of the arm part.
        joint_index: Joint to address.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ARM_TYPE_NODE_NAME])
          .add_node_with_index(_SENSED_POSITION_NODE_NAME, joint_index)
          .build()
      )

    @classmethod
    def sensed_velocity(
        cls,
        part_name: str,
        joint_index: int,
    ) -> str:
      """Generates a state variable path for a single sensed joint velocity.

      Field type: double

      Args:
        part_name: Name of the arm part.
        joint_index: Joint to address.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ARM_TYPE_NODE_NAME])
          .add_node_with_index(_SENSED_VELOCITY_NODE_NAME, joint_index)
          .build()
      )

    @classmethod
    def sensed_acceleration(
        cls,
        part_name: str,
        joint_index: int,
    ) -> str:
      """Generates a state variable path for a single sensed joint acceleration.

      Field type: double

      Args:
        part_name: Name of the arm part.
        joint_index: Joint to address.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ARM_TYPE_NODE_NAME])
          .add_node_with_index(_SENSED_ACCELERATION_NODE_NAME, joint_index)
          .build()
      )

    @classmethod
    def sensed_torque(
        cls,
        part_name: str,
        joint_index: int,
    ) -> str:
      """Generates a state variable path for a single sensed joint torque.

      Field type: double

      Args:
        part_name: Name of the arm part.
        joint_index: Joint to address.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ARM_TYPE_NODE_NAME])
          .add_node_with_index(_SENSED_TORQUE_NODE_NAME, joint_index)
          .build()
      )

    class TwistDimension(enum.Enum):
      """Helper enum to map a twist dimension onto an array index.

      X,Y,Z map to the linear velocity and RX, RY, RZ map to the angular
      velocities of the twist.
      """

      X = 0
      Y = 1
      Z = 2
      RX = 3
      RY = 4
      RZ = 5

    @classmethod
    def base_twist_tip_sensed(
        cls,
        part_name: str,
        twist_dimension: TwistDimension,
    ) -> str:
      """Generates a state variable path for a single sensed twist entry.

      The twist is calculated for the tip in the robot's base frame based on the
      sensed joint velocities.

      Field type: double

      Args:
        part_name: Name of the arm part.
        twist_dimension: Twist dimension to specify the value of the twist array
          to address.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ARM_TYPE_NODE_NAME])
          .add_node_with_index(
              _BASE_TWIST_TIP_SENSED_NODE_NAME, twist_dimension.value
          )
          .build()
      )

    @classmethod
    def base_linear_velocity_tip_sensed(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the Cartesian linear (translational) velocity magnitude (Euclidean or l^2-Norm) of the arm tip.

      Field type: double

      Args:
        part_name: Name of the arm part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([
              part_name,
              _ARM_TYPE_NODE_NAME,
              _BASE_LINEAR_VELOCITY_TIP_SENSED_NODE_NAME,
          ])
          .build()
      )

    @classmethod
    def base_angular_velocity_tip_sensed(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the Cartesian angular (rotational) velocity magnitude (Euclidean or l^2-Norm) of the arm tip.

      Field type: double

      Args:
        part_name: Name of the arm part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([
              part_name,
              _ARM_TYPE_NODE_NAME,
              _BASE_ANGULAR_VELOCITY_TIP_SENSED_NODE_NAME,
          ])
          .build()
      )

    @classmethod
    def current_control_mode(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the currently used control mode.

      The value corresponds to the values of the enum
         :intrinsic.icon.proto.part_status_pb2.PartControlMode.

      Field type: int64

      Args:
        part_name: Name of the arm part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _ARM_TYPE_NODE_NAME, _CURRENT_CONTROL_MODE_NODE_NAME]
          )
          .build()
      )

  class ForceTorque:
    """Groups all state variable path generator functions for the force-torque sensor part."""

    class WrenchDimension(enum.Enum):
      """Helper enum to map a wrench dimension onto an array index.

      X,Y,Z map to the forces and RX, RY, RZ map to the torques of the wrench.
      """

      X = 0
      Y = 1
      Z = 2
      RX = 3
      RY = 4
      RZ = 5

    @classmethod
    def wrench_at_tip(
        cls,
        part_name: str,
        wrench_dimension: WrenchDimension,
    ) -> str:
      """Generates a state variable path for a single wrench value sensed at the force torque sensor in the frame of the arm tip.

      Field type: double

      Args:
        part_name: Name of the force torque sensor part.
        wrench_dimension: Wrench dimension to specify the value of the twist
          array to address.

      Returns:
        Generated state variable path string.
      """

      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _FT_TYPE_NODE_NAME])
          .add_node_with_index(_WRENCH_NODE_NAME, wrench_dimension.value)
          .build()
      )

    @classmethod
    def force_magnitude_at_tip(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the magnitude (Euclidean or l^2-Norm) of the **force** sensed at the force torque sensor in the frame of the arm tip.

      Field type: double

      Args:
        part_name: Name of the force torque sensor part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _FT_TYPE_NODE_NAME, _FORCE_MAGNITUDE_NODE_NAME]
          )
          .build()
      )

    @classmethod
    def torque_magnitude_at_tip(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the magnitude (Euclidean or l^2-Norm) of the **torque** sensed at the force torque sensor in the frame of the arm tip.

      Field type: double

      Args:
        part_name: Name of the force torque sensor part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _FT_TYPE_NODE_NAME, _TORQUE_MAGNITUDE_NODE_NAME]
          )
          .build()
      )

  class Gripper:
    """Groups all state variable path generator functions for the gripper part."""

    @classmethod
    def status(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the opening status of the gripper.

      The enum values in this field are reported as integer values but
      correspond to the proto enum
      intrinsic.icon.proto.part_status_pb2.GripperState.SensedState.

      Field type: int

      Args:
        part_name: Name of the gripper part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _GRIPPER_TYPE_NODE_NAME, _GRIPPER_STATUS_NODE_NAME]
          )
          .build()
      )

    @classmethod
    def opening_width(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the opening width of the gripper.

      Field type: double

      Args:
        part_name: Name of the gripper part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([
              part_name,
              _GRIPPER_TYPE_NODE_NAME,
              _GRIPPER_OPENING_WIDTH_NODE_NAME,
          ])
          .build()
      )

  class ADIO:
    """Groups all state variable path generator functions for the ADIO (Analog and Digital Inputs and Outputs) part."""

    @classmethod
    def digital_input(
        cls,
        part_name: str,
        block_name: str,
        signal_index: int,
    ) -> str:
      """Generates a state variable path for the status of a digital input of the signal at `signal_index` in block `block_name`.

      Field type: bool

      Args:
        part_name: Name of the adio part.
        block_name: Name of the signal block.
        signal_index: Index in the block.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _ADIO_TYPE_NODE_NAME, _DIGITAL_INPUT_NODE_NAME]
          )
          .add_node_with_index(block_name, signal_index)
          .build()
      )

    @classmethod
    def digital_output(
        cls,
        part_name: str,
        block_name: str,
        signal_index: int,
    ) -> str:
      """Generates a state variable path for the status of a digital output of the signal at `signal_index` in block `block_name`.

      Field type: bool

      Args:
        part_name: Name of the adio part.
        block_name: Name of the signal block.
        signal_index: Index in the block.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes(
              [part_name, _ADIO_TYPE_NODE_NAME, _DIGITAL_OUTPUT_NODE_NAME]
          )
          .add_node_with_index(block_name, signal_index)
          .build()
      )

    @classmethod
    def analog_input(
        cls,
        part_name: str,
        block_name: str,
        signal_index: int,
    ) -> str:
      """Generates a state variable path for the status of an analog input of the signal at `signal_index` in block `block_name`.

      Field type: double

      Args:
        part_name: Name of the adio part.
        block_name: Name of the signal block.
        signal_index: Index in the block.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([part_name, _ADIO_TYPE_NODE_NAME, _ANALOG_INPUT_NODE_NAME])
          .add_node_with_index(block_name, signal_index)
          .build()
      )

  class RangeFinder:
    """Groups all state variable path generator functions for the rangefinder part."""

    @classmethod
    def distance(
        cls,
        part_name: str,
    ) -> str:
      """Generates a state variable path for the sensed distance of the rangefinder.

      Field type: double

      Args:
        part_name: Name of the rangefinder part.

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([
              part_name,
              _RANGEFINDER_TYPE_NODE_NAME,
              _RANGEFINDER_DISTANCE_NODE_NAME,
          ])
          .build()
      )

  class Safety:
    """Groups all state variable path generator functions for the safety signals."""

    @classmethod
    def enable_button_status(cls) -> str:
      """Generates a state variable path for the state of the enable safety button.

      The enum values in this field are reported as integer values but
      correspond to the proto enum
      intrinsic.icon.proto.safety_status_pb2.ButtonStatus.

      Field type: int

      Returns:
        Generated state variable path string.
      """
      return (
          _StateVariablePathBuilder()
          .add_nodes([
              _SAFETY_TYPE_NODE_NAME,
              _ENABLE_BUTTON_STATUS_NODE_NAME,
          ])
          .build()
      )
