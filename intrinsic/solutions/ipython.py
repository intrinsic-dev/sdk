# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides access to the IPython environment.

Provides meaningful fallback behavior if IPython is not present, e.g., if we are
running in a google3 Python runtime.

Imports for IPython modules in this file have to be done on-the-fly and behind
'_running_in_ipython()' checks, which prevents them from being executed in a
google3 Python runtime. There is no build dependency on
//third_party/py/IPython, but imports for IPython modules will be successful
when running in an IPython enabled runtime such as our Jupyter container.
"""

import builtins
from typing import Any


def _running_in_ipython() -> bool:
  """Returns whether we are running in an IPython environment.

  Will return False when running in a google3 Python runtime.
  """
  return hasattr(builtins, '__IPYTHON__')


def _display_html(html: str, newline_after_html: bool) -> None:
  """Displays the given HTML via IPython.

  Assumes that '_running_in_ipython()' is True, otherwise has no effect.

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
  if _running_in_ipython():
    _display_html(html, newline_after_html)
  else:
    print('Display only executed in IPython.')


def display_if_ipython(python_object: Any) -> None:
  """Displays the given Python object if running in IPython.

  Args:
      python_object: Python object to display if running in IPython.
  """
  if _running_in_ipython():
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
  if _running_in_ipython():
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
