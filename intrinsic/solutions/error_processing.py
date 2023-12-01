# Copyright 2023 Intrinsic Innovation LLC

"""Module for extracting ErrorReports and presenting to user."""

import enum
import html
from typing import Any, List, Sequence

from google.longrunning import operations_pb2
from google.protobuf import empty_pb2
from google.rpc import code_pb2
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2_grpc
from intrinsic.logging.errors.proto import error_report_pb2
from intrinsic.perception.proto import frame_pb2
from intrinsic.solutions import camera_utils
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import ipython


ERROR_SEPARATOR = '\n\n========\n'
NO_ERROR_FOUND_MSG = 'No error data found.'
_ERROR_REPORT_EVENT_SOURCE = 'error_report'
_COLLAPSIBLE_ERROR_HEADER_HTML = """<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.error-header {
  background-color: #f1f1f1;
  color: #900;
  padding: 8px;
  width: 100%;
  box-sizing: border-box;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.error-content {
  padding: 0 18px;
  display: block;
  overflow: hidden;
  background-color: #f1f1f1;
}

.multiline {
  white-space: pre-wrap;
}

.collapsible {
  background-color: #900;
  color: white;
  cursor: pointer;
  padding: 18px;
  width: 100%;
  box-sizing: border-box;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.collapsible-internal {
  background-color: #777;
  color: white;
  cursor: pointer;
  padding: 1px;
  width: 100%;
  box-sizing: border-box;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.active, .collapsible:hover {
  background-color: #300;
}

.active, .collapsible-internal:hover {
  background-color: #300;
}

.content {
  padding: 0 18px;
  display: none;
  overflow: hidden;
  background-color: #f1f1f1;
}
</style>
</head>"""
_ERROR_INTRO_HTML = """
<legend style="color:#900; font-weight: bold">Errors summary:</legend>"""
_COLLAPSIBLE_SCRIPT_HTML = """<script>
var coll = document.getElementsByClassName("collapsible");
var coll_internal = document.getElementsByClassName("collapsible-internal");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
for (i = 0; i < coll_internal.length; i++) {
  coll_internal[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
</script>"""


def _error_recovery_instructions_list_html(err: 'ErrorInstance') -> str:
  """Converts all recovery instructions into a human readable html list.

  Args:
    err: Error to retrieve instructions from.

  Returns:
    html string representation of error recovery instructions
  """
  if not err.recovery_instructions:
    return ''

  recovery_instructions = '<ul>'
  for instruction in err.recovery_instructions:
    recovery_instructions += f'<li>{instruction.human_readable}</li>'
  recovery_instructions += '</ul>'

  images = ''

  for d in err.data:
    if d.data and d.data.type_url:
      if frame_pb2.Frame.DESCRIPTOR.full_name in d.data.type_url:
        frame = camera_utils.get_frame_from_any(d.data)
        img = camera_utils.get_encoded_frame(frame)
        images += f"<img src='data:image/png;base64,{img}'/>"

  return (
      '<br>'
      '  <strong>Recovery Instructions:</strong>'
      f'     {recovery_instructions}'
      f'     {images}'
  )


def _error_to_html(err: 'ErrorInstance') -> str:
  summary = html.escape(err.human_readable_summary.replace('\n', '<br>'))
  error_message = html.escape(err.error_message)
  recovery_instructions = _error_recovery_instructions_list_html(err)

  return (
      '<div class="error-header">'
      f'  <strong>{summary}</strong>'
      '</div>'
      '<div class="error-content"><p><pre class="proto">'
      f'  <div style="margin-left: 1em;">{error_message}</div>'
      f'  {recovery_instructions}'
      '</pre></p>'
      '</div>'
  )


class PrintLevel(enum.Enum):
  """Config for how much detail is printed about errors."""

  OFF = 1  # No printing done.
  SUMMARY = 2  # Only a short summary about the error is printed.


