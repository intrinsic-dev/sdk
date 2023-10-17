# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.util.grpc."""

import time
from unittest import mock

from absl.testing import absltest
import grpc
from intrinsic.util.grpc import error_handling


class _GrpcError(grpc.RpcError, grpc.Call):
  """Helper class that emulates a gRPC error."""

  def __init__(self, code: int):
    self._code = code

  def code(self) -> int:
    return self._code

  def details(self):
    return '_GrpcError'


@error_handling.retry_on_grpc_unavailable
def _call_with_retry(stub) -> str:
  return stub.call()


class ErrorsTest(absltest.TestCase):

  @mock.patch.object(time, 'sleep')
  def test_retry_on_grpc_unavailable_retries_on_certain_errors(self, _):
    stub = mock.MagicMock()
    stub.call.side_effect = [
        _GrpcError(grpc.StatusCode.UNAVAILABLE),
        _GrpcError(grpc.StatusCode.UNIMPLEMENTED),
        'some result',
    ]
    result = _call_with_retry(stub)
    stub.call.assert_called_with()
    self.assertEqual(result, 'some result')

  @mock.patch.object(time, 'sleep')
  def test_retry_on_grpc_unavailable_fails_after_max_retries(self, mock_sleep):
    stub = mock.MagicMock()
    # We receive an UNAVAILABLE error when we directly try to contact a grpc
    # server that is not (yet) running.
    stub.call.side_effect = _GrpcError(grpc.StatusCode.UNAVAILABLE)
    with self.assertRaises(_GrpcError) as context:
      _call_with_retry(stub)
    self.assertEqual(context.exception.code(), grpc.StatusCode.UNAVAILABLE)
    # Stub gets called for the max number of attempts.
    self.assertEqual(stub.call.call_count, 15)
    mock_sleep.assert_has_calls([mock.call(mock.ANY)])

  def test_retry_on_grpc_unavailable_does_not_retry_on_other_grpc_error(self):
    stub = mock.MagicMock()
    stub.call.side_effect = _GrpcError(grpc.StatusCode.INVALID_ARGUMENT)
    with self.assertRaises(Exception) as context:
      _call_with_retry(stub)
    self.assertEqual(context.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
    self.assertEqual(stub.call.call_count, 1)

  def test_retry_on_grpc_unavailable_does_not_retry_on_non_grpc_error(self):
    stub = mock.MagicMock()
    stub.call.side_effect = Exception('non-grpc error')
    with self.assertRaises(Exception) as context:
      _call_with_retry(stub)
    self.assertEqual(str(context.exception), 'non-grpc error')
    self.assertEqual(stub.call.call_count, 1)


if __name__ == '__main__':
  absltest.main()
