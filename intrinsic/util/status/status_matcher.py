# Copyright 2023 Intrinsic Innovation LLC

"""Matchers for tests with ExtendedStatusError."""

import re
from typing import Callable

from intrinsic.util.status import status_exception


def matches(
    *,
    title: str | None = None,
    component: str | None = None,
    code: int | None = None,
    external_report_message: str | None = None,
    external_report_message_regex: str | None = None,
    internal_report_message: str | None = None,
    internal_report_message_regex: str | None = None,
) -> Callable[[status_exception.ExtendedStatusError], bool]:
  """Creates a test matcher for ExtendedStatusError.

  Usage example:
  with self.assertRaisesWithPredicateMatch(
      status_exception.ExtendedStatusError,
      status_matcher.matches(code=2345, external_status_message="Ext message")
  ):
      call_my_function_that_raises()

  Args:
    title: if not None, exact title match with raised exception required
    component: if not None, exact status code component match with raised
      exception required
    code: if not None, exact status code match with raised exception required
    external_report_message: if not None, exact external report message match
      with raised exception required
    external_report_message_regex: if not None, regex must match external report
      message match of raised exception required
    internal_report_message: if not None, exact internal report message match
      with raised exception required
    internal_report_message_regex: if not None, regex must match internal report
      message match of raised exception required

  Returns:
    Predicate function to be used with assertRaisesWithPredicateMatch.
  """

  def matcher(e: status_exception.ExtendedStatusError) -> bool:
    proto = e.proto

    if title is not None and title != proto.title:
      return False

    if component is not None and component != proto.status_code.component:
      return False

    if code is not None and code != proto.status_code.code:
      return False

    if (
        external_report_message is not None
        and external_report_message != proto.external_report.message
    ):
      return False

    if external_report_message_regex is not None and not re.match(
        external_report_message_regex, proto.external_report.message
    ):
      return False

    if (
        internal_report_message is not None
        and internal_report_message != proto.internal_report.message
    ):
      return False

    if internal_report_message_regex is not None and not re.match(
        internal_report_message_regex, proto.internal_report.message
    ):
      return False

    return True

  return matcher
