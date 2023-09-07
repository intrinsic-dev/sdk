# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

import math

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.robotics.pymath import coordinate_system as cs
from intrinsic.robotics.pymath import math_test
import numpy as np

RDF = cs.RDF

RHS = cs.CoordinateSystem(
    name='Bullet',
    right_handed=True,
    up_direction=[0, 0, 1],
    front_direction=[1, 0, 0],
)

LHS = cs.CoordinateSystem(
    name='Unity',
    right_handed=False,
    up_direction=[0, 1, 0],
    front_direction=[0, 0, 1],
)

RHS_LHS = np.matmul(RHS._local_rdf, LHS._rdf_local)
LHS_RHS = np.matmul(LHS._local_rdf, RHS._rdf_local)


def point_rhs(r=0, u=0, f=0):
  return RHS.vector_from_rdf([r, -u, f])


def point_lhs(r=0, u=0, f=0):
  return LHS.vector_from_rdf([r, -u, f])


MODEL_POINTS_RDF = [
    cs.Vector3(RDF, 0, 0, 0),
    cs.Vector3(RDF, 2, 0, 0),
    cs.Vector3(RDF, 2, -3, 0),
    cs.Vector3(RDF, 0, -3, 0),
    cs.Vector3(RDF, 0, -3, 4),
    cs.Vector3(RDF, 0, 0, 4),
    cs.Vector3(RDF, 2, 0, 4),
    cs.Vector3(RDF, 2, -3, 4),
]

MODEL_POINTS_RHS = [cs.Vector3.from_rdf(RHS, rdf) for rdf in MODEL_POINTS_RDF]

MODEL_POINTS_LHS = [cs.Vector3.from_rdf(LHS, rdf) for rdf in MODEL_POINTS_RDF]

# Scene poses ordered from leaf to root, so they should be applied in order to a
# model point.
SCENE_POSES_DATA = [
    # angle, axis, translation
    (0, [0, 0, 1], [1, -3, 2]),
    (45, [0, -1, 0], [0, 0, 0]),
    (30, [1, 0, 0], [10, 1, 5]),
    (0, [0, 0, 1], [0, 0, 0]),
    (10, [1, 2, 3], [0, 4, 2]),
]


def pose_from_data(frame, degrees, axis, translation):
  axis_rdf = cs.Vector3(RDF, xyz=axis, normalize=True)
  axis_frame = cs.Vector3.from_rdf(frame, axis_rdf)
  translation_rdf = cs.Vector3(RDF, xyz=translation)
  translation_frame = cs.Vector3.from_rdf(frame, translation_rdf)
  return cs.Pose3(
      rotation=cs.Rotation3.axis_angle(degrees=degrees, axis=axis_frame),
      translation=translation_frame,
  )


SCENE_POSES_RDF = [
    pose_from_data(RDF, degrees, axis, translation)
    for degrees, axis, translation in SCENE_POSES_DATA
]

SCENE_POSES_RHS = [
    pose_from_data(RHS, degrees, axis, translation)
    for degrees, axis, translation in SCENE_POSES_DATA
]

SCENE_POSES_LHS = [
    pose_from_data(LHS, degrees, axis, translation)
    for degrees, axis, translation in SCENE_POSES_DATA
]


def product(values, identity=1):
  result = identity
  for v in reversed(values):
    result *= v
  return result


