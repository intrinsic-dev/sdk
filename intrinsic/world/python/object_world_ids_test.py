# Copyright 2023 Intrinsic Innovation LLC

"""Tests for object_world_ids."""

from absl.testing import absltest
from intrinsic.world.python import object_world_ids


class ObjectWorldIdsTest(absltest.TestCase):

  def test_root_object_name(self):
    self.assertEqual(
        object_world_ids.ROOT_OBJECT_NAME,
        object_world_ids.WorldObjectName('root'),
    )

  def test_root_object_id(self):
    self.assertEqual(
        object_world_ids.ROOT_OBJECT_ID,
        object_world_ids.ObjectWorldResourceId('root'),
    )


if __name__ == '__main__':
  absltest.main()
