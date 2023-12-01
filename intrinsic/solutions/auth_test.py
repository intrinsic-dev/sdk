# Copyright 2023 Intrinsic Innovation LLC

import datetime
import pathlib
from unittest import mock
from absl.testing import absltest
from intrinsic.solutions import auth
from intrinsic.solutions import userconfig


class AuthTest(absltest.TestCase):

  @mock.patch.object(userconfig, "get_user_config_dir", autospec=True)
  def test_get_configuration_configuration_not_found(
      self, mock_user_config_dir
  ):
    testdir = self.create_tempdir()
    mock_user_config_dir.return_value = testdir.full_path

    with self.assertRaises(auth.CredentialsNotFoundError):
      auth.get_configuration("bad_configuration")

  @mock.patch.object(userconfig, "get_user_config_dir", autospec=True)
  def test_get_configuration_returns_valid_configuration_if_exists(
      self, mock_user_config_dir
  ):
    testdir = self.create_tempdir()
    testfile = pathlib.Path(
        testdir.full_path,
        auth.STORE_DIRECTORY,
        f"test-project{auth.AUTH_CONFIG_EXTENSION}",
    )
    testfile.parent.mkdir(exist_ok=True, parents=True)
    testfile.write_text("""{
  "name": "test-project",
  "tokens": {
    "default": {
      "apiKey": "ink_0000000000000000000000000000000000000000000000000000000000000000",
      "validUntil": "2023-06-01T00:00:00.000000+00:00"
    },
    "test": {
      "apiKey": "ink_1111111111111111111111111111111111111111111111111111111111111111",
      "validUntil": "2023-07-01T00:00:00.000000+00:00"
    }
  },
  "lastUpdated": "2023-05-24T09:22:26Z"
}""")

    gold = auth.ProjectConfiguration(
        "test-project",
        tokens={
            "default": auth.ProjectToken(
                "ink_0000000000000000000000000000000000000000000000000000000000000000",
                datetime.datetime.fromisoformat(
                    "2023-06-01T00:00:00.000000+00:00"
                ),
            ),
            "test": auth.ProjectToken(
                "ink_1111111111111111111111111111111111111111111111111111111111111111",
                datetime.datetime.fromisoformat(
                    "2023-07-01T00:00:00.000000+00:00"
                ),
            ),
        },
    )
    mock_user_config_dir.return_value = testdir.full_path
    result = auth.get_configuration("test-project")
    self.assertEqual(gold, result)

  def test_project_token_validate(self):
    token = auth.ProjectToken("ink_00000")

    # should not raise if API key is set (valid_until is optional)
    token.validate()

    token.valid_until = datetime.datetime.now() + datetime.timedelta(days=1)
    token.validate()

    # expired token should raise
    token.valid_until = datetime.datetime.now() - datetime.timedelta(days=1)
    with self.assertRaisesRegex(AttributeError, "project token expired: .*"):
      token.validate()

  def test_project_token_get_request_metadata(self):
    token = auth.ProjectToken("ink_00000")
    self.assertEqual(
        token.get_request_metadata(), (("authorization", "Bearer ink_00000"),)
    )

  @mock.patch.object(userconfig, "get_user_config_dir", autospec=True)
  def test_read_org_info_raises_if_file_not_found(self, mock_user_config_dir):
    testdir = self.create_tempdir()
    mock_user_config_dir.return_value = testdir.full_path

    with self.assertRaises(auth.OrgNotFoundError):
      auth.read_org_info("org_for_which_no_local_info_is_stored")

  @mock.patch.object(userconfig, "get_user_config_dir", autospec=True)
  def test_read_org_info_returns_stored_org_info(self, mock_user_config_dir):
    testdir = self.create_tempdir()
    testfile = pathlib.Path(
        testdir.full_path, auth.ORG_STORE_DIRECTORY, "my_org.json"
    )
    testfile.parent.mkdir(exist_ok=True, parents=True)
    testfile.write_text("""{
  "org": "my_org",
  "project": "my_project"
}""")
    mock_user_config_dir.return_value = testdir.full_path

    result = auth.read_org_info("my_org")

    self.assertEqual(
        result, auth.OrgInfo(organization="my_org", project="my_project")
    )


if __name__ == "__main__":
  absltest.main()