class FrameTest(math_test.TestCase, parameterized.TestCase):

  @parameterized.parameters(
      (RHS.x, 'V.Bullet([1. 0. 0.])'),
      (LHS.y, 'V.Unity([0. 1. 0.])'),
      (RDF.z, 'V.RDF([0. 0. 1.])'),
      (RHS.i, 'Q.Bullet([1i + 0j + 0k + 0])'),
      (-LHS.j + LHS.k, 'Q.Unity([0i + -1j + 1k + 0])'),
      (RDF.k, 'Q.RDF([0i + 0j + 1k + 0])'),
      (cs.Rotation3(RHS.k), 'R(Q.Bullet([0i + 0j + 1k + 0]))'),
      (cs.Rotation3.identity(LHS), 'R(Q.Unity([0i + 0j + 0k + 1]))'),
      (
          cs.Rotation3.axis_angle(degrees=120, axis=RHS.x + RHS.y + RHS.z),
          'R(Q.Bullet([0.5i + 0.5j + 0.5k + 0.5]))',
      ),
      (
          cs.Pose3(cs.Rotation3(RHS.i), RHS.z),
          'P(R(Q.Bullet([1i + 0j + 0k + 0])), V.Bullet([0. 0. 1.]))',
      ),
      (
          cs.Pose3.identity(RDF),
          'P(R(Q.RDF([0i + 0j + 0k + 1])), V.RDF([0. 0. 0.]))',
      ),
      (
          cs.Pose3.from_rotation(cs.Rotation3(LHS.i + LHS.k)),
          'P(R(Q.Unity([1i + 0j + 1k + 0])), V.Unity([0. 0. 0.]))',
      ),
      (
          cs.Pose3.from_translation(RHS.k),
          'P(R(Q.Bullet([0i + 0j + 0k + 1])), Q.Bullet([0i + 0j + 1k + 0]))',
      ),
  )
  def test_str(self, v, s):
    self.assertEqual(v.__str__(), s)

  @parameterized.parameters(
      (RHS.x, 'V.Bullet([1.0, 0.0, 0.0])'),
      (LHS.y, 'V.Unity([0.0, 1.0, 0.0])'),
      (RDF.z, 'V.RDF([0.0, 0.0, 1.0])'),
      (RHS.i, 'Q.Bullet([1.0, 0.0, 0.0, 0.0])'),
      (LHS.j, 'Q.Unity([0.0, 1.0, 0.0, 0.0])'),
      (RDF.k, 'Q.RDF([0.0, 0.0, 1.0, 0.0])'),
      (cs.Rotation3(RHS.k), 'R(Q.Bullet([0.0, 0.0, 1.0, 0.0]))'),
      (cs.Rotation3.identity(LHS), 'R(Q.Unity([0.0, 0.0, 0.0, 1.0]))'),
      (
          cs.Rotation3(cs.Quaternion.from_xyzw(RHS, [1, -1, 0.5, 0.25])),
          'R(Q.Bullet([1.0, -1.0, 0.5, 0.25]))',
      ),
      (
          cs.Pose3(cs.Rotation3(RHS.i), RHS.z),
          'P(R(Q.Bullet([1.0, 0.0, 0.0, 0.0])), V.Bullet([0.0, 0.0, 1.0]))',
      ),
      (
          cs.Pose3.identity(RDF),
          'P(R(Q.RDF([0.0, 0.0, 0.0, 1.0])), V.RDF([0.0, 0.0, 0.0]))',
      ),
      (
          cs.Pose3.from_rotation(cs.Rotation3(LHS.i + LHS.k)),
          'P(R(Q.Unity([1.0, 0.0, 1.0, 0.0])), V.Unity([0.0, 0.0, 0.0]))',
      ),
      (
          cs.Pose3.from_translation(RHS.k),
          (
              'P(R(Q.Bullet([0.0, 0.0, 0.0, 1.0])), Q.Bullet([0.0, 0.0, 1.0,'
              ' 0.0]))'
          ),
      ),
  )
  def test_repr(self, v, s):
    self.assertEqual(v.__repr__(), s)

  @parameterized.parameters(RHS, LHS)
  def test_transforms(self, frame):
    frame.log()
    det = 1 if frame.right_handed else -1
    self.assertEqual(np.linalg.det(frame._rdf_local), det)
    self.assertEqual(np.linalg.det(frame._local_rdf), det)
    self.assert_all_equal(
        np.matmul(frame._rdf_local, frame._local_rdf), np.identity(3)
    )

  @parameterized.parameters(RHS, LHS)
  def test_vectors(self, frame):
    frame.log()
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, x=1)), frame.right
    )
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, x=-1)), frame.left
    )
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, y=1)), frame.down
    )
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, y=-1)), frame.up
    )
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, z=1)), frame.front
    )
    self.assertEqual(
        cs.Vector3.from_rdf(frame, cs.Vector3(RDF, z=-1)), frame.back
    )
    self.assertEqual(frame.right.to_rdf(), cs.Vector3(RDF, x=1))
    self.assertEqual(frame.left.to_rdf(), cs.Vector3(RDF, x=-1))
    self.assertEqual(frame.down.to_rdf(), cs.Vector3(RDF, y=1))
    self.assertEqual(frame.up.to_rdf(), cs.Vector3(RDF, y=-1))
    self.assertEqual(frame.front.to_rdf(), cs.Vector3(RDF, z=1))
    self.assertEqual(frame.back.to_rdf(), cs.Vector3(RDF, z=-1))

  @parameterized.parameters(RHS, LHS)
  def test_to_frame(self, frame):
    for g in [
        frame.x,
        frame.i,
        cs.Rotation3(frame.j),
        cs.Pose3(cs.Rotation3(frame.k), frame.y + frame.z),
    ]:
      self.assertEqual(g.to_frame(frame), g)
      g_rdf = g.to_rdf()
      self.assertAlmostEqual(g_rdf.to_rdf(), g_rdf)
      self.assertEqual(g.__class__.from_rdf(RDF, g_rdf), g_rdf)
      self.assertEqual(g.__class__.from_rdf(frame, g_rdf), g)

  def test_wrong_system(self):
    msg = 'Geometric objects have different coordinate systems: '

    vec_rhs = RHS.x + RHS.y + RHS.z + RHS.zero
    vec_lhs = LHS.x + LHS.y + LHS.z - LHS.zero
    self.assertRaisesRegex(ValueError, msg, vec_rhs.__add__, vec_lhs)
    self.assertRaisesRegex(ValueError, msg, RHS.x.__add__, LHS.y)
    self.assertRaisesRegex(ValueError, msg, RDF.x.__sub__, LHS.y)
    self.assertRaisesRegex(ValueError, msg, RHS.x.__eq__, RDF.y)
    self.assertRaisesRegex(ValueError, msg, RHS.x.__ne__, LHS.y)
    self.assertRaisesRegex(ValueError, msg, RHS.i.__add__, LHS.j)
    self.assertRaisesRegex(ValueError, msg, RDF.i.__sub__, LHS.j)
    self.assertRaisesRegex(ValueError, msg, RHS.i.__eq__, RDF.j)
    self.assertRaisesRegex(ValueError, msg, RHS.i.__ne__, LHS.j)
    self.assertRaisesRegex(ValueError, msg, RHS.i.__mul__, LHS.j)
    self.assertRaisesRegex(ValueError, msg, RHS.i.__truediv__, LHS.j)

    rot_rhs = cs.Rotation3(RHS.i + RHS.j + RHS.k)
    rot_lhs = cs.Rotation3(LHS.i + LHS.j + LHS.k)
    self.assertRaisesRegex(
        ValueError, msg, rot_rhs.__mul__, cs.Rotation3(LHS.one)
    )
    self.assertRaisesRegex(
        ValueError, msg, rot_rhs.__truediv__, cs.Rotation3(RDF.one)
    )
    self.assertRaisesRegex(
        ValueError, msg, rot_lhs.__sub__, cs.Rotation3(RHS.k)
    )
    self.assertRaisesRegex(ValueError, msg, rot_rhs.rotate_vector, LHS.y)
    self.assertRaisesRegex(ValueError, msg, rot_lhs.rotate_vector, RDF.x)

    self.assertRaisesRegex(ValueError, msg, cs.Pose3, RHS.i, LHS.x)

    pose_rhs = cs.Pose3(rot_rhs, RHS.x)
    pose_lhs = cs.Pose3(rot_lhs, LHS.z)
    pose_rdf = cs.Pose3.identity(RDF)
    pose_rhs_r = cs.Pose3.from_rotation(rot_rhs)
    pose_lhs_r = cs.Pose3.from_rotation(rot_lhs)
    pose_rhs_t = cs.Pose3.from_translation(translation=RHS.x - RHS.y)
    pose_lhs_t = cs.Pose3.from_translation(translation=LHS.y + LHS.z * 2)
    self.assertRaisesRegex(ValueError, msg, pose_rhs.transform_point, LHS.y)
    self.assertRaisesRegex(ValueError, msg, pose_rhs.transform_point, RDF.y)
    self.assertRaisesRegex(ValueError, msg, pose_lhs.transform_point, RHS.y)
    self.assertRaisesRegex(ValueError, msg, pose_rdf.transform_point, LHS.y)
    self.assertRaisesRegex(ValueError, msg, pose_rhs.__mul__, pose_lhs)
    self.assertRaisesRegex(ValueError, msg, pose_lhs.__mul__, pose_rhs_r)
    self.assertRaisesRegex(ValueError, msg, pose_lhs.__mul__, pose_rhs_t)
    self.assertRaisesRegex(ValueError, msg, pose_rhs.__mul__, pose_rdf)
    self.assertRaisesRegex(ValueError, msg, pose_rhs_r.__truediv__, pose_lhs)
    self.assertRaisesRegex(ValueError, msg, pose_rdf.__truediv__, pose_lhs_r)
    self.assertRaisesRegex(ValueError, msg, pose_lhs_t.__sub__, pose_rhs)
    self.assertRaisesRegex(ValueError, msg, pose_lhs_r.__sub__, pose_rhs_t)


