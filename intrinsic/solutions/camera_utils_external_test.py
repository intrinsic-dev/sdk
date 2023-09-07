# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for camera_utils."""

from absl.testing import absltest
from intrinsic.perception.proto import frame_pb2
from intrinsic.perception.proto import image_buffer_pb2
from intrinsic.solutions import camera_utils
import numpy as np


def _make_random_rgbd_frame():
  np.random.seed(117)
  rgb8u = np.random.uniform(low=0, high=255, size=[3, 4, 3]).astype(np.uint8)
  depth32f = np.random.uniform(low=0.0, high=2.0, size=[2, 3, 1]).astype(
      np.float32
  )
  frame = frame_pb2.Frame()
  frame.acquisition_time.seconds = 123
  frame.camera_params.intrinsic_params.focal_length_x = 2.0
  (frame.rgb8u.dimensions.rows, frame.rgb8u.dimensions.cols) = rgb8u.shape[0:2]
  frame.rgb8u.pixel_type = image_buffer_pb2.PixelType.PIXEL_INTENSITY
  frame.rgb8u.num_channels = 3
  frame.rgb8u.data = rgb8u.tobytes()
  frame.rgb8u.type = image_buffer_pb2.TYPE_8U
  (frame.depth32f.dimensions.rows, frame.depth32f.dimensions.cols) = (
      depth32f.shape[0:2]
  )
  frame.depth32f.pixel_type = image_buffer_pb2.PixelType.PIXEL_DEPTH
  frame.depth32f.num_channels = 1
  frame.depth32f.data = depth32f.tobytes()
  frame.depth32f.type = image_buffer_pb2.TYPE_32F
  return frame


class CamerUtilsExternalTest(absltest.TestCase):

  def test_init_frame(self):
    _ = camera_utils.Frame(frame_pb2.Frame())

  def test_frame_to_proto(self):
    frame = _make_random_rgbd_frame()
    converted_frame = camera_utils.Frame(frame).proto()
    self.assertEqual(converted_frame, frame)


if __name__ == '__main__':
  absltest.main()
