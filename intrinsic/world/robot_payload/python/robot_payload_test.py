# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion
from intrinsic.solutions.testing import compare
from intrinsic.world.proto import robot_payload_pb2
from intrinsic.world.robot_payload.python import robot_payload
import numpy as np


class RobotPayloadTest(parameterized.TestCase):

  def test_create_payload_works(self):
    payload = robot_payload.RobotPayload.create(
        mass=1.2,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=2.0 * np.eye(3),
    )

    self.assertEqual(payload.mass, 1.2)
    self.assertEqual(
        payload.tip_t_cog,
        data_types.Pose3(translation=[1.0, 2.0, 3.0]),
    )
    np.testing.assert_array_equal(payload.inertia, 2.0 * np.eye(3))

  def test_create_empty_payload_works(self):
    payload = robot_payload.RobotPayload()

    self.assertEqual(payload.mass, 0.0)
    self.assertEqual(payload.tip_t_cog, data_types.Pose3())
    np.testing.assert_array_equal(payload.inertia, np.zeros((3, 3)))

  def test_set_mass_works(self):
    payload = robot_payload.RobotPayload()

    payload.set_mass(1.3)

    self.assertEqual(payload.mass, 1.3)

  def test_set_tip_t_cog_works(self):
    payload = robot_payload.RobotPayload()

    payload.set_tip_t_cog(data_types.Pose3(translation=[1.0, 2.0, 3.0]))

    np.testing.assert_array_equal(
        payload.tip_t_cog.translation, [1.0, 2.0, 3.0]
    )

  def test_set_inertia_works(self):
    payload = robot_payload.RobotPayload()

    payload.set_inertia(np.eye(3) * 2.0)

    np.testing.assert_array_equal(payload.inertia, np.eye(3) * 2.0)

  def test_set_wrong_size_inertia_raises_error(self):
    payload = robot_payload.RobotPayload()

    with self.assertRaisesRegex(
        ValueError, r'Inertia must be a 3x3 matrix, got \(2, 2\).'
    ):
      payload.set_inertia(np.eye(2))

  def test_from_proto_works(self):
    proto = robot_payload_pb2.RobotPayload(
        mass_kg=1.0,
        tip_t_cog=proto_conversion.pose_to_proto(
            data_types.Pose3(translation=[1.0, 2.0, 3.0])
        ),
        inertia=proto_conversion.ndarray_to_matrix_proto(np.eye(3) * 2.0),
    )

    payload = robot_payload.payload_from_proto(proto)

    self.assertEqual(payload.mass, 1.0)
    self.assertEqual(
        payload.tip_t_cog, data_types.Pose3(translation=[1.0, 2.0, 3.0])
    )
    np.testing.assert_array_equal(payload.inertia, np.eye(3) * 2.0)

  @parameterized.named_parameters(
      dict(
          testcase_name='wrong_size_inertia',
          proto=robot_payload_pb2.RobotPayload(
              mass_kg=1.0,
              tip_t_cog=proto_conversion.pose_to_proto(
                  data_types.Pose3(translation=[1.0, 2.0, 3.0])
              ),
              inertia=proto_conversion.ndarray_to_matrix_proto(np.eye(2) * 2.0),
          ),
          error=ValueError,
      ),
  )
  def test_from_proto_fails_for_invalid_proto(
      self, proto: robot_payload_pb2.RobotPayload, error: Exception
  ):
    with self.assertRaises(error):
      robot_payload.payload_from_proto(proto)

  def test_to_proto_works(self):
    payload = robot_payload.RobotPayload.create(
        mass=1.0,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=np.eye(3) * 2.0,
    )

    proto = robot_payload.payload_to_proto(payload)

    self.assertEqual(proto.mass_kg, 1.0)
    compare.assertProto2Equal(
        self,
        proto.tip_t_cog,
        proto_conversion.pose_to_proto(
            data_types.Pose3(translation=[1.0, 2.0, 3.0])
        ),
    )
    compare.assertProto2Equal(
        self,
        proto.inertia,
        proto_conversion.ndarray_to_matrix_proto(np.eye(3) * 2.0),
    )

  @parameterized.named_parameters(
      dict(
          testcase_name='default',
          payload=robot_payload.RobotPayload(),
          other=robot_payload.RobotPayload(),
      ),
      dict(
          testcase_name='full_payload',
          payload=robot_payload.RobotPayload.create(
              mass=1.0,
              tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
              inertia=np.eye(3) * 2.0,
          ),
          other=robot_payload.RobotPayload.create(
              mass=1.0,
              tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
              inertia=np.eye(3) * 2.0,
          ),
      ),
  )
  def test_equal(
      self,
      payload: robot_payload.RobotPayload,
      other: robot_payload.RobotPayload,
  ):
    self.assertEqual(payload, other)

  def test_not_equal(self):
    payload = robot_payload.RobotPayload.create(
        mass=1.0,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=np.eye(3) * 2.0,
    )
    other = robot_payload.RobotPayload.create(
        mass=2.0,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=np.eye(3) * 2.0,
    )

    self.assertNotEqual(payload, other)

  def test_different_types_not_equal(self):
    payload = robot_payload.RobotPayload.create(
        mass=1.0,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=np.eye(3) * 2.0,
    )

    self.assertNotEqual(payload, 1.0)

  def test_to_string(self):
    payload = robot_payload.RobotPayload.create(
        mass=1.0,
        tip_t_cog=data_types.Pose3(translation=[1.0, 2.0, 3.0]),
        inertia=np.eye(3) * 2.0,
    )

    self.assertEqual(
        str(payload),
        'RobotPayload(mass=1.0, tip_t_cog=Pose3(Rotation3([0i + 0j + 0k +'
        ' 1]),[1. 2. 3.]), inertia=[[2. 0. 0.]\n [0. 2. 0.]\n [0. 0. 2.]])',
    )


if __name__ == '__main__':
  absltest.main()
