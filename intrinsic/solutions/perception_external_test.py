# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for cameras."""

from unittest import mock
from absl.testing import absltest
from intrinsic.solutions import perception


class CamerasTest(absltest.TestCase):

  def test_camera_init_smoke(self):
    _ = perception.Camera(
        channel=mock.MagicMock(),
        handle=mock.MagicMock(),
        equipment_registry=mock.MagicMock(),
        executive=mock.MagicMock(),
        is_simulated=False,
    )

  def test_cameras_init_smoke(self):
    _ = perception.Cameras(
        equipment_registry=mock.MagicMock(),
        grpc_channel=mock.MagicMock(),
        executive=mock.MagicMock(),
        is_simulated=True,
    )


if __name__ == '__main__':
  absltest.main()
