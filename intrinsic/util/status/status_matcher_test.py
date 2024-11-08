# Copyright 2023 Intrinsic Innovation LLC

"""Tests extended status matcher."""

from absl.testing import absltest
from intrinsic.util.status import status_exception
from intrinsic.util.status import status_matcher


class StatusMatcherTest(absltest.TestCase):

  def test_matcher_component_and_code(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(component="ai.testing.my_component", code=123),
    ):
      raise status_exception.ExtendedStatusError("ai.testing.my_component", 123)

  def test_matcher_component_and_code_mismatch(self):
    self.assertFalse(
        status_matcher.matches(component="ai.testing.my_component", code=123)(
            status_exception.ExtendedStatusError(
                "ai.testing.other_component", 123
            )
        )
    )
    self.assertFalse(
        status_matcher.matches(component="ai.testing.my_component", code=123)(
            status_exception.ExtendedStatusError("ai.testing.my_component", 432)
        )
    )

  def test_matcher_title(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(title="My Title"),
    ):
      raise status_exception.ExtendedStatusError(
          "ai.testing.my_component", 123, title="My Title"
      )

  def test_matcher_title_mismatch(self):
    self.assertFalse(
        status_matcher.matches(
            component="ai.testing.my_component", code=123, title="My title"
        )(
            status_exception.ExtendedStatusError(
                "ai.testing.other_component", 123, title="Other title"
            )
        )
    )

  def test_matcher_user_message(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(user_message="Ext message"),
    ):
      raise status_exception.ExtendedStatusError(
          "ai.testing.my_component", 123, user_message="Ext message"
      )

  def test_matcher_user_message_mismatch(self):
    self.assertFalse(
        status_matcher.matches(
            user_message="Ext message",
        )(
            status_exception.ExtendedStatusError(
                "ai.testing.my_component",
                123,
                user_message="Other message",
            )
        )
    )

  def test_matcher_user_message_regex(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(user_message_regex=r"Ext \d+"),
    ):
      raise status_exception.ExtendedStatusError(
          "ai.testing.my_component", 123, user_message="Ext 353"
      )

  def test_matcher_user_message_regex_mismatch(self):
    self.assertFalse(
        status_matcher.matches(
            user_message_regex=r"Ext \d+",
        )(
            status_exception.ExtendedStatusError(
                "ai.testing.my_component",
                123,
                user_message="Ext message",
            )
        )
    )

  def test_matcher_debug_message(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(debug_message="Int message"),
    ):
      raise status_exception.ExtendedStatusError(
          "ai.testing.my_component", 123, debug_message="Int message"
      )

  def test_matcher_debug_message_mismatch(self):
    self.assertFalse(
        status_matcher.matches(
            debug_message="Int message",
        )(
            status_exception.ExtendedStatusError(
                "ai.testing.my_component",
                123,
                debug_message="Other message",
            )
        )
    )

  def test_matcher_debug_message_regex(self):
    with self.assertRaisesWithPredicateMatch(
        status_exception.ExtendedStatusError,
        status_matcher.matches(debug_message_regex=r"Int \d+"),
    ):
      raise status_exception.ExtendedStatusError(
          "ai.testing.my_component", 123, debug_message="Int 353"
      )

  def test_matcher_debug_message_regex_mismatch(self):
    self.assertFalse(
        status_matcher.matches(
            debug_message_regex=r"Int \d+",
        )(
            status_exception.ExtendedStatusError(
                "ai.testing.my_component",
                123,
                debug_message="Int message",
            )
        )
    )


if __name__ == "__main__":
  absltest.main()
