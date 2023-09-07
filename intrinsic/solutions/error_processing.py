# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Module for extracting ErrorReports and presenting to user."""

import enum
import html
from typing import Any, List, Optional, Sequence, Tuple

from google.protobuf import empty_pb2
from google.protobuf import text_format
from google.rpc import code_pb2
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2_grpc
from intrinsic.logging.proto import log_item_pb2
from intrinsic.perception.proto import frame_pb2
from intrinsic.solutions import camera_utils
from intrinsic.solutions import errors as solutions_errors
from intrinsic.solutions import ipython
from intrinsic.solutions import structured_logging

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


def _error_to_collapsible_button_html(
    err: 'ErrorInstance',
    internal_errors: Optional[List['ErrorInstance']] = None,
) -> str:
  """Prepares html for an interactive button for an error.

  Args:
    err: Error summary
    internal_errors: Optional. Additional errors nested under this error.

  Returns:
    html representation for interactive error button.
  """
  summary = html.escape(err.human_readable_summary.replace('\n', '<br>'))
  error_message = html.escape(err.error_message)

  # Internal errors are represented as buttons that are only visible when the
  # parent error is uncollapsed.
  internal_buttons_html = ''
  if internal_errors:
    internal_buttons = [
        _error_to_collapsible_button_html(e) for e in internal_errors
    ]
    internal_buttons_html = ''.join(internal_buttons)

  recovery_instructions = _error_recovery_instructions_list_html(err)

  return (
      '<div class="error-header">'
      f'  <strong>{summary}</strong>'
      '</div>'
      '<div class="error-content"><p><pre class="proto">'
      f'  <div style="margin-left: 1em;">{error_message}</div>'
      f'  {recovery_instructions}'
      f'  {internal_buttons_html}'
      '</pre></p>'
      '</div>'
  )


class PrintLevel(enum.Enum):
  """Config for how much detail is printed about errors."""

  OFF = 1  # No printing done.
  SUMMARY = 2  # Only a short summary about the error is printed.
  FULL_ERROR_REPORT = 3  # The full proto ErrorReport is printed.


