# Copyright 2023 Intrinsic Innovation LLC

"""Tests for ipython."""

import io
import sys
from unittest import mock

from absl.testing import absltest
from intrinsic.solutions import ipython


class IpythonTest(absltest.TestCase):

  def test_no_html_display_outside_ipython(self):
    stdout_mock = io.StringIO()
    with mock.patch.object(sys, 'stdout', stdout_mock):
      ipython.display_html_if_ipython('<span>Some html</span>')

    self.assertEqual(
        stdout_mock.getvalue(), 'Display only executed in IPython.\n'
    )

  def test_no_display_outside_ipython(self):
    stdout_mock = io.StringIO()
    with mock.patch.object(sys, 'stdout', stdout_mock):
      ipython.display_if_ipython('<span>Some html</span>')

    self.assertEqual(
        stdout_mock.getvalue(), 'Display only executed in IPython.\n'
    )


if __name__ == '__main__':
  absltest.main()
