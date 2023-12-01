# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.executive.jupyter.workcell.error_processing."""

import io
from unittest import mock

from absl.testing import absltest
from google.longrunning import operations_pb2
from google.protobuf import empty_pb2
from google.protobuf import text_format
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.logging.errors.proto import error_report_pb2
from intrinsic.solutions import error_processing


class ErrorProcessingTest(absltest.TestCase):
  """Tests that all public methods of ErrorLoader work."""

  def setUp(self):
    super().setUp()

    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.HEALTHY
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    self._error_module = error_processing.ErrorsLoader(installer_stub)

  def _create_failed_operation(self, error_reports=None):
    operation = operations_pb2.Operation(done=True)
    details_any = operation.error.details.add()
    if error_reports is not None:
      details_any.Pack(
          error_report_pb2.ErrorReports(error_reports=error_reports)
      )
    else:
      details_any.Pack(
          error_report_pb2.ErrorReports(
              error_reports=[error_report_pb2.ErrorReport()]
          )
      )
    return operation

  def test_extract_errors_returns_errors(self):
    """Tests that errors are correctly extracted."""
    error_report = text_format.Parse(
        """
        description {
          status: {
            code: 7
            message: "some message"
          }
          human_readable_summary: "some text"
        }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation([error_report, error_report])

    error_group = self._error_module.extract_error_data(operation)

    self.assertLen(error_group.errors, 2)
    self.assertEqual(error_group.errors[0].error_report_proto, error_report)
    self.assertEqual(error_group.errors[1].error_report_proto, error_report)

  def test_extract_errors_with_unhealthy_workcell(self):
    """Tests that unhealthy (pending) workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.PENDING
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    expected_substring = 'expected to become healthy again automatically'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)
    self.assertRegex(error_group.summary, expected_substring)
    self.assertRegex(error_group._repr_html_(), expected_substring)
    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_extract_errors_with_not_recoverable_workcell(self):
    """Tests that unhealthy (not recoverable) workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.ERROR
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    expected_substring = 'Try restarting'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)
    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_extract_errors_with_unavailable_workcell_status(self):
    """Tests that oes not crash on unavailable installer service."""
    installer_stub = mock.MagicMock()
    installer_stub.GetInstalledSpec.side_effect = Exception('not available')
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    expected_substring = 'Could not load the workcell status'
    self.assertRegex(error_group.workcell_health_issue, expected_substring)
    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_extract_errors_with_unknown_workcell_status(self):
    """Tests that unknown workcell status is documented."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.UNKNOWN
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    self.assertRegex(error_group.workcell_health_issue, 'Unknown')
    installer_stub.GetInstalledSpec.assert_called_once_with(empty_pb2.Empty())

  def test_extract_errors_with_healthy_workcell(self):
    """Tests that healthy workcell is detected."""
    installer_stub = mock.MagicMock()
    installer_service_response = installer_pb2.GetInstalledSpecResponse
    installer_service_response.status = (
        installer_pb2.GetInstalledSpecResponse.HEALTHY
    )
    installer_stub.GetInstalledSpec.return_value = installer_service_response
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    self.assertEmpty(error_group.workcell_health_issue)
    self.assertNotRegex(error_group.summary, 'WORKCELL NOT HEALTHY')
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
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    # Validate that an empty 'error_reason' is not surfaced.
    undesired_match = 'Error reason: '
    self.assertNotRegex(error_group.workcell_health_issue, undesired_match)

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
    operation = self._create_failed_operation()

    error_module = error_processing.ErrorsLoader(
        installer_service_stub=installer_stub
    )
    error_group = error_module.extract_error_data(operation)

    # Validate that the passed error is surfaced.
    desired_match = 'Error reason: ' + installer_service_response.error_reason
    self.assertRegex(error_group.workcell_health_issue, desired_match)

  def test_extract_errors_empty(self):
    """Tests that an empty list is returned for no errors."""
    operation = self._create_failed_operation([])

    error_group = self._error_module.extract_error_data(operation)

    self.assertEmpty(error_group.errors)

  def test_extract_errors_keeps_error_order(self):
    """Tests that errors are sorted by most recent error first."""
    error_report_1 = text_format.Parse(
        """
        description {
          human_readable_summary: "some text 1"
        }""",
        error_report_pb2.ErrorReport(),
    )
    error_report_2 = text_format.Parse(
        """
        description {
          human_readable_summary: "some text 2"
        }""",
        error_report_pb2.ErrorReport(),
    )
    error_report_3 = text_format.Parse(
        """
        description {
          human_readable_summary: "some text 3"
        }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation(
        [error_report_1, error_report_2, error_report_3]
    )

    error_group = self._error_module.extract_error_data(operation)

    self.assertIn('some text 1', error_group.errors[0].summary)
    self.assertIn('some text 2', error_group.errors[1].summary)
    self.assertIn('some text 3', error_group.errors[2].summary)

  def test_summary_string(self):
    """Tests that a summary of error reports are composed correctly."""
    error_report = text_format.Parse(
        """
        description {
          human_readable_summary: "some text"
        }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation([error_report])

    error_group = self._error_module.extract_error_data(operation)

    self.assertRegex(error_group.summary, 'Error: some text')

  def test_prints_summary(self):
    """Tests that a summary of error reports is printed."""
    operation = self._create_failed_operation()
    error_group = self._error_module.extract_error_data(operation)

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()

    self.assertRegex(mock_stdout.getvalue(), 'Errors summary')

  def test_prints_summary_no_errors(self):
    """Tests that a summary of error reports is printed."""
    operation = self._create_failed_operation([])
    error_group = self._error_module.extract_error_data(operation)

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()

    self.assertRegex(
        mock_stdout.getvalue(), error_processing.NO_ERROR_FOUND_MSG
    )

  def test_prints_summary_as_default(self):
    """Tests that a summary of error reports is printed."""
    operation = self._create_failed_operation()
    error_group = self._error_module.extract_error_data(operation)

    mock_stdout = io.StringIO()
    with mock.patch('sys.stdout', mock_stdout):
      error_group.print_info()

    self.assertRegex(mock_stdout.getvalue(), 'Errors summary')

  def test_html_from_error_group(self):
    """Tests that expected HTML code is generated for ErrorGroup."""
    error_report = text_format.Parse(
        """
        description {
          status: {
            code: 7
            message: "some message"
          }
          human_readable_summary: "some text"
        }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation([error_report])
    error_group = self._error_module.extract_error_data(operation)

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
    error_report_skill = text_format.Parse(
        """
        description {
          status: {
            code: 7
            message: "some message"
          }
          human_readable_summary: "skill error summary"
        }""",
        error_report_pb2.ErrorReport(),
    )
    error_report_subskill = text_format.Parse(
        """
        description {
          status: {
            code: 7
            message: "some other message"
          }
          human_readable_summary: "subskill error summary"
        }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation(
        [error_report_skill, error_report_subskill]
    )
    error_group = self._error_module.extract_error_data(operation)

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
    error_report = text_format.Parse(
        """
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
          }""",
        error_report_pb2.ErrorReport(),
    )
    operation = self._create_failed_operation([error_report])
    error_group = self._error_module.extract_error_data(operation)

    html_text = error_group._repr_html_()

    self.assertRegex(html_text, "<img src='data:image/png;base64")

  def test_additional_information_filter(self):
    """Tests that error messages are filtered by the information they provide."""
    skill_error = error_processing.ErrorInstance(
        text_format.Parse(
            """
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
            }""",
            error_report_pb2.ErrorReport(),
        )
    )

    self.assertTrue(skill_error.additional_information(skill_error))

    no_recovery_error = error_processing.ErrorInstance(
        text_format.Parse(
            """
            description {
              status: {
                message: "foo"
              }
              human_readable_summary: "skill error summary"
            }""",
            error_report_pb2.ErrorReport(),
        )
    )

    self.assertFalse(skill_error.additional_information(no_recovery_error))

    different_recovery_error = error_processing.ErrorInstance(
        text_format.Parse(
            """
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
            }""",
            error_report_pb2.ErrorReport(),
        )
    )
    self.assertTrue(
        skill_error.additional_information(different_recovery_error)
    )

    same_recovery_error = error_processing.ErrorInstance(
        text_format.Parse(
            """
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
            }""",
            error_report_pb2.ErrorReport(),
        )
    )
    self.assertFalse(skill_error.additional_information(same_recovery_error))

    different_data_error = error_processing.ErrorInstance(
        text_format.Parse(
            """
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
            }""",
            error_report_pb2.ErrorReport(),
        )
    )
    self.assertTrue(skill_error.additional_information(different_data_error))


if __name__ == '__main__':
  absltest.main()
