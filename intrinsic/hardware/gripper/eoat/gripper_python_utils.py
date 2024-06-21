# Copyright 2023 Intrinsic Innovation LLC

"""Utility libraries for controlling the grippers.

Currently only provides utilities for `SuctionGripper` and `PinchGripper`
including methods `grasp/release/gripping_indicated`.
"""

from __future__ import annotations

import abc
import logging

from intrinsic.hardware.gripper.eoat import gripper_client
from intrinsic.hardware.gripper.service.proto import generic_gripper_pb2
from intrinsic.resources.proto import resource_handle_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_resources
import numpy as np


class Gripper(metaclass=abc.ABCMeta):
  """Gripper interface that communicates with grippers.

  Grippers start off in a non-faulted state. If a fault is encountered, they
  switch into a faulted state.  The `clear_faults` method takes them back from
  faulted to nonfaulted.
  """

  def clear_faults(self) -> bool:
    """Clears faults on the gripper (and re-enables it).

    Returns:
      Whether clear faults was successful.
    """

  @abc.abstractmethod
  def grasp(self) -> None:
    """Activates the gripper for grasping.

    On a suction gripper, this means turning on suction; on a finger gripper,
    this means closing the fingers.

    Returns:
      Whether the activation completed successfully.
    """

  @abc.abstractmethod
  def release(self) -> None:
    """Activates the gripper for releasing.

    On a suction gripper, this means turning off suction; on a finger gripper,
    this means opening the fingers.

    Returns:
      Whether the release completed successfully.
    """

  @abc.abstractmethod
  def gripping_indicated(self) -> bool:
    """Checks if the gripper is gripping something.

    On a suction gripper, this means suction pressure exceeds a preset
    threshold, which indicates an object is present. On a finger gripper,
    this means after attempting to close the fingers, the distance between
    fingers exceeds a preset threshold, which indicates the same.

    Returns:
      Whether the gripper is gripping something.
    """

  @property
  @abc.abstractmethod
  def type(self) -> gripper_client.GripperTypes:
    """Returns the type of the gripper."""

  @property
  @abc.abstractmethod
  def name(self) -> str:
    """Returns name of the gripper."""

  @abc.abstractmethod
  def command(
      self, command: generic_gripper_pb2.CommandRequest
  ) -> generic_gripper_pb2.CommandResponse | None:
    """Commands the gripper.

    On an adaptive pinch gripper, controls the gripper with one or more of the
    following commands:
     * move to a specific position in SI unit (not the same as joint position).
      E.g., both finger moves to 0.01 m from its fully open position.
     * move with a specific velocity
     * move with a specific force
    Suction gripper or pinch gripper do not support this method.

    Args:
      command: The command to send to the gripper.

    Returns:
      The response from the gripper. Or None if the gripper is simulated.
    """


class SuctionGripper(Gripper):
  """Allows a user to interact with a suction gripper."""

  def __init__(
      self,
      gripper_handle: resource_handle_pb2.ResourceHandle,
      is_simulated: bool = False,
  ):
    """Constructor.

    Args:
      gripper_handle: The resource handle of the gripper.
      is_simulated: Whether the gripper is simulated.
    """
    self._is_simulated = is_simulated
    self._name = gripper_handle.name

    # Simulated gripper.
    if is_simulated:
      self._client = None
      logging.info("Simulating a SuctionGripper.")
      return

    # Gripper client.
    self._client = gripper_client.GripperClient.connect_with_gripper_handle(
        gripper_handle=gripper_handle,
        gripper_type=gripper_client.GripperTypes.SUCTION,
    )

  def clear_faults(self) -> bool:
    """Clears faults on the gripper (and re-enables it).

    Returns:
      Whether clear faults was successful.
    """
    raise NotImplementedError(
        "`clear_faults` is not yet implemented for `SuctionGripper`."
    )

  def grasp(self) -> None:
    """Turns on suction for grasping.

    This has no effect in simulation.
    """
    if self._client:
      self._client.grasp()

  def release(self) -> None:
    """Turns off suction for releasing.

    This has no effect in simulation.
    """
    if self._client:
      self._client.release()

  def blow_off(self) -> None:
    """Blows off air.

    This has no effect in simulation.
    """
    if self._client:
      self._client.blow_off()

  def gripping_indicated(self) -> bool:
    """Checks if the gripper is gripping something.

    On a suction gripper, this means suction pressure exceeds a preset
    threshold, which indicates an object is present. If the gripper is
    simulated, this returns True.

    Returns:
      On a real gripper, return if the gripper is gripping something. On a
      simulated gripper, always return True.
    """
    if self._client:
      return self._client.gripping_indicated()
    else:
      # The gripper is simulated.
      return True

  @property
  def type(self) -> gripper_client.GripperTypes:
    """Returns the type of the gripper."""
    return gripper_client.GripperTypes.SUCTION

  @property
  def name(self) -> str:
    """Returns name of the gripper."""
    return self._name

  def command(
      self, command: generic_gripper_pb2.CommandRequest
  ) -> generic_gripper_pb2.CommandResponse | None:
    raise NotImplementedError(
        "`command` is not supported for `SuctionGripper`."
    )