class ErrorInstance:
  """ErrorReport augmented by further insights from error processing.

  Attributes: log_item_proto
    uid: LogItem unique ID of error.
    parent_error_uid: Set if this error happened in the scope of an error of a
      higher-level component. The UID is the LogItem UID of the parent.
  """

  def __init__(self, log_item: log_item_pb2.LogItem):
    """Constructs an ErrorInstance object.

    Args:
      log_item: LogItem proto for this ErrorInstance.
    """
    self._log_item_proto: log_item_pb2.LogItem = log_item

    # Set if this error happened in the scope of an error of a higher-level
    # component. The UID is the LogItem UID of the parent.
    self.parent_error_uid: Optional[int] = None

  def __str__(self) -> str:
    return f"{self.summary}\n\n For more details use the 'details' property."

  @property
  def uid(self) -> int:
    """LogItem unique ID of error."""
    return self._log_item_proto.metadata.uid

  @property
  def log_item_proto(self) -> log_item_pb2.LogItem:
    return self._log_item_proto

  @property
  def summary(self) -> str:
    """String representing a summary view on the error summary.

    Returns:
      String representing the summary
    """
    return (
        f'Error: {self.human_readable_summary} \nError Status:  '
        f' {code_pb2.Code.Name(self.log_item_proto.payload.error_report.description.status.code)}\n'
        f'  Message: {self.error_message}'
    )

  @property
  def details(self) -> str:
    """String representing a detailed view on the error summary.

    Returns:
      String representing the details
    """
    return (
        f'{self.summary}\n\nFull LogItem:\n'
        f'{text_format.MessageToString(self.log_item_proto)}'
    )

  @property
  def human_readable_summary(self) -> str:
    """String representing the human readable summary of the error.

    Returns:
      String representing the human readable summary
    """
    return (
        self.log_item_proto.payload.error_report.description.human_readable_summary
    )

  @property
  def error_message(self) -> str:
    """String representing the error message.

    Returns:
      String representing the error message
    """
    return self.log_item_proto.payload.error_report.description.status.message

  @property
  def recovery_instructions(self) -> Sequence[Any]:
    """Retrieves list of recovery instructions for this error.

    Returns:
      List of recovery instructions
    """
    return self.log_item_proto.payload.error_report.instructions.items

  @property
  def data(self) -> Sequence[Any]:
    """Retrieves list of additional data for this error.

    Returns:
      List of additional data
    """
    return self.log_item_proto.payload.error_report.data.items

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

    # We reverse to order to show the most recent error first.
    def negative_acquisition_time(e: ErrorInstance) -> Tuple[int, int]:
      return (
          -e.log_item_proto.metadata.acquisition_time.seconds,
          -e.log_item_proto.metadata.acquisition_time.nanos,
      )

    self._errors.sort(key=negative_acquisition_time)

    self._process_error_hierarchy()
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

  @property
  def details(self) -> str:
    """String representing a detailed view on the error summaries.

    Returns:
      String representing the details including the full ErrorReport proto.
    """
    result = ''
    if self.workcell_health_issue:
      result += self.workcell_health_issue
    if not self.errors:
      result += NO_ERROR_FOUND_MSG
    else:
      result += '\nDetailed error summaries:\n'
      result += ERROR_SEPARATOR.join([e.details for e in self.errors])
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
    elif print_level is PrintLevel.FULL_ERROR_REPORT:
      print(self.details)
    else:
      raise solutions_errors.InvalidArgumentError(
          f'Unknown PrintLevel: {print_level} (value = {print_level.value})'
      )

  def display_only_in_ipython(self) -> None:
    """Display an object but only if running in IPython."""
    ipython.display_html_if_ipython(self._repr_html_(), newline_after_html=True)

  def _process_error_hierarchy(self) -> None:
    """Extracts hierarchical relationships between instances in self.errors.

    The results are stores within the error instances.
    """
    for err in self.errors:
      # Process subskill invocations. A subskill is expected to contain the ID
      # of its parent skill error in its LogItem context.
      if err.log_item_proto.context.parent_skill_id != 0:
        # Note that we currently assume only one nesting level.
        def is_parent(
            parent: ErrorInstance, child: ErrorInstance = err
        ) -> bool:
          """Evaluates whether 'child' is a child of 'parent'."""
          return parent.log_item_proto.context.parent_skill_id == 0 and (
              parent.log_item_proto.context.skill_id
              == child.log_item_proto.context.parent_skill_id
          )

        potential_parents = list(filter(is_parent, self.errors))
        if len(potential_parents) == 1:
          err.parent_error_uid = potential_parents[0].uid
        else:
          print(
              'Warning: Unexpected parent relationship of the error with UID'
              f' {err.uid}. Expected 1 parent but found '
              f'{len(potential_parents)}.'
          )

  def _get_top_level_errors(self) -> List[ErrorInstance]:
    """Returns all errors which are not nested below another parent error.

    Returns:
      List of errors which do not have child errors.
    """
    return list(filter(lambda err: not err.parent_error_uid, self.errors))

  def _get_children(self, uid: int) -> List[ErrorInstance]:
    """Returns all errors that are nested below a given error.

    Args:
      uid: LogItem UID of error.

    Returns:
      List children.
    """
    return list(
        filter(
            lambda e: e.parent_error_uid and e.parent_error_uid == uid,
            self.errors,
        )
    )

  def _get_unique_top_level_errors(self) -> List[ErrorInstance]:
    """Returns all errors which are not nested below another parent error.

    Additionally removes errors which group other top-level errors.

    Returns:
      List of unique errors which do not have child errors.
    """
    top_level_errors = self._get_top_level_errors()

    keep = []
    for e in top_level_errors:
      keep.append(e)
      for x in top_level_errors:
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

    errors_repr = [
        _error_to_collapsible_button_html(
            err, internal_errors=self._get_children(err.uid)
        )
        for err in self._get_unique_top_level_errors()
    ]

    body = ''
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
  components at
  runtime. This class uses the DataLogger as the backend storing the reports. It
  is both used as an internal helper class within workcell client modules to
  expose errors, as well as a separate module by the user.
  """

  def __init__(
      self,
      structured_logs: structured_logging.StructuredLogs,
      installer_service_stub: installer_pb2_grpc.InstallerServiceStub,
  ):
    """Constructs an Entity object.

    Note that already during construction, we fetch the list of children and
    cache them.

    Args:
      structured_logs: DataLogger client.
      installer_service_stub: Installer service to check the workcell health.
    """
    self._structured_logs: structured_logging.StructuredLogs = structured_logs
    self._installer_service_stub: installer_pb2_grpc.InstallerServiceStub = (
        installer_service_stub
    )

  def list_error_data(
      self,
      executive_plan_id: Optional[int] = None,
      last_seconds_to_read: int = 1200,
  ) -> ErrorGroup:
    """Load all ErrorReports for a given plan execution.

    This call might take a few seconds as data needs to be loaded from the
    backend.

    Note that currently only data for the last 6 hours is stored on prem. By
    default only the last 20 min are considered. If you have a longer execution
    or would like to load errors from executions in the past, adjust
    'last_seconds_to_read'.

    Args:
      executive_plan_id: Optional Log ID of the plan to consider. Can be e.g.
        found in ExecutiveState.
      last_seconds_to_read: Only considers recent logs within this timeframe

    Returns:
      List of LogItems containing metadata and the ErrorReport payload
    """
    print('Reading error reports...', end='')
    log_items = self._structured_logs.query(
        _ERROR_REPORT_EVENT_SOURCE, last_seconds_to_read
    )
    print('Done.')
    if not log_items:
      return ErrorGroup([], workcell_health_issue=self._load_workcell_health())
    if not executive_plan_id:
      return ErrorGroup(
          [ErrorInstance(proto) for proto in log_items],
          workcell_health_issue=self._load_workcell_health(),
      )
    log_item_proto_list = list(
        filter(
            lambda item: item.context.executive_plan_id == executive_plan_id,
            log_items,
        )
    )
    return ErrorGroup(
        [ErrorInstance(proto) for proto in log_item_proto_list],
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
