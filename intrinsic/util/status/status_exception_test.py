# Copyright 2023 Intrinsic Innovation LLC

"""Tests for ExtendedStatusError."""

import datetime
from typing import Optional

from absl.testing import absltest
from google.protobuf import timestamp_pb2
from intrinsic.logging.proto import context_pb2
from intrinsic.solutions.testing import compare
from intrinsic.util.status import extended_status_pb2
from intrinsic.util.status import status_exception


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

  def test_set_status_code(self):
    error = status_exception.ExtendedStatusError("ai.testing.my_component", 123)
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        )
    )

    compare.assertProto2Equal(self, error.proto, expected_status)

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

    compare.assertProto2Equal(self, error.proto, expected_status)

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

    compare.assertProto2Equal(self, error.proto, expected_status)

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

    compare.assertProto2Equal(self, error.proto, expected_status)

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
        self, error.proto, expected_status, ignored_fields=["internal_report"]
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
        self, error.proto, expected_status, ignored_fields=["internal_report"]
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

    compare.assertProto2Equal(self, error.proto, expected_status)

  def test_set_log_context(self):
    log_context = context_pb2.Context(executive_plan_id=123)

    error = status_exception.ExtendedStatusError(
        "ai.testing.my_component", 123
    ).set_log_context(log_context)

    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="ai.testing.my_component", code=123
        ),
        log_context=log_context,
    )

    compare.assertProto2Equal(self, error.proto, expected_status)

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


if __name__ == "__main__":
  absltest.main()