class RhsTest(math_test.TestCase):

  def test_frame(self):
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, x=1)), RHS.right)
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, x=-1)), RHS.left)
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, y=1)), RHS.down)
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, y=-1)), RHS.up)
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, z=1)), RHS.front)
    self.assertEqual(cs.Vector3.from_rdf(RHS, cs.Vector3(RDF, z=-1)), RHS.back)

  def test_vector3(self):
    v1 = cs.Vector3(RHS, 1, 1, 1)
    for v in [RHS.zero, v1, RHS.x, RHS.y, RHS.z]:
      logging.debug('cs.Vector3.__str__ = %s', v)
      logging.debug('cs.Vector3.__repr__ = %r', v)
      self.assertEqual(v, v)
      self.assertEqual(v * 0, RHS.zero)
      self.assertEqual(v * 0.0, RHS.zero)
      self.assertEqual(v + v, v * 2)
      self.assertEqual(v - v, RHS.zero)
      self.assertEqual(v + RHS.zero, v)
      self.assertEqual(v - RHS.zero, v)
      self.assertEqual(RHS.zero - v, -v)
      self.assertNotEqual(v + v1, v)
      self.assertNotEqual(v + RHS.x, v)
      self.assertNotEqual(v + RHS.y, v)
      self.assertNotEqual(v + RHS.z, v)

    self.assertEqual(RHS.x + RHS.y + RHS.z, v1)

  def test_quaternion(self):
    q0 = cs.Quaternion.zero(RHS)
    for q in [RHS.one, RHS.i, RHS.j, RHS.k]:
      logging.debug('cs.Quaternion.__str__ = %s', q)
      logging.debug('cs.Quaternion.__repr__ = %r', q)
      self.assertEqual(q, q)
      self.assertEqual(q * q0, q0)
      self.assertEqual(q0 * q, q0)
      q_inv = q.inverse()
      self.assertEqual(q * q_inv, RHS.one)
      self.assertEqual(q_inv * q, RHS.one)

    self.assertEqual(RHS.i * RHS.j, RHS.k)
    self.assertEqual(RHS.j * RHS.i, -RHS.k)
    self.assertEqual(RHS.j * RHS.k, RHS.i)
    self.assertEqual(RHS.k * RHS.j, -RHS.i)
    self.assertEqual(RHS.k * RHS.i, RHS.j)
    self.assertEqual(RHS.i * RHS.k, -RHS.j)

  def test_rotation(self):
    v1 = cs.Vector3(RHS, 1, 1, 1)
    r_identity = cs.Rotation3.identity(RHS)
    rx180 = cs.Rotation3(q=RHS.i)
    ry180 = cs.Rotation3(q=RHS.j)
    rz180 = cs.Rotation3(q=RHS.k)
    rx90 = cs.Rotation3.x_rotation(RHS, degrees=90)
    ry90 = cs.Rotation3.y_rotation(RHS, degrees=90)
    rz90 = cs.Rotation3.z_rotation(RHS, degrees=90)
    for r in [r_identity, rx180, ry180, rz180, rx90, ry90, rz90]:
      logging.debug('cs.Quaternion.__str__ = %s', r)
      logging.debug('cs.Quaternion.__repr__ = %r', r)
      r_inv = r.inverse()
      self.assertEqual(r, r)
      self.assertEqual(r_inv, r_inv)
      self.assertEqual(r * r_identity, r)
      self.assertEqual(r_identity * r, r)
      self.assertEqual(r * r_inv, r_identity)
      self.assertEqual(r_inv * r, r_identity)
      for v in [RHS.zero, v1, RHS.x, RHS.y, RHS.z]:
        v_r = r.rotate_vector(v)
        v_r_inv = r_inv.rotate_vector(v)
        self.assertAlmostEqual(r_inv.rotate_vector(v_r), v)
        self.assertAlmostEqual(r.rotate_vector(v_r_inv), v)

    self.assertAlmostEqual(rx90.rotate_vector(RHS.x), RHS.x)
    self.assertAlmostEqual(rx90.rotate_vector(RHS.y), RHS.z, msg=rx90)
    self.assertAlmostEqual(rx90.rotate_vector(RHS.z), -RHS.y)

    self.assertAlmostEqual(ry90.rotate_vector(RHS.x), -RHS.z)
    self.assertAlmostEqual(ry90.rotate_vector(RHS.y), RHS.y)
    self.assertAlmostEqual(ry90.rotate_vector(RHS.z), RHS.x)

    self.assertAlmostEqual(rz90.rotate_vector(RHS.x), RHS.y)
    self.assertAlmostEqual(rz90.rotate_vector(RHS.y), -RHS.x)
    self.assertAlmostEqual(rz90.rotate_vector(RHS.z), RHS.z)

  def test_rotation_angle(self):
    for degrees in range(-180, 180, 15):
      radians = np.radians(degrees)
      s = math.sin(radians)
      c = math.cos(radians)
      x_rotation = cs.Rotation3.x_rotation(RHS, degrees=degrees)
      y_rotation = cs.Rotation3.y_rotation(RHS, degrees=degrees)
      z_rotation = cs.Rotation3.z_rotation(RHS, degrees=degrees)
      for v in MODEL_POINTS_RHS:
        logging.debug('degrees=%s, v=%s', degrees, v)
        x_rot = x_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            x_rot, cs.Vector3(RHS, v.x, v.y * c - v.z * s, v.z * c + v.y * s)
        )
        y_rot = y_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            y_rot, cs.Vector3(RHS, v.x * c + v.z * s, v.y, v.z * c - v.x * s)
        )
        z_rot = z_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            z_rot, cs.Vector3(RHS, v.x * c - v.y * s, v.y * c + v.x * s, v.z)
        )

  def test_pose(self):
    p_identity = cs.Pose3.identity(RHS)
    world_pose_model = product(SCENE_POSES_RHS, p_identity)
    poses = SCENE_POSES_RHS
    poses_inv = [p.inverse() for p in poses]
    for p in poses:
      p_inv = p.inverse()
      self.assertAlmostEqual(p * p_inv, p_identity)
      self.assertAlmostEqual(p_inv * p, p_identity)

    for p_model in MODEL_POINTS_RHS:
      p_world = world_pose_model.transform_point(p_model)
      p_tmp = p_model
      for pose in poses:
        p_tmp = pose.transform_point(p_tmp)
      self.assertAlmostEqual(p_tmp, p_world)
      p_tmp = p_world
      for pose in poses_inv:
        p_tmp = pose.transform_point(p_world)