class PinchGripper(Gripper):
  """Allows a user to interact with a (non-adaptive) pinch gripper.

  This interacts with the world service to update the gripper's joint
  position in the world to reflect its position change. Since the pinch
  gripper service doesn't provide position feedback, the joint position in the
  world is an estimated position instead of the actual position. More
  specifically, the gripper is set to fully closed position for `grasp` and
  set to fully open position for `release`.
  """

  def __init__(
      self,
      gripper_handle: resource_handle_pb2.ResourceHandle,
      world: object_world_client.ObjectWorldClient,
      is_simulated: bool = False,
  ):
    """Constructor.

    Args:
      gripper_handle: The resource handle of the gripper.
      world: The object world. Used for updating gripper joint positions.
      is_simulated: Whether the gripper is simulated.
    """
    self._is_simulated = is_simulated
    self._world = world
    self._name = gripper_handle.name

    # Gripper object in the object world.
    self._gripper_object = world.get_kinematic_object(gripper_handle)

    # Simulated gripper.
    if is_simulated:
      self._client = None
      logging.info("Simulating a PinchGripper.")
      return

    # Gripper client.
    self._client = gripper_client.GripperClient.connect_with_gripper_handle(
        gripper_handle=gripper_handle,
        gripper_type=gripper_client.GripperTypes.PINCH,
    )

  def clear_faults(self) -> bool:
    """Clears faults on the gripper (and re-enables it).

    Returns:
      Whether clear faults was successful.
    """
    raise NotImplementedError(
        "`clear_faults` is not yet implemented for `PinchGripper`."
    )

  def grasp(self) -> None:
    """Closes the gripper until either fully closed or until the object is grasped, and updates the world accordingly."""
    if self._client:
      self._client.grasp()

    # Update gripper joint positions in object world.
    _update_pinch_gripper_joint_positions(
        self._world, "grasp", self._gripper_object
    )

  def release(self) -> None:
    """Fully opens the gripper, and updates the world accordingly."""
    if self._client:
      self._client.release()

    # Update gripper joint positions in object world.
    _update_pinch_gripper_joint_positions(
        self._world, "release", self._gripper_object
    )

  def gripping_indicated(self) -> bool:
    """Checks if the gripper is gripping something.

    On a pinch gripper, this means the "part present" signal is True.
    If the gripper is simulated, this returns True.

    Returns:
      On a real gripper, return if the gripper is gripping something. On a
      simulated gripper, always return True.
    """
    if self._client:
      return self._client.gripping_indicated()
    else:
      # The gripper is simulated.
      return True

  @property
  def type(self) -> gripper_client.GripperTypes:
    """Returns the type of the gripper."""
    return gripper_client.GripperTypes.PINCH

  @property
  def name(self) -> str:
    """Returns name of the gripper."""
    return self._name

  def command(
      self, command: generic_gripper_pb2.CommandRequest
  ) -> generic_gripper_pb2.CommandResponse | None:
    raise NotImplementedError("`command` is not supported for `PinchGripper`.")


