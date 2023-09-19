# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Camera misc helper methods."""
from __future__ import annotations

from typing import Optional, Tuple

from intrinsic.perception.proto import camera_config_pb2
from intrinsic.perception.proto import dimensions_pb2
from intrinsic.perception.proto import distortion_params_pb2
from intrinsic.perception.proto import intrinsic_params_pb2
import numpy as np


def extract_identifier(config: camera_config_pb2.CameraConfig) -> Optional[str]:
  """Extract the camera identifier from the camera config."""
  # extract device_id from oneof
  identifier = config.identifier
  camera_driver = identifier.WhichOneof("drivers")
  if camera_driver == "genicam":
    return identifier.genicam.device_id
  elif camera_driver == "openni":
    return identifier.openni.device_id
  elif camera_driver == "v4l":
    return str(identifier.v4l.device_id)
  elif camera_driver == "photoneo":
    return identifier.photoneo.device_id
  elif camera_driver == "realsense":
    return identifier.realsense.device_id
  elif camera_driver == "plenoptic_unit":
    return identifier.plenoptic_unit.device_id
  elif camera_driver == "fake_genicam":
    return "fake_genicam"
  else:
    return None


def extract_dimensions(
    dimensions: dimensions_pb2.Dimensions,
) -> Tuple[int, int]:
  """Extract dimensions into a tuple."""
  return (dimensions.cols, dimensions.rows)


def extract_intrinsic_dimensions(
    ip: intrinsic_params_pb2.IntrinsicParams,
) -> Tuple[int, int]:
  """Extract dimensions from intrinsic params into a tuple."""
  return extract_dimensions(ip.dimensions)


def extract_intrinsic_matrix(
    ip: intrinsic_params_pb2.IntrinsicParams,
) -> np.ndarray:
  """Extract intrinsic matrix from intrinsic params as a numpy array."""
  return np.array([
      [ip.focal_length_x, 0, ip.principal_point_x],
      [0, ip.focal_length_y, ip.principal_point_y],
      [0, 0, 1],
  ])


def extract_distortion_params(
    dp: distortion_params_pb2.DistortionParams,
) -> np.ndarray:
  """Extract distortion parameters from distortion params as a numpy array."""
  if dp.k4 or dp.k5 or dp.k6:
    return np.array([dp.k1, dp.k2, dp.p1, dp.p2, dp.k3, dp.k4, dp.k5, dp.k6])
  else:
    return np.array([dp.k1, dp.k2, dp.p1, dp.p2, dp.k3])