class ErrorInstance:
  """ErrorReport augmented by further insights from error processing."""

  def __init__(self, error_report: error_report_pb2.ErrorReport):
    """Constructs an ErrorInstance object.

    Args:
      error_report: ErrorReport proto for this ErrorInstance.
    """
    self._error_report_proto: error_report_pb2.ErrorReport = error_report

  def __str__(self) -> str:
    return f"{self.summary}\n\n For more details use the 'details' property."

  @property
  def error_report_proto(self) -> error_report_pb2.ErrorReport:
    return self._error_report_proto

  @property
  def summary(self) -> str:
    """String representing a summary view on the error summary.

    Returns:
      String representing the summary
    """
    return (
        f'Error: {self.human_readable_summary} \nError Status:  '
        f' {code_pb2.Code.Name(self.error_report_proto.description.status.code)}\n'
        f'  Message: {self.error_message}'
    )

  @property
  def human_readable_summary(self) -> str:
    """String representing the human readable summary of the error.

    Returns:
      String representing the human readable summary
    """
    return self.error_report_proto.description.human_readable_summary

  @property
  def error_message(self) -> str:
    """String representing the error message.

    Returns:
      String representing the error message
    """
    return self.error_report_proto.description.status.message

  @property
  def recovery_instructions(self) -> Sequence[Any]:
    """Retrieves list of recovery instructions for this error.

    Returns:
      List of recovery instructions
    """
    return self.error_report_proto.instructions.items

  @property
  def data(self) -> Sequence[Any]:
    """Retrieves list of additional data for this error.

    Returns:
      List of additional data
    """
    return self.error_report_proto.data.items

  def additional_information(self, e: 'ErrorInstance') -> bool:
    """Checks whether additional information is provided by given error.

    Args:
      e: Error to compare for information

    Returns:
      False if given error does not provide additional Information
    """
    if self == e:
      return True
    if self.error_message == e.error_message:
      if self.recovery_instructions and not e.recovery_instructions:
        return False
      if self.recovery_instructions == e.recovery_instructions:
        if self.data and not e.data or self.data == e.data:
          return False
    return True


class ErrorGroup:
  """List of error summaries with utilities.

  Attributes: errors
    workcell_health_issue: Empty if the workcell was healthy when this object
      was constructed, otherwise a description of the health status.
  """

  def __init__(
      self, errors: List[ErrorInstance], workcell_health_issue: str = ''
  ):
    """Constructs an ErrorGroup object.

    Args:
      errors: List of ErrorInstance objects.
      workcell_health_issue: Empty if the workcell is healthy when this object
        is constructed, otherwise a description of the health status.
    """
    self._errors: List[ErrorInstance] = errors
    self.workcell_health_issue: str = workcell_health_issue

  def __str__(self) -> str:
    return self.summary

  @property
  def errors(self) -> List[ErrorInstance]:
    return self._errors

  @property
  def summary(self) -> str:
    """String representing a summary view on the error summaries.

    Returns:
      String representing the summary view
    """
    result = ''
    if self.workcell_health_issue:
      result += self.workcell_health_issue
    if not self.errors:
      result += NO_ERROR_FOUND_MSG
    else:
      result += '\n===Errors summary:===\n'
      result += ERROR_SEPARATOR.join([e.summary for e in self.errors])
    return result

  def print_info(self, print_level: PrintLevel = PrintLevel.SUMMARY) -> None:
    """Print information about errors.

    Args:
      print_level: Config for how much detail is printed.
    """
    if print_level is PrintLevel.OFF:
      return
    elif print_level is PrintLevel.SUMMARY:
      print(self.summary)
    else:
      raise solutions_errors.InvalidArgumentError(
          f'Unknown PrintLevel: {print_level} (value = {print_level.value})'
      )

  def display_only_in_ipython(self) -> None:
    """Display an object but only if running in IPython."""
    ipython.display_html_if_ipython(self._repr_html_(), newline_after_html=True)

  def _get_unique_errors(self) -> List[ErrorInstance]:
    """Returns all unique errors.

    Removes errors that do not provide additional information.

    Returns:
      List of unique errors.
    """
    keep = []
    for e in self._errors:
      keep.append(e)
      for x in self._errors:
        if x not in keep:
          break
        if not e.additional_information(x):
          keep.remove(x)
        elif not x.additional_information(e):
          keep.remove(e)
          break

    return keep

  def _repr_html_(self) -> str:
    """Used to display rich information about errors in a Jupyter notebook.

    In a Jupyter notebook display(<this_object>) will render this HTML.

    Returns:
      Rich html representation of errors.
    """

    errors_repr = [_error_to_html(err) for err in self._get_unique_errors()]

    if self.errors:
      body = f"""
 <fieldset>
 {_ERROR_INTRO_HTML}
 {html.escape(self.workcell_health_issue)}
 {"".join(errors_repr)}
 </fieldset>
 {_COLLAPSIBLE_SCRIPT_HTML}
 """
    else:
      body = 'No errors found.'

    return f"""{_COLLAPSIBLE_ERROR_HEADER_HTML}
                <body>
                  {body}
                </body>"""