class LhsTest(math_test.TestCase):

  def test_vector3(self):
    v1 = cs.Vector3(LHS, 1, 1, 1)
    for v in [LHS.zero, LHS.x, LHS.y, LHS.z, v1]:
      logging.debug('cs.Vector3.__str__ = %s', v)
      logging.debug('cs.Vector3.__repr__ = %r', v)
      self.assertEqual(v, v)
      self.assertEqual(v * 0, LHS.zero)
      self.assertEqual(v * 0.0, LHS.zero)
      self.assertEqual(v + v, v * 2)
      self.assertEqual(v - v, LHS.zero)
      self.assertEqual(v + LHS.zero, v)
      self.assertEqual(v - LHS.zero, v)
      self.assertEqual(LHS.zero - v, -v)
      self.assertNotEqual(v + v1, v)
      self.assertNotEqual(v + LHS.x, v)
      self.assertNotEqual(v + LHS.y, v)
      self.assertNotEqual(v + LHS.z, v)

    self.assertEqual(LHS.x + LHS.y + LHS.z, v1)

  def test_quaternion(self):
    q0 = cs.Quaternion.zero(LHS)
    for q in [LHS.one, LHS.i, LHS.j, LHS.k]:
      logging.debug('cs.Quaternion.__str__ = %s', q)
      logging.debug('cs.Quaternion.__repr__ = %r', q)
      self.assertEqual(q, q)
      self.assertEqual(q * q0, q0)
      self.assertEqual(q0 * q, q0)
      q_inv = q.inverse()
      self.assertEqual(q * q_inv, LHS.one)
      self.assertEqual(q_inv * q, LHS.one)

    self.assertEqual(LHS.i * LHS.j, -LHS.k)
    self.assertEqual(LHS.j * LHS.i, LHS.k)
    self.assertEqual(LHS.j * LHS.k, -LHS.i)
    self.assertEqual(LHS.k * LHS.j, LHS.i)
    self.assertEqual(LHS.k * LHS.i, -LHS.j)
    self.assertEqual(LHS.i * LHS.k, LHS.j)

  def test_rotation(self):
    v1 = cs.Vector3(LHS, 1, 1, 1)

    r_identity = cs.Rotation3.identity(LHS)
    rx180 = cs.Rotation3(q=LHS.i)
    ry180 = cs.Rotation3(q=LHS.j)
    rz180 = cs.Rotation3(q=LHS.k)
    rx90 = cs.Rotation3.x_rotation(LHS, degrees=90)
    ry90 = cs.Rotation3.y_rotation(LHS, degrees=90)
    rz90 = cs.Rotation3.z_rotation(LHS, degrees=90)
    for r in [r_identity, rx180, ry180, rz180, rx90, ry90, rz90]:
      logging.debug('cs.Quaternion.__str__ = %s', r)
      logging.debug('cs.Quaternion.__repr__ = %r', r)
      r_inv = r.inverse()
      self.assertEqual(r, r)
      self.assertEqual(r_inv, r_inv)
      self.assertEqual(r * r_identity, r)
      self.assertEqual(r_identity * r, r)
      self.assertEqual(r * r_inv, r_identity)
      self.assertEqual(r_inv * r, r_identity)
      for v in [LHS.zero, v1, LHS.x, LHS.y, LHS.z]:
        v_r = r.rotate_vector(v)
        v_r_inv = r_inv.rotate_vector(v)
        self.assertAlmostEqual(r_inv.rotate_vector(v_r), v)
        self.assertAlmostEqual(r.rotate_vector(v_r_inv), v)

    self.assertAlmostEqual(rx90.rotate_vector(LHS.x), LHS.x)
    self.assertAlmostEqual(rx90.rotate_vector(LHS.y), -LHS.z)
    self.assertAlmostEqual(rx90.rotate_vector(LHS.z), LHS.y)

    self.assertAlmostEqual(ry90.rotate_vector(LHS.x), LHS.z)
    self.assertAlmostEqual(ry90.rotate_vector(LHS.y), LHS.y)
    self.assertAlmostEqual(ry90.rotate_vector(LHS.z), -LHS.x)

    self.assertAlmostEqual(rz90.rotate_vector(LHS.x), -LHS.y)
    self.assertAlmostEqual(rz90.rotate_vector(LHS.y), LHS.x)
    self.assertAlmostEqual(rz90.rotate_vector(LHS.z), LHS.z)

  def test_rotation_angle(self):
    for degrees in range(-180, 180, 15):
      radians = np.radians(degrees)
      s = math.sin(radians)
      c = math.cos(radians)
      x_rotation = cs.Rotation3.x_rotation(LHS, degrees=degrees)
      y_rotation = cs.Rotation3.y_rotation(LHS, degrees=degrees)
      z_rotation = cs.Rotation3.z_rotation(LHS, degrees=degrees)
      for v in MODEL_POINTS_LHS:
        logging.debug('degrees=%s, v=%s', degrees, v)
        x_rot = x_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            x_rot, cs.Vector3(LHS, v.x, v.y * c + v.z * s, v.z * c - v.y * s)
        )
        y_rot = y_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            y_rot, cs.Vector3(LHS, v.x * c - v.z * s, v.y, v.z * c + v.x * s)
        )
        z_rot = z_rotation.rotate_vector(v)
        self.assertAlmostEqual(
            z_rot, cs.Vector3(LHS, v.x * c + v.y * s, v.y * c - v.x * s, v.z)
        )

  def test_pose(self):
    p_identity = cs.Pose3.identity(LHS)
    world_pose_model = product(SCENE_POSES_LHS, p_identity)
    poses = SCENE_POSES_LHS
    poses_inv = [p.inverse() for p in poses]
    for p in poses:
      p_inv = p.inverse()
      self.assertAlmostEqual(p * p_inv, p_identity)
      self.assertAlmostEqual(p_inv * p, p_identity)

    for p_model in MODEL_POINTS_LHS:
      p_world = world_pose_model.transform_point(p_model)
      p_tmp = p_model
      for pose in poses:
        p_tmp = pose.transform_point(p_tmp)
      self.assertAlmostEqual(p_tmp, p_world)
      p_tmp = p_world
      for pose in poses_inv:
        p_tmp = pose.transform_point(p_world)


