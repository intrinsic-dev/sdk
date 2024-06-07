# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.icon.python.icon_api."""

from unittest import mock

from absl.testing import absltest
import grpc
from intrinsic.icon.proto import logging_mode_pb2
from intrinsic.icon.proto import safety_status_pb2
from intrinsic.icon.proto import service_pb2
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import _session
from intrinsic.icon.python import errors
from intrinsic.icon.python import icon_api
from intrinsic.logging.proto import context_pb2
from intrinsic.math.python import data_types
from intrinsic.util.grpc import connection
from intrinsic.world.robot_payload.python import robot_payload
import numpy as np


class IconTest(absltest.TestCase):

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_local(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    credentials = grpc.local_channel_credentials()
    mock_local_channel_credentials.return_value = credentials
    icon_client = icon_api.Client.connect(insecure=False)
    self.assertIsInstance(icon_client, icon_api.Client)
    mock_secure_channel.assert_called_once_with('localhost:8128', credentials)
    mock_insecure_channel.assert_not_called()
    mock_intercept_channel.assert_called_once()
    mock_channel_ready_future.assert_called_once()

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_insecure(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    icon_client = icon_api.Client.connect(
        grpc_host='foo', grpc_port=1234, insecure=True
    )
    self.assertIsInstance(icon_client, icon_api.Client)
    mock_local_channel_credentials.assert_not_called()
    mock_secure_channel.assert_not_called()
    mock_insecure_channel.assert_called_once_with('foo:1234')
    mock_intercept_channel.assert_called_once()
    mock_channel_ready_future.assert_called_once()

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_error(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    credentials = grpc.local_channel_credentials()
    mock_local_channel_credentials.return_value = credentials
    mock_channel_ready_future.side_effect = grpc.FutureTimeoutError('foo')
    with self.assertRaises(errors.Client.ServerError):
      icon_api.Client.connect(insecure=False)
    mock_intercept_channel.assert_not_called()
    mock_secure_channel.assert_called_once_with('localhost:8128', credentials)
    mock_insecure_channel.assert_not_called()
    mock_channel_ready_future.assert_called_once()

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_local_params(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    credentials = grpc.local_channel_credentials()
    mock_local_channel_credentials.return_value = credentials
    icon_client = icon_api.Client.connect_with_params(
        connection.ConnectionParams.local_port(8128), insecure=False
    )
    self.assertIsInstance(icon_client, icon_api.Client)
    mock_secure_channel.assert_called_once_with('localhost:8128', credentials)
    mock_insecure_channel.assert_not_called()
    mock_intercept_channel.assert_called_once()
    mock_channel_ready_future.assert_called_once()

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_insecure_params(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    icon_client = icon_api.Client.connect_with_params(
        connection.ConnectionParams.no_ingress('foo:1234'), insecure=True
    )
    self.assertIsInstance(icon_client, icon_api.Client)
    mock_local_channel_credentials.assert_not_called()
    mock_secure_channel.assert_not_called()
    mock_insecure_channel.assert_called_once_with('foo:1234')
    mock_intercept_channel.assert_called_once()
    mock_channel_ready_future.assert_called_once()

  @mock.patch.object(grpc, 'intercept_channel', autospec=True)
  @mock.patch.object(grpc, 'channel_ready_future', autospec=True)
  @mock.patch.object(grpc, 'local_channel_credentials', autospec=True)
  @mock.patch.object(grpc, 'secure_channel', autospec=True)
  @mock.patch.object(grpc, 'insecure_channel', autospec=True)
  def test_connect_error_params(
      self,
      mock_insecure_channel,
      mock_secure_channel,
      mock_local_channel_credentials,
      mock_channel_ready_future,
      mock_intercept_channel,
  ):
    credentials = grpc.local_channel_credentials()
    mock_local_channel_credentials.return_value = credentials
    mock_channel_ready_future.side_effect = grpc.FutureTimeoutError('foo')
    with self.assertRaises(errors.Client.ServerError):
      icon_api.Client.connect_with_params(
          connection.ConnectionParams.local_port(8128), insecure=False
      )
    mock_secure_channel.assert_called_once_with('localhost:8128', credentials)
    mock_insecure_channel.assert_not_called()
    mock_intercept_channel.assert_not_called()
    mock_channel_ready_future.assert_called_once()

  def test_generated_action_types(self):
    stub = mock.MagicMock()
    action_signatures = [
        types_pb2.ActionSignature(action_type_name='foo.bar'),
        types_pb2.ActionSignature(action_type_name='a.b.cat'),
        types_pb2.ActionSignature(action_type_name='baz'),
        # Expect this to be skipped since there's no name.
        types_pb2.ActionSignature(),
    ]
    response = service_pb2.ListActionSignaturesResponse(
        action_signatures=action_signatures
    )
    stub.ListActionSignatures.return_value = response

    icon_client = icon_api.Client(stub)
    # pylint: disable=g-generic-assert
    self.assertEqual(len(icon_client.ActionType), 3)
    # pylint: enable=g-generic-assert
    self.assertEqual(icon_client.ActionType.BAR.value, 'foo.bar')
    self.assertEqual(icon_client.ActionType.CAT.value, 'a.b.cat')
    self.assertEqual(icon_client.ActionType.BAZ.value, 'baz')

  def test_get_action_signature_by_name(self):
    stub = mock.MagicMock()
    action_signature = types_pb2.ActionSignature(
        action_type_name='my_action_type'
    )
    response = service_pb2.GetActionSignatureByNameResponse(
        action_signature=action_signature
    )
    stub.GetActionSignatureByName.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(
        icon_client.get_action_signature_by_name('my_action_type'),
        action_signature,
    )
    stub.GetActionSignatureByName.assert_called_once_with(
        service_pb2.GetActionSignatureByNameRequest(name='my_action_type'),
        timeout=None,
    )

  def test_get_action_signature_by_name_not_found(self):
    stub = mock.MagicMock()
    response = service_pb2.GetActionSignatureByNameResponse()
    stub.GetActionSignatureByName.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertIsNone(
        icon_client.get_action_signature_by_name('not_found_action_type')
    )
    stub.GetActionSignatureByName.assert_called_once_with(
        service_pb2.GetActionSignatureByNameRequest(
            name='not_found_action_type'
        ),
        timeout=None,
    )

  def test_get_config(self):
    stub = mock.MagicMock()
    response = service_pb2.GetConfigResponse()
    stub.GetConfig.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(icon_client.get_config(), response)
    stub.GetConfig.assert_called_once_with(
        service_pb2.GetConfigRequest(), timeout=None
    )

  def test_get_status(self):
    stub = mock.MagicMock()
    response = service_pb2.GetStatusResponse()
    stub.GetStatus.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(icon_client.get_status(), response)
    stub.GetStatus.assert_called_once_with(
        service_pb2.GetStatusRequest(), timeout=None
    )

  def test_get_status_safety_status(self):
    stub = mock.MagicMock()
    safety_status = safety_status_pb2.SafetyStatus(
        mode_of_safe_operation=safety_status_pb2.MODE_OF_SAFE_OPERATION_TEACHING_1,
        estop_button_status=safety_status_pb2.BUTTON_STATUS_NOT_AVAILABLE,
        enable_button_status=safety_status_pb2.BUTTON_STATUS_ENGAGED,
        requested_behavior=safety_status_pb2.REQUESTED_BEHAVIOR_NORMAL_OPERATION,
    )
    response = service_pb2.GetStatusResponse(safety_status=safety_status)
    stub.GetStatus.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(icon_client.get_status(), response)
    stub.GetStatus.assert_called_once_with(
        service_pb2.GetStatusRequest(), timeout=None
    )

  def test_is_action_compatible(self):
    stub = mock.MagicMock()
    response = service_pb2.IsActionCompatibleResponse(is_compatible=False)
    stub.IsActionCompatible.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertFalse(
        icon_client.is_action_compatible('linear_move', 'robot_gripper')
    )
    stub.IsActionCompatible.assert_called_once_with(
        service_pb2.IsActionCompatibleRequest(
            action_type_name='linear_move', part_name='robot_gripper'
        ),
        timeout=None,
    )

  def test_list_compatible_parts(self):
    stub = mock.MagicMock()
    response = service_pb2.ListCompatiblePartsResponse(parts=['foo'])
    stub.ListCompatibleParts.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(
        icon_client.list_compatible_parts(action_type_names=['my_action_type']),
        ['foo'],
    )
    stub.ListCompatibleParts.assert_called_once_with(
        service_pb2.ListCompatiblePartsRequest(
            action_type_names=['my_action_type']
        ),
        timeout=None,
    )

  def test_list_parts(self):
    stub = mock.MagicMock()
    response = service_pb2.ListPartsResponse(parts=['foo'])
    stub.ListParts.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(icon_client.list_parts(), ['foo'])
    stub.ListParts.assert_called_once_with(
        service_pb2.ListPartsRequest(), timeout=None
    )

  def test_list_action_signatures(self):
    stub = mock.MagicMock()
    icon_client = icon_api.Client(stub)
    stub.ListActionSignatures.reset_mock()

    action_signatures = [types_pb2.ActionSignature()]
    response = service_pb2.ListActionSignaturesResponse(
        action_signatures=action_signatures
    )
    stub.ListActionSignatures.return_value = response
    self.assertEqual(
        list(icon_client.list_action_signatures()), action_signatures
    )
    stub.ListActionSignatures.assert_called_once_with(
        service_pb2.ListActionSignaturesRequest(), timeout=None
    )

  def test_enable(self):
    stub = mock.MagicMock()
    response = service_pb2.EnableResponse()
    stub.Enable.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.enable()
    stub.Enable.assert_called_once_with(
        service_pb2.EnableRequest(), timeout=None
    )

  def test_enable_with_nondefault_timeout(self):
    stub = mock.MagicMock()
    response = service_pb2.EnableResponse()
    stub.Enable.return_value = response
    rpc_timeout = 10

    icon_client = icon_api.Client(stub, rpc_timeout=rpc_timeout)
    icon_client.enable()
    stub.Enable.assert_called_once_with(
        service_pb2.EnableRequest(), timeout=rpc_timeout
    )

  def test_disable(self):
    stub = mock.MagicMock()
    response = service_pb2.DisableResponse()
    stub.Disable.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.disable()
    stub.Disable.assert_called_once_with(
        service_pb2.DisableRequest(), timeout=None
    )

  def test_clear_faults(self):
    stub = mock.MagicMock()
    response = service_pb2.ClearFaultsResponse()
    stub.ClearFaults.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.clear_faults()
    stub.ClearFaults.assert_called_once_with(
        service_pb2.ClearFaultsRequest(), timeout=None
    )

  def test_get_operational_status(self):
    stub = mock.MagicMock()
    response = service_pb2.GetOperationalStatusResponse(
        operational_status=types_pb2.OperationalStatus(
            state=types_pb2.OperationalState.FAULTED,
            fault_reason='Jello cube is melted',
        )
    )
    stub.GetOperationalStatus.return_value = response

    icon_client = icon_api.Client(stub)
    result_status = icon_client.get_operational_status()
    self.assertEqual(result_status.state, response.operational_status.state)
    self.assertEqual(
        result_status.fault_reason, response.operational_status.fault_reason
    )
    stub.GetOperationalStatus.assert_called_once_with(
        service_pb2.GetOperationalStatusRequest(), timeout=None
    )

  @mock.patch.object(_session, 'Session', autospec=True)
  def test_start_session(self, mock_session_cls):
    """Starting a session should create the new object."""
    stub = mock.MagicMock()

    icon_client = icon_api.Client(stub)
    self.assertIsNotNone(icon_client.start_session(['foo']))
    mock_session_cls.assert_called_once_with(stub, ['foo'], None)

  @mock.patch.object(_session, 'Session', autospec=True)
  def test_start_session_with_context(self, mock_session_cls):
    """Starting a session should create the new object."""
    stub = mock.MagicMock()

    icon_client = icon_api.Client(stub)
    self.assertIsNotNone(
        icon_client.start_session(['foo'], context_pb2.Context(skill_id=123456))
    )
    mock_session_cls.assert_called_once_with(
        stub, ['foo'], context_pb2.Context(skill_id=123456)
    )

  @mock.patch.object(_session, 'Session', autospec=True)
  def test_start_session_with_context_management(self, mock_session_cls):
    """Obtaining a session with context management should succeed."""
    stub = mock.MagicMock()

    icon_client = icon_api.Client(stub)
    with icon_client.start_session(['foo']) as session:
      self.assertIsNotNone(session)
    mock_session_cls.assert_called_once_with(stub, ['foo'], None)

  @mock.patch.object(_session, 'Session', autospec=True)
  def test_start_session_error(self, mock_session_cls):
    """Errors in starting a session should be propagated."""
    stub = mock.MagicMock()
    mock_session_cls.side_effect = grpc.RpcError('uh oh')

    icon_client = icon_api.Client(stub)
    with self.assertRaises(grpc.RpcError):
      with icon_client.start_session(['foo']):
        pass
    mock_session_cls.assert_called_once_with(stub, ['foo'], None)

  def test_get_speed_override(self):
    stub = mock.MagicMock()
    response = service_pb2.GetSpeedOverrideResponse(override_factor=0.23)
    stub.GetSpeedOverride.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.get_speed_override()
    stub.GetSpeedOverride.assert_called_once()

  def test_set_speed_override(self):
    stub = mock.MagicMock()
    response = service_pb2.SetSpeedOverrideResponse()
    stub.SetSpeedOverride.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.set_speed_override(0.75)
    stub.SetSpeedOverride.assert_called_once_with(
        service_pb2.SetSpeedOverrideRequest(override_factor=0.75), timeout=None
    )

  def test_get_logging_mode(self):
    stub = mock.MagicMock()
    response = service_pb2.GetLoggingModeResponse(
        logging_mode=logging_mode_pb2.LOGGING_MODE_FULL_RATE
    )
    stub.GetLoggingMode.return_value = response

    icon_client = icon_api.Client(stub)
    self.assertEqual(
        icon_client.get_logging_mode(), logging_mode_pb2.LOGGING_MODE_FULL_RATE
    )
    stub.GetLoggingMode.assert_called_once_with(
        service_pb2.GetLoggingModeRequest(), timeout=None
    )

  def test_set_logging_mode(self):
    stub = mock.MagicMock()
    response = service_pb2.SetLoggingModeResponse()
    stub.SetLoggingMode.return_value = response

    icon_client = icon_api.Client(stub)
    icon_client.set_logging_mode(logging_mode_pb2.LOGGING_MODE_FULL_RATE)
    stub.SetLoggingMode.assert_called_once_with(
        service_pb2.SetLoggingModeRequest(
            logging_mode=logging_mode_pb2.LOGGING_MODE_FULL_RATE
        ),
        timeout=None,
    )

  def test_get_part_properties(self):
    stub = mock.MagicMock()
    part_1_properties = service_pb2.PartPropertyValues()
    part_1_properties.property_values_by_name['double_prop'].CopyFrom(
        service_pb2.PartPropertyValue(double_value=1.23)
    )
    part_1_properties.property_values_by_name['bool_prop'].CopyFrom(
        service_pb2.PartPropertyValue(bool_value=False)
    )
    expected_response = service_pb2.GetPartPropertiesResponse()
    expected_response.part_properties_by_part_name['part_1'].CopyFrom(
        part_1_properties
    )
    stub.GetPartProperties.return_value = expected_response

    icon_client = icon_api.Client(stub)
    actual_response = icon_client.get_part_properties()
    stub.GetPartProperties.assert_called_once()
    self.assertEqual(expected_response, actual_response)

  def test_set_part_properties(self):
    stub = mock.MagicMock()
    response = service_pb2.SetPartPropertiesResponse()
    stub.SetPartProperties.return_value = response

    expected_request = service_pb2.SetPartPropertiesRequest()
    part_1_properties = service_pb2.PartPropertyValues()
    part_1_properties.property_values_by_name['double_prop'].CopyFrom(
        service_pb2.PartPropertyValue(double_value=1.23)
    )
    expected_request.part_properties_by_part_name['part_1'].CopyFrom(
        part_1_properties
    )
    icon_client = icon_api.Client(stub)
    icon_client.set_part_properties({'part_1': {'double_prop': 1.23}})
    stub.SetPartProperties.assert_called_once_with(
        expected_request, timeout=None
    )


if __name__ == '__main__':
  absltest.main()
