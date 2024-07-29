# Copyright 2023 Intrinsic Innovation LLC

"""Tests for ExtendedStatusError."""

import datetime
from typing import Optional

from absl.testing import absltest
from google.protobuf import timestamp_pb2
from google.rpc import code_pb2
from google.rpc import status_pb2
import grpc
from intrinsic.logging.proto import context_pb2
from intrinsic.solutions.testing import compare
from intrinsic.util.status import extended_status_pb2
from intrinsic.util.status import status_exception
from pybind11_abseil import status as abseil_status


class StatusExceptionTest(absltest.TestCase):

  def test_set_extended_status(self):
    status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="Cannot Overwrite", code=222
        ),
        title="Title",
        internal_report=extended_status_pb2.ExtendedStatus.Report(
            message="Ext Message"
        ),
        external_report=extended_status_pb2.ExtendedStatus.Report(
            message="Int Message"
        ),
    )

    error = status_exception.ExtendedStatusError(
        "Comp", code=123
    ).set_extended_status(status)

    # Overwriting the status code is not allowed, so the status code from
    # the proto was ignored.
    expected_status = extended_status_pb2.ExtendedStatus()
    expected_status.CopyFrom(status)
    expected_status.status_code.CopyFrom(
        extended_status_pb2.StatusCode(component="Comp", code=123)
    )

    compare.assertProto2Equal(self, expected_status, error.proto)

  def test_set_from_constructor(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        123,
        title="Title",
        external_report_message="Ext message",
        internal_report_message="Int message",
        timestamp=datetime.datetime.fromtimestamp(
            1711552798.1, datetime.timezone.utc
        ),
    )

    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        title="Title",
        external_report=extended_status_pb2.ExtendedStatus.Report(
            message="Ext message"
        ),
        internal_report=extended_status_pb2.ExtendedStatus.Report(
            message="Int message"
        ),
        timestamp=timestamp_pb2.Timestamp(seconds=1711552798, nanos=100000000),
    )

    compare.assertProto2Equal(self, error.proto, expected_status)

  def test_default_timestamp(self):
    start = datetime.datetime.now()
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        123,
    )

    self.assertGreater(error.timestamp, start)

  def test_set_status_code(self):
    error = status_exception.ExtendedStatusError("ai.testing.my_component", 123)
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        )
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_set_title(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_title("My title")
    expected_status = extended_status_pb2.ExtendedStatus(
        title="My title",
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_set_timestamp(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_timestamp(
        datetime.datetime.fromtimestamp(1711552798.1, datetime.timezone.utc)
    )
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        timestamp=timestamp_pb2.Timestamp(seconds=1711552798, nanos=100000000),
    )

    compare.assertProto2Equal(self, error.proto, expected_status)

  def test_timestamp(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_timestamp(datetime.datetime.fromtimestamp(1711552798.1))

    # No timezone here, returned timestamp is local time
    self.assertEqual(
        datetime.datetime.fromtimestamp(1711552798.1),
        error.timestamp,
    )

    self.assertEqual(
        datetime.datetime.fromtimestamp(1711552798.1, datetime.timezone.utc),
        error.timestamp.astimezone(datetime.timezone.utc),
    )

  def test_set_timestamp_default(self):
    start = datetime.datetime.now()
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_timestamp()

    self.assertGreater(error.timestamp, start)

  def test_set_internal_report_message(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_internal_report_message("Foo")
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        internal_report=extended_status_pb2.ExtendedStatus.Report(
            message="Foo"
        ),
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_set_external_report_message(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_external_report_message("Bar")
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        external_report=extended_status_pb2.ExtendedStatus.Report(
            message="Bar"
        ),
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_emit_traceback_to_internal_report(self):
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.intrinsic.my_skill", code=2342
        ),
    )

    def _function_raising_extended_status_error():
      raise status_exception.ExtendedStatusError(
          "ai.intrinsic.my_skill", 2342
      ).emit_traceback_to_internal_report()

    # cannot use self.assertRaises as that loses the __traceback__ field
    error: Optional[status_exception.ExtendedStatusError] = None
    try:
      _function_raising_extended_status_error()
    except status_exception.ExtendedStatusError as e:
      error = e

    compare.assertProto2Equal(
        self,
        error.proto,
        expected_status,
        ignored_fields=["internal_report", "timestamp"],
    )
    self.assertIn(
        "Traceback (most recent call last):",
        error.proto.internal_report.message,
    )

  def test_emit_traceback_to_internal_report_appends(self):
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.intrinsic.my_skill", code=2342
        ),
    )

    def _function_raising_extended_status_error():
      raise status_exception.ExtendedStatusError(
          "ai.intrinsic.my_skill", 2342
      ).set_internal_report_message(
          "Prior message"
      ).emit_traceback_to_internal_report()

    # cannot use self.assertRaises as that loses the __traceback__ field
    error: Optional[status_exception.ExtendedStatusError] = None
    try:
      _function_raising_extended_status_error()
    except status_exception.ExtendedStatusError as e:
      error = e

    compare.assertProto2Equal(
        self,
        error.proto,
        expected_status,
        ignored_fields=["internal_report", "timestamp"],
    )
    self.assertRegex(
        error.proto.internal_report.message,
        r"Prior message\s*Traceback \(most recent call last\):.*",
    )

  def test_add_context(self):
    context_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(component="Cont", code=234),
        title="Cont Title",
    )

    error = (
        status_exception.ExtendedStatusError("ai.testing.my_component", 123)
        .set_title("Foo")
        .add_context(context_status)
    )

    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        title="Foo",
        context=[context_status],
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_set_log_context(self):
    log_context = context_pb2.Context(executive_plan_id=123)

    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_log_context(log_context)

    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        related_to=extended_status_pb2.ExtendedStatus.Relations(
            log_context=log_context,
        ),
    )

    compare.assertProto2Equal(
        self, error.proto, expected_status, ignored_fields=["timestamp"]
    )

  def test_to_string(self):
    error = (
        status_exception.ExtendedStatusError("ai.testing.my_component", 123)
        .set_external_report_message("external message")
        .set_internal_report_message("internal message")
        .set_timestamp(
            datetime.datetime.fromtimestamp(1711552798.1, datetime.timezone.utc)
        )
    )

    expected_str = """StatusCode: ai.testing.my_component:123
Timestamp:  Wed Mar 27 15:19:58 2024
External Report:
  external message
Internal Report:
  internal message
"""

    self.assertEqual(str(error), expected_str)

  def test_grpc_status_code(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        123,
        external_report_message="external message",
    )

    self.assertEqual(error.code, grpc.StatusCode.UNKNOWN)

  def test_grpc_status_title(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        123,
        title="some title",
    )
    self.assertEqual(error.details, "some title")

  def test_grpc_status_trailing_metadata(self):
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        123,
        title="some title",
        timestamp=datetime.datetime.fromtimestamp(
            1711552798.1, datetime.timezone.utc
        ),
    )

    status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        title="some title",
        timestamp=timestamp_pb2.Timestamp(seconds=1711552798, nanos=100000000),
    )
    rpc_status = status_pb2.Status(code=code_pb2.UNKNOWN, message=status.title)
    rpc_status.details.add().Pack(status)

    self.assertEqual(
        error.trailing_metadata,
        (("grpc-status-details-bin", rpc_status.SerializeToString()),),
    )

  def test_backward_compatible_code_resolved(self):
    # The following assumes that a legacy status was automatically converted
    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component",
        # The following mimics that the code was retrieved from Abseil
        abseil_status.StatusCodeAsInt(
            abseil_status.StatusCode.INVALID_ARGUMENT
        ),
        title="My title",
        timestamp=datetime.datetime.fromtimestamp(
            1711552798.1, datetime.timezone.utc
        ),
    )

    # At this time, it should already have been converted to the grpc code
    self.assertEqual(error.code, grpc.StatusCode.INVALID_ARGUMENT)

    rpc_status = status_pb2.Status()
    rpc_status.ParseFromString(error.trailing_metadata[0][1])

    # Here is the google rpc code that was written to the proto
    expected_status = status_pb2.Status(
        code=code_pb2.INVALID_ARGUMENT, message="My title"
    )
    expected_status.details.add().Pack(
        extended_status_pb2.ExtendedStatus(
            status_code=extended_status_pb2.StatusCode(
                component="ai.testing.my_component",
                code=code_pb2.INVALID_ARGUMENT,
            ),
            title="My title",
            timestamp=timestamp_pb2.Timestamp(
                seconds=1711552798, nanos=100000000
            ),
        ),
    )
    compare.assertProto2Equal(self, rpc_status, expected_status)


if __name__ == "__main__":
  absltest.main()
