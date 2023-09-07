# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.workcell.error_processing."""

import io
from typing import List
from unittest import mock

from absl.testing import absltest
from google.protobuf import empty_pb2
from google.protobuf import text_format
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.logging.proto import log_item_pb2
from intrinsic.logging.proto import logger_service_pb2
from intrinsic.solutions import error_processing
from intrinsic.solutions import structured_logging


class ErrorProcessingTest(absltest.TestCase):
  """Tests that all public methods of ErrorLoader work."""

  def setUp(self):
    super().setUp()
    self._pb_error = text_format.Parse(
        """
        metadata {
          event_source: "error_report"
          acquisition_time: { seconds: 2147483647 }
        }
        context { executive_plan_id: 1 }
        payload { error_report {
          description {
            status: {
              code: 7
              message: "some message"
            }
            human_readable_summary: "some text"
          }
        } }""",
        log_item_pb2.LogItem(),
    )
    self._pb_skill_error = text_format.Parse(
        """
        metadata {
          event_source: "error_report"
          acquisition_time: { seconds: 2147483647 }
        }
        context { executive_plan_id: 1 skill_id:42 }
        payload { error_report {
          description {
            status: {
              message: "foo"
            }
            human_readable_summary: "skill error summary"
          }
          instructions {
            items {
              human_readable: "some specific helpful text"
            }
          }
          data {
            items {
              data {
                type_url: "type.googleapis.com/intrinsic_proto.perception.Frame"
                value: ""
              }
            }
          } } }""",
        log_item_pb2.LogItem(),
    )
    self._pb_subskill_error = text_format.Parse(
        """
        metadata {
          event_source: "error_report"
          acquisition_time: { seconds: 2147483647 }
        }
        context {
          executive_plan_id: 1
          parent_skill_id: 42
          skill_id: 43
        }
        payload { error_report {
          description {
            human_readable_summary: "subskill error summary"
          } } }""",
        log_item_pb2.LogItem(),
    )

    self._logs_stub = mock.MagicMock()

    # Needs setup with 'setup_logs_mock' before use.
    self._logs_module: structured_logging.StructuredLogs = (
        structured_logging.StructuredLogs(self._logs_stub)
    )

    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.HEALTHY
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    self._error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_stub
    )

  def _setup_logs_mock(self, data: List[log_item_pb2.LogItem]) -> None:
    """Prepared log mocking with given LogItems."""
    list_log_sources_response = logger_service_pb2.ListLogSourcesResponse()
    for item in data:
      list_log_sources_response.event_sources.append(item.metadata.event_source)
    self._logs_stub.ListLogSources.return_value = list_log_sources_response
    response = logger_service_pb2.GetLogItemsResponse()
    response.log_items.extend(data)
    self._logs_stub.GetLogItems.return_value = response

  def test_lists_errors(self):
    """Tests that errors are loaded and listed."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    self.assertEqual(error_group.errors[0].log_item_proto, self._pb_error)
    self.assertEqual(error_group.errors[1].log_item_proto, self._pb_error)

  def test_lists_errors_with_unhealthy_workcell(self):
    """Tests that unhealthy (pending) workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.PENDING
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    expected_substring = 'expected to become healthy again automatically'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)
    self.assertRegex(error_group.summary, expected_substring)
    self.assertRegex(error_group.details, expected_substring)
    self.assertRegex(error_group._repr_html_(), expected_substring)

    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_lists_errors_with_not_recoverable_workcell(self):
    """Tests that unhealthy (not recoverable) workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.ERROR
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    expected_substring = 'Try restarting'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)

    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_lists_errors_with_unavailable_workcell_status(self):
    """Tests that oes not crash on unavailable installer service."""
    installer_stub = mock.MagicMock()
    installer_stub.GetInstalledSpec.side_effect = Exception('not available')

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    expected_substring = 'Could not load the workcell status'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)

    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_lists_errors_with_unknown_workcell_status(self):
    """Tests that unknown workcell status is documented."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.UNKNOWN
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    self.assertRegex(error_group.workcell_health_issue, 'Unknown')

    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_lists_errors_with_healthy_workcell(self):
    """Tests that healthy workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.HEALTHY
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)
    self.assertEmpty(error_group.workcell_health_issue)
    self.assertNotRegex(error_group.summary, 'WORKCELL NOT HEALTHY')
    self.assertNotRegex(error_group.details, 'WORKCELL NOT HEALTHY')
    self.assertNotRegex(error_group._repr_html_(), 'WORKCELL NOT HEALTHY')

    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_handle_empty_error_reason(self):
    """Tests that healthy workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.PENDING
    )
    # Here, we inject an empty string.
    installer_service_response.error_reason = ''
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)

    # Validate that an empty 'error_reason' is not surfaced.
    undesired_match = 'Error reason: '
    self.assertNotRegex(error_group.workcell_health_issue, undesired_match)
    self.assertNotRegex(error_group.details, undesired_match)
    self.assertNotRegex(error_group.details, undesired_match)

  def test_handle_error_reason(self):
    """Tests that healthy workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.PENDING
    )
    # Here, we inject an empty string.
    installer_service_response.error_reason = 'this is the error'
    installer_stub.GetInstalledSpec.return_value = installer_service_response

    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_module = error_processing.ErrorsLoader(
        self._logs_module, installer_service_stub=installer_stub
    )
    error_group = error_module.list_error_data()
    self.assertLen(error_group.errors, 2)

    # Validate that the passed error is surfaced.
    desired_match = 'Error reason: ' + installer_service_response.error_reason
    self.assertRegex(error_group.workcell_health_issue, desired_match)
    self.assertRegex(error_group.details, desired_match)
    self.assertRegex(error_group.details, desired_match)

  def test_lists_errors_empty(self):
    """Tests that an empty list is returned for no errors."""
    self._setup_logs_mock([])
    self.assertEmpty(self._error_module.list_error_data().errors)

  def test_lists_errors_sorts(self):
    """Tests that errors are sorted by most recent error first."""
    first_error = log_item_pb2.LogItem()
    first_error.CopyFrom(self._pb_error)
    first_error.metadata.acquisition_time.seconds = 1687300000
    second_error = log_item_pb2.LogItem()
    second_error.CopyFrom(self._pb_error)
    second_error.metadata.acquisition_time.seconds = 1687300001
    third_error = log_item_pb2.LogItem()
    third_error.CopyFrom(self._pb_error)
    third_error.metadata.acquisition_time.seconds = 1687300002
    self._setup_logs_mock([second_error, third_error, first_error])

    error_group = self._error_module.list_error_data()

    self.assertEqual(
        [
            e.log_item_proto.metadata.acquisition_time.seconds
            for e in error_group.errors
        ],
        [1687300002, 1687300001, 1687300000],
    )

  def test_filtering_by_executive_plan_id(self):
    """Tests that errors can be filtered by executive plan id."""
    err_id_other = text_format.Parse(
        """
        metadata {
          event_source: "error_report"
          acquisition_time: { seconds: 2147483647 }
        }
        context { executive_plan_id: 42 }
        payload { error_report {} }""",
        log_item_pb2.LogItem(),
    )

    self._setup_logs_mock([err_id_other, self._pb_error, err_id_other])
    error_group = self._error_module.list_error_data(executive_plan_id=1)
    self.assertLen(error_group.errors, 1)
    self.assertEqual(
        error_group.errors[0].log_item_proto,
        self._pb_error,
        self._pb_error,
    )

  def test_summary_string(self):
    """Tests that a summary of error reports are composed correctly."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    self.assertRegex(error_group.summary, 'Error: some text')

  def test_prints_summary(self):
    """Tests that a summary of error reports is printed."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()
    self.assertRegex(mock_stdout.getvalue(), 'Errors summary')

  def test_prints_summary_no_errors(self):
    """Tests that a summary of error reports is printed."""
    self._setup_logs_mock([])
    error_group = self._error_module.list_error_data()
    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()
    self.assertRegex(
        mock_stdout.getvalue(), error_processing.NO_ERROR_FOUND_MSG
    )

  def test_details_string(self):
    """Tests that details of error reports are composed correctly."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    self.assertRegex(error_group.details, 'Detailed error summaries')

  def test_prints_summary_as_default(self):
    """Tests that a summary of error reports is printed."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()
    self.assertRegex(mock_stdout.getvalue(), 'Errors summary')

  def test_prints_details(self):
    """Tests that a details of error reports is printed."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info(
          print_level=error_processing.PrintLevel.FULL_ERROR_REPORT
      )
    self.assertRegex(mock_stdout.getvalue(), 'Detailed error summaries')

  def test_html_from_error_group(self):
    """Tests that expected HTML code is generated for ErrorGroup."""
    self._setup_logs_mock([self._pb_error, self._pb_error])
    error_group = self._error_module.list_error_data()
    html_text = error_group._repr_html_()
    self.assertRegex(
        html_text,
        '<div class="error-header">  <strong>some text</strong></div>',
    )
    self.assertRegex(
        html_text, '  <div style="margin-left: 1em;">some message</div>'
    )

  def test_html_for_subskill(self):
    """Tests that expected HTML code is generated for subskills."""
    self._setup_logs_mock([self._pb_skill_error, self._pb_subskill_error])
    error_group = self._error_module.list_error_data()
    html_text = error_group._repr_html_()
    self.assertRegex(
        html_text,
        (
            '<div class="error-header">  '
            '<strong>skill error summary</strong></div>'
        ),
    )
    self.assertRegex(
        html_text, '<div class="error-header">  <strong>subskill error summary'
    )

  def test_html_for_camera_frame(self):
    """Tests that expected HTML code is generated for camera frames."""
    self._setup_logs_mock([self._pb_skill_error])
    error_group = self._error_module.list_error_data()
    html_text = error_group._repr_html_()
    self.assertRegex(html_text, "<img src='data:image/png;base64")

  def test_additional_information_filter(self):
    """Tests that error messages are filtered by the information they provide."""
    skill_error_instance = error_processing.ErrorInstance(self._pb_skill_error)
    self.assertTrue(
        skill_error_instance.additional_information(skill_error_instance)
    )

    test_error_no_recovery = text_format.Parse(
        """
        metadata { event_source: "error_report" }
        context { executive_plan_id: 1 skill_id:42 }
        payload { error_report {
          description {
            status: {
              message: "foo"
            }
            human_readable_summary: "skill error summary"
          } } }""",
        log_item_pb2.LogItem(),
    )
    self.assertFalse(
        skill_error_instance.additional_information(
            error_processing.ErrorInstance(test_error_no_recovery)
        )
    )

    test_error_different_recovery = text_format.Parse(
        """
        metadata { event_source: "error_report" }
        context { executive_plan_id: 1 skill_id:42 }
        payload { error_report {
          description {
            status: {
              message: "foo"
            }
            human_readable_summary: "skill error summary"
          }
          instructions {
            items {
              human_readable: "some different helpful text"
            }
          } } }""",
        log_item_pb2.LogItem(),
    )
    self.assertTrue(
        skill_error_instance.additional_information(
            error_processing.ErrorInstance(test_error_different_recovery)
        )
    )

    test_error_same_recovery = text_format.Parse(
        """
        metadata { event_source: "error_report" }
        context { executive_plan_id: 1 skill_id:42 }
        payload { error_report {
          description {
            status: {
              message: "foo"
            }
            human_readable_summary: "skill error summary"
          }
          instructions {
            items {
              human_readable: "some specific helpful text"
            }
          } } }""",
        log_item_pb2.LogItem(),
    )
    self.assertFalse(
        skill_error_instance.additional_information(
            error_processing.ErrorInstance(test_error_same_recovery)
        )
    )

    test_error_different_data = text_format.Parse(
        """
        metadata { event_source: "error_report" }
        context { executive_plan_id: 1 skill_id:42 }
        payload { error_report {
          description {
            status: {
              message: "foo"
            }
            human_readable_summary: "skill error summary"
          }
          instructions {
            items {
              human_readable: "some specific helpful text"
            }
          }
          data {
            items {
              status: {
                message: "foo"
              }
            }
          } } }""",
        log_item_pb2.LogItem(),
    )
    self.assertTrue(
        skill_error_instance.additional_information(
            error_processing.ErrorInstance(test_error_different_data)
        )
    )


if __name__ == '__main__':
  absltest.main()
