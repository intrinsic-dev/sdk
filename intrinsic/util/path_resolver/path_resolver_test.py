# Copyright 2023 Intrinsic Innovation LLC

"""Tests for helper functions to resolve runfiles paths."""

import os

from absl.testing import absltest
from intrinsic.util.path_resolver import path_resolver

TEST_FILE = 'intrinsic/util/path_resolver/path_resolver_test.py'


class PathResolverTest(absltest.TestCase):

  def test_resolve_runfiles_path(self):
    path = path_resolver.resolve_runfiles_path(TEST_FILE)
    self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
  absltest.main()