class FrameConversionTest(math_test.TestCase):

  def _lhs_rhs(self, lhs, rhs, rdf=None):
    if rdf is None:
      rdf = lhs.to_rdf()
    msg = '\nlhs = %s\nrhs = %s\nrdf = %s' % (lhs, rhs, rdf)
    self.assertAlmostEqual(lhs.to_rdf(), rdf, msg=msg)
    self.assertAlmostEqual(rhs.to_rdf(), rdf, msg=msg)
    self.assertAlmostEqual(lhs.from_rdf(lhs.frame, rdf), lhs, msg=msg)
    self.assertAlmostEqual(rhs.from_rdf(rhs.frame, rdf), rhs, msg=msg)
    self.assertAlmostEqual(lhs.to_frame(rhs.frame), rhs, msg=msg)
    self.assertAlmostEqual(rhs.to_frame(lhs.frame), lhs, msg=msg)

  def test_frames(self):
    RHS.log()
    LHS.log()

    rhs_lhs = np.matmul(RHS._local_rdf, LHS._rdf_local)
    logging.info('\nrhs_lhs=\n%s', rhs_lhs)

    lhs_rhs = np.matmul(LHS._local_rdf, RHS._rdf_local)
    logging.info('\nlhs_rhs=\n%s', lhs_rhs)

    v1_lhs = cs.Vector3(LHS, 1, 1, 1)
    for v_lhs in [LHS.zero, v1_lhs, LHS.x, LHS.y, LHS.z]:
      v_rhs = v_lhs.to_frame(RHS)
      xyz_rhs = np.matmul(rhs_lhs, v_lhs.xyz)
      xyz_lhs = np.matmul(lhs_rhs, v_rhs.xyz)
      self.assertEqual(cs.Vector3(RHS, xyz=xyz_rhs), v_rhs)
      self.assertEqual(cs.Vector3(LHS, xyz=xyz_lhs), v_lhs)

  def test_vector(self):
    v1_lhs = cs.Vector3(LHS, 1, 1, 1)
    for v_lhs in [LHS.zero, v1_lhs, LHS.x, LHS.y, LHS.z]:
      v_rdf = v_lhs.to_rdf()
      v_rhs = v_lhs.to_frame(RHS)
      self._lhs_rhs(v_lhs, v_rhs)
      self.assertEqual(v_lhs.to_frame(LHS), v_lhs)
      self.assertEqual(v_rdf.to_frame(LHS), v_lhs)
      self.assertEqual(v_rdf.to_rdf(), v_rdf)

  def test_facings(self):
    self._lhs_rhs(LHS.zero, RHS.zero)
    self._lhs_rhs(LHS.front, RHS.front)
    self._lhs_rhs(LHS.back, RHS.back)
    self._lhs_rhs(LHS.up, RHS.up)
    self._lhs_rhs(LHS.down, RHS.down)
    self._lhs_rhs(LHS.left, RHS.left)
    self._lhs_rhs(LHS.right, RHS.right)

  def test_quaternion(self):
    q1234_lhs = cs.Quaternion.from_xyzw(LHS, [1, 2, 3, 4])
    for q_lhs in [LHS.one, LHS.i, LHS.j, LHS.k, q1234_lhs]:
      q_rhs = q_lhs.to_frame(RHS)
      self._lhs_rhs(q_lhs, q_rhs)
      self._lhs_rhs(q_lhs.inverse(), q_rhs.inverse())
      for u_lhs in [LHS.one, LHS.i, LHS.j, LHS.k, q1234_lhs]:
        u_rhs = u_lhs.to_frame(RHS)
        qu_lhs = q_lhs * u_lhs
        qu_rhs = q_rhs * u_rhs
        self._lhs_rhs(qu_lhs, qu_rhs)
        self._lhs_rhs(qu_lhs.inverse(), qu_rhs.inverse())

  def test_rotation(self):
    v1_lhs = cs.Vector3(LHS, 1, 1, 1)
    q1234_lhs = cs.Quaternion.from_xyzw(LHS, [1, 2, 3, 4])
    r_identity_lhs = cs.Rotation3.identity(LHS)
    rx180_lhs = cs.Rotation3(q=LHS.i)
    ry180_lhs = cs.Rotation3(q=LHS.j)
    rz180_lhs = cs.Rotation3(q=LHS.k)
    rx90_lhs = cs.Rotation3.x_rotation(LHS, degrees=90)
    ry90_lhs = cs.Rotation3.y_rotation(LHS, degrees=90)
    rz90_lhs = cs.Rotation3.z_rotation(LHS, degrees=90)
    r1234_lhs = cs.Rotation3(q=q1234_lhs, normalize=True)

    vectors_lhs = [
        LHS.zero,
        LHS.x,
        LHS.y,
        LHS.z,
        v1_lhs,
        cs.Vector3(LHS, 1, -1, 1),
        cs.Vector3(LHS, 1, 2, 3),
    ]
    rotations_lhs = [
        r_identity_lhs,
        rx180_lhs,
        ry180_lhs,
        rz180_lhs,
        rx90_lhs,
        ry90_lhs,
        rz90_lhs,
        r1234_lhs,
    ]
    for r_lhs in rotations_lhs:
      r_rhs = r_lhs.to_frame(RHS)
      self._lhs_rhs(r_lhs, r_rhs)
      self.assertEqual(r_rhs.to_frame(LHS), r_lhs)
      self.assertEqual(r_lhs.inverse().to_frame(RHS), r_rhs.inverse())
      for u_lhs in rotations_lhs:
        u_rhs = u_lhs.to_frame(RHS)
        ru_lhs = r_lhs * u_lhs
        ru_rhs = r_rhs * u_rhs
        self.assertEqual(ru_lhs.to_frame(RHS), ru_rhs)
        self._lhs_rhs(ru_lhs, ru_rhs)
        for v_lhs in vectors_lhs:
          v_rhs = v_lhs.to_frame(RHS)
          uv_lhs = u_lhs.rotate_vector(v_lhs)
          ruv_lhs = r_lhs.rotate_vector(uv_lhs)
          uv_rhs = u_rhs.rotate_vector(v_rhs)
          ruv_rhs = r_rhs.rotate_vector(uv_rhs)
          self.assertAlmostEqual(ruv_lhs.to_frame(RHS), ruv_rhs)
          self._lhs_rhs(ruv_lhs, ruv_rhs)

  def test_rotation_angle(self):
    for degrees in range(-180, 180, 15):
      radians = np.radians(degrees)
      for axis_rdf in [
          cs.Vector3(frame=RDF, x=1),
          cs.Vector3(frame=RDF, y=1),
          cs.Vector3(frame=RDF, z=1),
          cs.Vector3(frame=RDF, xyz=[1, 1, 1], normalize=True),
      ]:
        axis_lhs = cs.Vector3.from_rdf(LHS, axis_rdf)
        axis_rhs = cs.Vector3.from_rdf(RHS, axis_rdf)
        rot_rdf = cs.Rotation3.axis_angle(degrees=degrees, axis=axis_rdf)
        rot_lhs = cs.Rotation3.axis_angle(degrees=degrees, axis=axis_lhs)
        rot_rhs = cs.Rotation3.axis_angle(degrees=degrees, axis=axis_rhs)
        self._lhs_rhs(rot_lhs, rot_rhs, rot_rdf)
        self.assertEqual(
            cs.Rotation3.axis_angle(radians=radians, axis=axis_rdf), rot_rdf
        )
        self.assertEqual(
            cs.Rotation3.axis_angle(radians=radians, axis=axis_rhs), rot_rhs
        )
        self.assertEqual(
            cs.Rotation3.axis_angle(radians=radians, axis=axis_lhs), rot_lhs
        )
        for pt_model_lhs, pt_model_rhs in zip(
            MODEL_POINTS_LHS, MODEL_POINTS_RHS
        ):
          self._lhs_rhs(pt_model_lhs, pt_model_rhs)
          pt_lhs = rot_lhs.rotate_vector(pt_model_lhs)
          pt_rhs = rot_rhs.rotate_vector(pt_model_rhs)
          self._lhs_rhs(pt_lhs, pt_rhs)

  def test_model_points(self):
    for pt_model_lhs, pt_model_rhs in zip(MODEL_POINTS_LHS, MODEL_POINTS_RHS):
      self._lhs_rhs(pt_model_lhs, pt_model_rhs)

  def test_scene_poses(self):
    for pose_lhs, pose_rhs in zip(SCENE_POSES_LHS, SCENE_POSES_RHS):
      self._lhs_rhs(pose_lhs, pose_rhs)
      self._lhs_rhs(pose_lhs.inverse(), pose_rhs.inverse())

  def test_poses(self):
    poses_rdf = SCENE_POSES_RDF
    poses_lhs = SCENE_POSES_LHS
    poses_rhs = SCENE_POSES_RHS
    product_rdf = cs.Pose3.identity(RDF)
    product_lhs = cs.Pose3.identity(LHS)
    product_rhs = cs.Pose3.identity(RHS)
    for pose_rdf, pose_lhs, pose_rhs in zip(poses_rdf, poses_lhs, poses_rhs):
      self._lhs_rhs(pose_lhs, pose_rhs, pose_rdf)
      product_rdf = pose_rdf * product_rdf
      product_lhs = pose_lhs * product_lhs
      product_rhs = pose_rhs * product_rhs
    self._lhs_rhs(product_lhs, product_rhs, product_rdf)

  def test_inverse_poses(self):
    poses_rdf = [p.inverse() for p in reversed(SCENE_POSES_RDF)]
    poses_lhs = [p.inverse() for p in reversed(SCENE_POSES_LHS)]
    poses_rhs = [p.inverse() for p in reversed(SCENE_POSES_RHS)]
    product_rdf = cs.Pose3.identity(RDF)
    product_lhs = cs.Pose3.identity(LHS)
    product_rhs = cs.Pose3.identity(RHS)
    for pose_rdf, pose_lhs, pose_rhs in zip(poses_rdf, poses_lhs, poses_rhs):
      self._lhs_rhs(pose_lhs, pose_rhs, pose_rdf)
      product_rdf *= pose_rdf
      product_lhs *= pose_lhs
      product_rhs *= pose_rhs
    self._lhs_rhs(product_lhs, product_rhs, product_rdf)

  def test_transform_chain(self):
    poses_lhs = SCENE_POSES_LHS
    poses_inv_lhs = [p.inverse() for p in reversed(SCENE_POSES_LHS)]
    poses_rhs = SCENE_POSES_RHS
    poses_inv_rhs = [p.inverse() for p in reversed(SCENE_POSES_RHS)]

    world_pose_model_lhs = product(poses_lhs, cs.Pose3.identity(LHS))
    model_pose_world_lhs = product(poses_inv_lhs, cs.Pose3.identity(LHS))
    world_pose_model_rhs = product(poses_rhs, cs.Pose3.identity(RHS))
    model_pose_world_rhs = product(poses_inv_rhs, cs.Pose3.identity(RHS))
    self.assertNotEqual(world_pose_model_lhs, model_pose_world_lhs)
    self.assertNotAlmostEqual(world_pose_model_lhs, model_pose_world_lhs)
    self.assertNotEqual(world_pose_model_rhs, model_pose_world_rhs)
    self.assertNotAlmostEqual(world_pose_model_rhs, model_pose_world_rhs)
    self.assertAlmostEqual(
        world_pose_model_lhs * model_pose_world_lhs, cs.Pose3.identity(LHS)
    )
    self.assertAlmostEqual(
        world_pose_model_rhs * model_pose_world_rhs, cs.Pose3.identity(RHS)
    )
    self.assertAlmostEqual(world_pose_model_lhs.inverse(), model_pose_world_lhs)
    self.assertAlmostEqual(world_pose_model_rhs.inverse(), model_pose_world_rhs)
    self.assertAlmostEqual(world_pose_model_lhs, model_pose_world_lhs.inverse())
    self.assertAlmostEqual(world_pose_model_rhs, model_pose_world_rhs.inverse())

    self._lhs_rhs(cs.Pose3.identity(LHS), cs.Pose3.identity(RHS))
    self._lhs_rhs(world_pose_model_lhs, world_pose_model_rhs)
    self._lhs_rhs(model_pose_world_lhs, model_pose_world_rhs)

    for pt_model_rdf in MODEL_POINTS_RDF:
      pt_model_lhs = cs.Vector3.from_rdf(LHS, pt_model_rdf)
      pt_model_rhs = cs.Vector3.from_rdf(RHS, pt_model_rdf)
      self._lhs_rhs(pt_model_lhs, pt_model_rhs)

      pt_world_lhs = world_pose_model_lhs.transform_point(pt_model_lhs)
      pt_world_rhs = world_pose_model_rhs.transform_point(pt_model_rhs)
      self._lhs_rhs(pt_world_lhs, pt_world_rhs)

      node_pose_model_lhs = cs.Pose3.identity(LHS)
      node_pose_model_rhs = cs.Pose3.identity(RHS)
      pt_node_lhs = pt_model_lhs
      pt_node_rhs = pt_model_rhs
      for node_pose_lhs, node_pose_rhs in zip(poses_lhs, poses_rhs):
        self._lhs_rhs(node_pose_lhs, node_pose_rhs)

        node_pose_model_lhs = node_pose_lhs * node_pose_model_lhs
        node_pose_model_rhs = node_pose_rhs * node_pose_model_rhs
        self._lhs_rhs(node_pose_model_lhs, node_pose_model_rhs)

        pt_node_lhs = node_pose_lhs.transform_point(pt_node_lhs)
        pt_node_rhs = node_pose_rhs.transform_point(pt_node_rhs)
        self._lhs_rhs(pt_node_lhs, pt_node_rhs)

        pt2_node_lhs = node_pose_model_lhs.transform_point(pt_model_lhs)
        pt2_node_rhs = node_pose_model_rhs.transform_point(pt_model_rhs)
        self._lhs_rhs(pt2_node_lhs, pt2_node_rhs)

        self.assertAlmostEqual(
            node_pose_model_lhs.transform_point(pt_model_lhs), pt_node_lhs
        )
        self.assertAlmostEqual(
            node_pose_model_rhs.transform_point(pt_model_rhs), pt_node_rhs
        )

      self.assertAlmostEqual(pt_node_lhs, pt_world_lhs)
      self.assertAlmostEqual(pt_node_rhs, pt_world_rhs)

      node_pose_world_lhs = cs.Pose3.identity(LHS)
      node_pose_world_rhs = cs.Pose3.identity(RHS)
      pt_node_lhs = pt_world_lhs
      pt_node_rhs = pt_world_rhs
      for node_pose_lhs, node_pose_rhs in zip(poses_inv_lhs, poses_inv_rhs):
        self._lhs_rhs(node_pose_lhs, node_pose_rhs)

        node_pose_world_lhs = node_pose_lhs * node_pose_world_lhs
        node_pose_world_rhs = node_pose_rhs * node_pose_world_rhs
        self._lhs_rhs(node_pose_world_lhs, node_pose_world_rhs)

        pt_node_lhs = node_pose_lhs.transform_point(pt_node_lhs)
        pt_node_rhs = node_pose_rhs.transform_point(pt_node_rhs)
        self._lhs_rhs(pt_node_lhs, pt_node_rhs)

        pt2_node_lhs = node_pose_world_lhs.transform_point(pt_world_lhs)
        pt2_node_rhs = node_pose_world_rhs.transform_point(pt_world_rhs)
        self._lhs_rhs(pt2_node_lhs, pt2_node_rhs)

        self.assertAlmostEqual(
            node_pose_world_lhs.transform_point(pt_world_lhs), pt_node_lhs
        )
        self.assertAlmostEqual(
            node_pose_world_rhs.transform_point(pt_world_rhs), pt_node_rhs
        )


if __name__ == '__main__':
  np.random.seed(0)
  absltest.main()
