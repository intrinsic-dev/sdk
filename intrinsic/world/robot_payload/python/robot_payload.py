# Copyright 2023 Intrinsic Innovation LLC

"""The RobotPayload class represents the payload of a kinematic object."""

import math
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion
from intrinsic.world.proto import robot_payload_pb2
import numpy as np

_INERTA_SHAPE = (3, 3)


class RobotPayload:
  """Payload of a kinematic object."""

  def __init__(self):
    # Mass of the robot payload. Unit is kg.
    self._mass: float = 0.0

    # Center of gravity of the robot payload relative to the robot flange/tip
    # frame.
    self._tip_t_cog: data_types.Pose3 = data_types.Pose3()

    # 3x3 symmetric inertia matrix of the robot payload expressed about the link
    # center of mass. Unit is kg*m^2.
    self._inertia: np.ndarray = np.zeros(_INERTA_SHAPE)

  @property
  def mass(self) -> float:
    """Mass of the robot payload. Unit is kg."""
    return self._mass

  @property
  def tip_t_cog(self) -> data_types.Pose3:
    """Center of gravity of the robot payload expressed in the flange frame."""
    return self._tip_t_cog

  @property
  def inertia(self) -> np.ndarray:
    """Inertia of the robot payload expressed about the link center of mass."""
    return self._inertia

  @classmethod
  def create(
      cls,
      mass: float,
      tip_t_cog: data_types.Pose3,
      inertia: np.ndarray,
  ) -> 'RobotPayload':
    """Creates a RobotPayload. Does not check if the payload is valid."""
    payload = RobotPayload()
    payload.set_mass(mass)
    payload.set_tip_t_cog(tip_t_cog)
    payload.set_inertia(inertia)
    return payload

  def set_mass(self, mass: float) -> None:
    """Sets the mass of the robot payload. Unit is kg."""
    self._mass = mass

  def set_tip_t_cog(self, tip_t_cog: data_types.Pose3) -> None:
    """Sets the center of gravity of the robot payload."""
    self._tip_t_cog = tip_t_cog

  def set_inertia(self, inertia: np.ndarray) -> None:
    """Sets the inertia of the robot payload."""
    if inertia.shape != _INERTA_SHAPE:
      raise ValueError(f'Inertia must be a 3x3 matrix, got {inertia.shape}.')
    self._inertia = inertia

  def __eq__(self, other: 'RobotPayload') -> bool:
    if not isinstance(other, RobotPayload):
      return NotImplemented
    return (
        math.isclose(self.mass, other.mass)
        and self.tip_t_cog.almost_equal(other.tip_t_cog)
        and np.allclose(self.inertia, other.inertia)
    )

  def __str__(self):
    return (
        f'RobotPayload(mass={self.mass}, tip_t_cog={self.tip_t_cog},'
        f' inertia={self.inertia})'
    )


def payload_from_proto(
    proto: robot_payload_pb2.RobotPayload,
) -> RobotPayload:
  mass = proto.mass_kg
  tip_t_cog = data_types.Pose3()
  if proto.HasField('tip_t_cog'):
    tip_t_cog = proto_conversion.pose_from_proto(proto.tip_t_cog)
  inertia = np.zeros((3, 3))
  if proto.HasField('inertia'):
    inertia = proto_conversion.ndarray_from_matrix_proto(proto.inertia)

  return RobotPayload.create(
      mass,
      tip_t_cog,
      inertia,
  )


def payload_to_proto(
    payload: RobotPayload,
) -> robot_payload_pb2.RobotPayload:
  return robot_payload_pb2.RobotPayload(
      mass_kg=payload.mass,
      tip_t_cog=proto_conversion.pose_to_proto(payload.tip_t_cog),
      inertia=proto_conversion.ndarray_to_matrix_proto(payload.inertia),
  )
