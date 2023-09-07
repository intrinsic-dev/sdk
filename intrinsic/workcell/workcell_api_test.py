# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for workcell_api."""

import time
from unittest import mock

from absl.testing import absltest
from intrinsic.workcell import workcell_api


class WorkcellApiTest(absltest.TestCase):

  @mock.patch.object(time, "sleep")  # From retry logic in errors.py.
  def test_smoke(self, unused_mock_time):
    """Smoke test, mainly to ensure that importing workcell_api works."""
    # What we assert on here specifically is not that relevant.
    with self.assertRaises(Exception):
      workcell_api.connect(address="invalid_hostname:1234")


if __name__ == "__main__":
  absltest.main()
