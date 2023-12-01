# Copyright 2023 Intrinsic Innovation LLC

"""Tests for utils."""

import enum

from absl.testing import absltest
from intrinsic.solutions import utils


class UtilsTest(absltest.TestCase):
  """Tests functions in utils."""

  def test_is_iterable(self):
    """Tests is_iterable."""

    class NonIterableTestClass:

      def __init__(self):
        pass

    class IterableTestClass:

      def __init__(self):
        pass

      def __iter__(self):
        for i in range(0, 5):
          yield i

    self.assertTrue(utils.is_iterable(list()))
    self.assertTrue(utils.is_iterable({}))
    self.assertTrue(utils.is_iterable('foo'))
    self.assertTrue(utils.is_iterable(IterableTestClass()))
    self.assertFalse(utils.is_iterable(5))
    self.assertFalse(utils.is_iterable(NonIterableTestClass()))


class PrefixOptionsTest(absltest.TestCase):
  """Tests for utils.PrefixOptions."""

  def test_init(self):
    options = utils.PrefixOptions(
        xfa_prefix='my_xfa', world_prefix='my_world', skill_prefix='my_skills'
    )

    self.assertEqual(options.xfa_prefix, 'my_xfa')
    self.assertEqual(options.world_prefix, 'my_world')
    self.assertEqual(options.skill_prefix, 'my_skills')


if __name__ == '__main__':
  absltest.main()
