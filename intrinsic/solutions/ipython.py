# Copyright 2023 Intrinsic Innovation LLC

"""Provides access to the IPython environment.

Provides meaningful fallback behavior if IPython is not present, e.g., if we are
running in a regular Python script.

Imports for IPython modules in this file have to be done on-the-fly and behind
'running_in_ipython()' checks. There is no build dependency on
//third_party/py/IPython, but imports for IPython modules will be successful
when running in an IPython enabled runtime such as our Jupyter container.
"""

import builtins
import textwrap
from typing import Any

from intrinsic.util.status import status_exception
import ipywidgets as widgets


def running_in_ipython() -> bool:
  """Returns true if we are running in an IPython environment."""
  return hasattr(builtins, '__IPYTHON__')


def _display_html(html: str, newline_after_html: bool = False) -> None:
  """Displays the given HTML via IPython.

  Assumes that 'running_in_ipython()' is True, otherwise has no effect.

  Args:
      html: HTML string to display.
      newline_after_html: Whether to print a newline after the html for spatial
        separation from followup content.
  """
  try:
    # pytype: disable=import-error
    # pylint: disable=g-import-not-at-top
    from IPython.core import display
    # pytype: enable=import-error
    # pylint: enable=g-import-not-at-top
    display.display(display.HTML(html))
    if newline_after_html:
      print('\n')  # To separate spacially from followup content.
  except ImportError:
    pass


def display_html_if_ipython(
    html: str, newline_after_html: bool = False
) -> None:
  """Displays the given HTML if running in IPython.

  Args:
      html: HTML string to display if running in IPython.
      newline_after_html: Whether to print a newline after the html for spatial
        separation from followup content. Has no effect if not running in
        IPython.
  """
  if running_in_ipython():
    _display_html(html, newline_after_html)
  else:
    print('Display only executed in IPython.')


def _create_extended_status_widget(
    extended_status_error: status_exception.ExtendedStatusError,
) -> None:
  """Generates a widget for the extended status recursively.

  Args:
    extended_status_error: Extended status error to display.

  Returns:
    Widget that can be displayed in Jupyter.
  """
  box_children = []

  if extended_status_error.title:
    box_children.append(
        widgets.HTML(f'<b>Title</b>: {extended_status_error.title}')
    )

  status_code = extended_status_error.status_code
  box_children.append(
      widgets.HTML(f'<b>StatusCode</b>: {status_code[0]}:{status_code[1]}')
  )
  if extended_status_error.proto.HasField('timestamp'):
    box_children.append(
        widgets.HTML(
            '<b>Timestamp</b>:'
            f' {extended_status_error.timestamp.strftime("%c")}'
        )
    )

  if (
      extended_status_error.user_report is not None
      and extended_status_error.user_report.message
  ):
    box_children.append(
        widgets.HTML(
            '<div><b>External'
            ' Report</b><br'
            f' /><pre><samp>\n{textwrap.indent(extended_status_error.user_report.message, "  ")}</samp></pre></div>\n'
        )
    )

  if (
      extended_status_error.debug_report is not None
      and extended_status_error.debug_report.message
  ):
    debug_report_widget = widgets.Accordion(
        children=[
            widgets.HTML(
                f'<div><pre><samp>{textwrap.indent(extended_status_error.debug_report.message, "  ")}<br'
                ' /></samp></pre></div>\n'
            )
        ],
        selected_index=None,
    )
    debug_report_widget.set_title(0, 'Internal Report')
    box_children.append(debug_report_widget)

  if extended_status_error.proto.context:
    context_children = []

    for context in extended_status_error.proto.context:
      context_es = status_exception.ExtendedStatusError.create_from_proto(
          context
      )
      context_children.append(_create_extended_status_widget(context_es))

    context_tabs = widgets.Tab(children=context_children)
    for i in range(len(extended_status_error.proto.context)):
      context_tabs.set_title(i, f'Context {i}')

    box_children.append(context_tabs)

  return widgets.VBox(children=box_children)


def display_extended_status_if_ipython(
    extended_status_error: status_exception.ExtendedStatusError,
) -> None:
  """Displays the given ExtendedStatus if running in IPython.

  Args:
    extended_status_error: Extended status error to display.
  """
  if running_in_ipython():
    display_if_ipython(_create_extended_status_widget(extended_status_error))


def display_if_ipython(python_object: Any) -> None:
  """Displays the given Python object if running in IPython.

  Args:
      python_object: Python object to display if running in IPython.
  """
  if running_in_ipython():
    try:
      # pytype: disable=import-error
      # pylint: disable=g-import-not-at-top
      from IPython.core import display
      # pytype: enable=import-error
      # pylint: enable=g-import-not-at-top
      display.display(python_object)
    except ImportError:
      pass
  else:
    print('Display only executed in IPython.')


def display_html_or_print_msg(
    html: str, msg: str, newline_after_html: bool = False
) -> None:
  """Displays HTML if running in IPython or else prints a message.

  Args:
      html: HTML string to display if running in IPython.
      msg: Alternative message to print if not running in IPython.
      newline_after_html: Whether to print a newline after the html for spatial
        separation from followup content. Has no effect if not running in
        IPython.
  """
  if running_in_ipython():
    _display_html(html, newline_after_html)
  else:
    print(msg)


def display_image_if_ipython(data: bytes, width: int) -> None:
  """Displays an image if running in IPython.

  Args:
    data: The raw image data or a URL or filename to load the data from. This
      always results in embedded image data.
    width: Width in pixels to which to constrain the image in html
  """

  try:
    # pytype: disable=import-error
    # pylint: disable=g-import-not-at-top
    from IPython import display
    # pytype: enable=import-error
    # pylint: enable=g-import-not-at-top
    display.display(display.Image(data=data, width=width))
  except ImportError:
    pass