class AdaptivePinchGripper(Gripper):
  """Allows a user to interact with an adaptive pinch gripper.

  This interacts with the world service to update the gripper's joint
  position in the world to reflect its position change. For grasp and release,
  since the gripper service doesn't provide position feedback, the joint
  position in the world is an estimated position instead of the actual position.
  More specifically, the gripper is set to fully closed position for `grasp` and
  set to fully open position for `release`. For `command`, the gripper service
  provides position feedback, so the joint position in the world is updated
  accordingly.
  """

  # The multiply factor to convert from a closure position (in SI units) to
  # gripper joint position. e.g. joint_position = factor * closure_position
  closure_position_to_joint_position_factor = 0.5

  def __init__(
      self,
      gripper_handle: resource_handle_pb2.ResourceHandle,
      world: object_world_client.ObjectWorldClient,
      is_simulated: bool = False,
  ):
    """Constructor.

    Args:
      gripper_handle: The resource handle of the gripper.
      world: The object world. Used for updating gripper joint positions.
      is_simulated: Whether the gripper is simulated.
    """
    self._is_simulated = is_simulated
    self._world = world
    self._name = gripper_handle.name

    # Gripper object in the object world.
    self._gripper_object = world.get_kinematic_object(gripper_handle)

    # Simulated gripper.
    if is_simulated:
      self._client = None
      logging.info("Simulating an AdaptivePinchGripper.")
      return

    # Gripper client.
    self._client = gripper_client.GripperClient.connect_with_gripper_handle(
        gripper_handle=gripper_handle,
        gripper_type=gripper_client.GripperTypes.ADAPTIVE_PINCH,
    )

  def clear_faults(self) -> bool:
    """Clears faults on the gripper (and re-enables it).

    Returns:
      Whether clear faults was successful.
    """
    raise NotImplementedError(
        "`clear_faults` is not yet implemented for `AdaptivePinchGripper`."
    )

  def grasp(self) -> None:
    """Closes the gripper until either fully closed or until the object is grasped, and updates the world accordingly."""
    if self._client:
      self._client.grasp()

    # Update gripper joint positions in object world.
    # Adaptive pinch gripper is fully closed at its maximum position.
    self._world.update_joint_positions(
        self._gripper_object,
        joint_positions=self._gripper_object.joint_application_limits.max_position.values,
    )

  def release(self) -> None:
    """Fully opens the gripper, and updates the world accordingly."""
    if self._client:
      self._client.release()

    # Update gripper joint positions in object world.
    # Adaptive pinch gripper is fully open at its minimum position.
    self._world.update_joint_positions(
        self._gripper_object,
        joint_positions=self._gripper_object.joint_application_limits.min_position.values,
    )

  def gripping_indicated(self) -> bool:
    """Checks if the gripper is gripping something.

    On a pinch gripper, this means the "part present" signal is True.
    If the gripper is simulated, this returns True.

    Returns:
      On a real gripper, return if the gripper is gripping something. On a
      simulated gripper, always return True.
    """
    if self._client:
      return self._client.gripping_indicated()
    else:
      # The gripper is simulated.
      return True

  def command(
      self, command: generic_gripper_pb2.CommandRequest
  ) -> generic_gripper_pb2.CommandResponse | None:
    """Commands the gripper.

    On an adaptive pinch gripper, controls the gripper with one or more of the
    following commands:
     * move to a specific position in SI unit (not the same as joint position).
      E.g., both finger moves to 0.01 m from its fully open position.
     * move with a specific velocity
     * move with a specific force

    Args:
      command: The command to send to the gripper.

    Returns:
      The response from the gripper. Or None if the gripper is simulated.
    """
    # Gripper final joint positions are either from the response or from the
    # command.
    gripper_closure_position = None
    gripper_joint_position = None
    response = None
    joint_limit_lower = np.array(
        self._gripper_object.joint_application_limits.min_position.values
    )
    joint_limit_upper = np.array(
        self._gripper_object.joint_application_limits.max_position.values
    )

    if self._client:
      response = self._client.command(command)
      gripper_closure_position = response.position
    else:
      if command.HasField("position"):
        gripper_closure_position = command.position
      if command.HasField("position_percentage"):
        gripper_joint_position = (
            command.position_percentage
            / 100.0
            * (joint_limit_upper - joint_limit_lower)
        )

    if gripper_closure_position is not None:
      # Update gripper positions in the world. Note: finger DOFs are independent
      # and moving in direction opposite to measured gripper position.
      gripper_joint_position = (
          joint_limit_upper
          - self.closure_position_to_joint_position_factor
          * gripper_closure_position
      )
      gripper_joint_position = np.clip(
          gripper_joint_position, joint_limit_lower, joint_limit_upper
      )

    if gripper_joint_position is not None:
      self._world.update_joint_positions(
          self._gripper_object,
          joint_positions=list(gripper_joint_position),
      )
    return response

  @property
  def type(self) -> gripper_client.GripperTypes:
    """Returns the type of the gripper."""
    return gripper_client.GripperTypes.ADAPTIVE_PINCH

  @property
  def name(self) -> str:
    """Returns name of the gripper."""
    return self._name


def _update_pinch_gripper_joint_positions(
    world: object_world_client.ObjectWorldClient,
    command: str,
    gripper_object: object_world_resources.KinematicObject,
):
  """Updates the gripper joint positions in the object world."""
  if command == "grasp":
    gripper_joint_positions = (
        gripper_object.joint_application_limits.min_position.values
    )
  elif command == "release":
    gripper_joint_positions = (
        gripper_object.joint_application_limits.max_position.values
    )
  else:
    raise ValueError(f"Pinch gripper command is not supported: {command}!")

  world.update_joint_positions(
      gripper_object,
      joint_positions=gripper_joint_positions,
  )
