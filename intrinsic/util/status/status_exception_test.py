# Copyright 2023 Intrinsic Innovation LLC

"""Tests for ExtendedStatusError."""

import datetime

from absl.testing import absltest
from google.protobuf import timestamp_pb2
from intrinsic.logging.proto import context_pb2
from intrinsic.solutions.testing import compare
from intrinsic.util.status import extended_status_pb2
from intrinsic.util.status import status_exception


class StatusExceptionTest(absltest.TestCase):

  def test_set_extended_status(self):
    status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(component="Comp", code=123),
        title="Title",
        internal_report=extended_status_pb2.ExtendedStatus.Report(
            message="Ext Message"
        ),
        external_report=extended_status_pb2.ExtendedStatus.Report(
            message="Int Message"
        ),
    )

    error = status_exception.ExtendedStatusError().set_extended_status(status)

    compare.assertProto2Equal(self, status, error.extended_status)

  def test_set_status_code(self):
    error = status_exception.ExtendedStatusError().set_status_code(
        "My comp", 2342
    )
    expected_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(
            component="My comp", code=2342
        )
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_set_title(self):
    error = status_exception.ExtendedStatusError().set_title("My title")
    expected_status = extended_status_pb2.ExtendedStatus(title="My title")

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_set_timestamp(self):
    error = status_exception.ExtendedStatusError().set_timestamp(
        datetime.datetime.fromtimestamp(1711552798.1, datetime.timezone.utc)
    )
    expected_status = extended_status_pb2.ExtendedStatus(
        timestamp=timestamp_pb2.Timestamp(seconds=1711552798, nanos=100000000)
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_set_internal_report_message(self):
    error = status_exception.ExtendedStatusError().set_internal_report_message(
        "Foo"
    )
    expected_status = extended_status_pb2.ExtendedStatus(
        internal_report=extended_status_pb2.ExtendedStatus.Report(
            message="Foo"
        ),
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_set_external_report_message(self):
    error = status_exception.ExtendedStatusError().set_external_report_message(
        "Bar"
    )
    expected_status = extended_status_pb2.ExtendedStatus(
        external_report=extended_status_pb2.ExtendedStatus.Report(
            message="Bar"
        ),
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_add_context(self):
    context_status = extended_status_pb2.ExtendedStatus(
        status_code=extended_status_pb2.StatusCode(component="Cont", code=123),
        title="Cont Title",
    )

    error = (
        status_exception.ExtendedStatusError()
        .set_title("Foo")
        .add_context(context_status)
    )

    expected_status = extended_status_pb2.ExtendedStatus(
        title="Foo",
        context=[context_status],
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)

  def test_set_log_context(self):
    log_context = context_pb2.Context(executive_plan_id=123)

    error = status_exception.ExtendedStatusError().set_log_context(log_context)

    expected_status = extended_status_pb2.ExtendedStatus(
        log_context=log_context
    )

    compare.assertProto2Equal(self, error.extended_status, expected_status)


if __name__ == "__main__":
  absltest.main()
