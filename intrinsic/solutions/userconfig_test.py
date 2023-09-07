# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

import json
import os
import pathlib
import platform
from unittest import mock

from absl.testing import absltest
from intrinsic.solutions import userconfig


class UserConfigTest(absltest.TestCase):

  @mock.patch.object(platform, "system")
  @mock.patch("os.environ", {})
  def test_get_user_config_dir(self, mock_platform_system):
    mock_platform_system.return_value = "Linux"

    with self.assertRaises(RuntimeError):
      userconfig.get_user_config_dir()

    os.environ["HOME"] = "/home/test"
    self.assertEqual(userconfig.get_user_config_dir(), "/home/test/.config")

    mock_platform_system.return_value = "unknown os"
    with self.assertRaisesRegex(NotImplementedError, "unknown os"):
      userconfig.get_user_config_dir()

  @mock.patch.object(userconfig, "get_user_config_dir")
  def test_read_not_found(self, mock_get_user_config_dir):
    """Tests that the `get_config` function raises a `ValueError` if the config file is not found."""
    testdir = self.create_tempdir().full_path
    mock_get_user_config_dir.return_value = testdir + "/.config"
    with self.assertRaises(ValueError):
      userconfig.read()

  @mock.patch.object(userconfig, "get_user_config_dir")
  def test_read(self, mock_get_user_config_dir):
    """Tests that the `get_config` function returns the contents of the config file."""
    config = {"foo": "bar"}
    testdir = self.create_tempdir().full_path
    mock_get_user_config_dir.return_value = testdir + "/.config"
    env_path = pathlib.Path(
        mock_get_user_config_dir(),
        userconfig._CONFIG_FOLDER,
        userconfig._CONFIG_FILE,
    )
    env_path.parent.mkdir(parents=True, exist_ok=True)
    with open(env_path, "w") as env_file:
      json.dump(config, env_file)

    actual_config = userconfig.read()
    self.assertEqual(config, actual_config)


if __name__ == "__main__":
  absltest.main()