class ErrorsLoader:
  """Extracts error reports and prepares for presentation to user.

  ErrorReports are structured data which is logged by various intrinsic
  components at runtime and then returned by the Executive as part of a failed
  operation.
  """

  def __init__(
      self,
      installer_service_stub: installer_pb2_grpc.InstallerServiceStub,
  ):
    """Constructs an Entity object.

    Args:
      installer_service_stub: Installer service to check the workcell health.
    """
    self._installer_service_stub: installer_pb2_grpc.InstallerServiceStub = (
        installer_service_stub
    )

  def extract_error_data(
      self, failed_operation: operations_pb2.Operation
  ) -> ErrorGroup:
    """Extract all error reports from a failed operation.

    Args:
      failed_operation: The failed operation.

    Returns:
      An ErrorGroup containing all the error reports or an empty ErrorGroup if
      the given operation does not contain any error reports.
    """
    error_reports = error_report_pb2.ErrorReports()
    if failed_operation.HasField('error'):
      for detail_any in failed_operation.error.details:
        if detail_any.Unpack(error_reports):
          # The executive returns at most one ErrorReports instance in the error
          # details of a failed operation, so we can break here.
          break

    return ErrorGroup(
        [
            ErrorInstance(error_report)
            for error_report in error_reports.error_reports
        ],
        workcell_health_issue=self._load_workcell_health(),
    )

  def _load_workcell_health(self) -> str:
    """Loads the workcell health and returns an error message if not healthy.

    No retries, to avoid blocking the summary of errors.

    Returns:
      Empty if healthy, description otherwise.
    """
    try:
      response = self._installer_service_stub.GetInstalledSpec(
          empty_pb2.Empty()
      )
      error_reason = ''
      if isinstance(response.error_reason, str) and response.error_reason:
        error_reason = '\n\tError reason: ' + response.error_reason
      if response.status == installer_pb2.GetInstalledSpecResponse.HEALTHY:
        return ''
      elif response.status == installer_pb2.GetInstalledSpecResponse.PENDING:
        return (
            'WORKCELL NOT HEALTHY: Workcell backends not healthy now but '
            'expected to become healthy again automatically.'
            + error_reason
            + '\n'
        )
      elif response.status == installer_pb2.GetInstalledSpecResponse.ERROR:
        return (
            'WORKCELL NOT HEALTHY: Workcell backend is unhealthy and not '
            'expected to recover without intervention. Try restarting your '
            'app.'
            + error_reason
            + '\n'
        )
    except Exception:  # pylint: disable=broad-except
      return 'WORKCELL HEALTH UNKNOWN: Could not load the workcell status.\n'
    return (
        'WORKCELL HEALTH UNKNOWN: Unknown health status of workcell detected.\n'
    )
