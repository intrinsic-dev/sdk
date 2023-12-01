# Copyright 2023 Intrinsic Innovation LLC

from unittest import mock
from absl.testing import absltest
import grpc
from intrinsic.solutions import auth
from intrinsic.solutions import dialerutil


class DialerutilTest(absltest.TestCase):

  def test_create_channel_params_has_local_address(self):
    params = dialerutil.CreateChannelParams(
        address="http://istio-ingressgateway.app-ingress.svc.cluster.local:80"
    )
    self.assertTrue(params.has_local_address())

    params = dialerutil.CreateChannelParams(address="127.0.0.1:17080")
    self.assertTrue(params.has_local_address())

  def test_load_credentials_should_raise_if_non_local_and_cred_missing(self):
    params = dialerutil.CreateChannelParams()
    with self.assertRaises(ValueError):
      dialerutil._load_credentials(params)

  @mock.patch.object(auth, "get_configuration", autospec=True)
  def test_load_credentials_should_return_valid_token(
      self, mock_get_configuration
  ):
    mock_get_configuration.return_value = auth.ProjectConfiguration(
        name="test-project",
        tokens={"default": auth.ProjectToken("test-token", None)},
    )

    params = dialerutil.CreateChannelParams(project_name="test")
    result = dialerutil._load_credentials(params)
    self.assertIsNotNone(result)
    self.assertEqual(result.api_key, "test-token")

  @mock.patch.object(auth, "get_configuration", autospec=True)
  def test_dial_channel_opens_grpc_connection(self, mock_get_configuration):
    mock_get_configuration.return_value = auth.ProjectConfiguration(
        name="test-project",
        tokens={"default": auth.ProjectToken("test-token", None)},
    )
    channel = dialerutil.create_channel(
        params=dialerutil.CreateChannelParams(
            project_name="test", cluster="test-cluster"
        )
    )
    self.assertIsInstance(channel, grpc.Channel)


if __name__ == "__main__":
  absltest.main()
