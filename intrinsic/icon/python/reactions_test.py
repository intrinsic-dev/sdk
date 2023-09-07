# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.icon.python.reactions."""

import threading
from unittest import mock

from absl.testing import absltest
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import reactions


class ConditionTest(absltest.TestCase):

  def test_condition_is_done(self):
    self.assertEqual(
        reactions.Condition.is_done().proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='xfa.is_done',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                bool_value=True,
            )
        ),
    )

  def test_condition_is_true(self):
    self.assertEqual(
        reactions.Condition.is_true('foo').proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                bool_value=True,
            )
        ),
    )

  def test_condition_is_false(self):
    self.assertEqual(
        reactions.Condition.is_false('foo').proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                bool_value=False,
            )
        ),
    )

  def test_condition_is_equal(self):
    self.assertEqual(
        reactions.Condition.is_equal('foo', True).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                bool_value=True,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_equal('bar', 0.5).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='bar',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                double_value=0.5,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_equal('bar', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='bar',
                operation=types_pb2.Comparison.OpEnum.EQUAL,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_not_equal(self):
    self.assertEqual(
        reactions.Condition.is_not_equal('foo', True).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
                bool_value=True,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_not_equal('bar', 0.5).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='bar',
                operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
                double_value=0.5,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_not_equal('bar', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='bar',
                operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_approx_equal(self):
    self.assertEqual(
        reactions.Condition.is_approx_equal(
            'foo', 2.0, max_abs_error=0.125
        ).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.APPROX_EQUAL,
                double_value=2.0,
                max_abs_error=0.125,
            )
        ),
    )

  def test_condition_is_not_approx_equal(self):
    self.assertEqual(
        reactions.Condition.is_not_approx_equal(
            'foo', 2.0, max_abs_error=0.125
        ).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.APPROX_NOT_EQUAL,
                double_value=2.0,
                max_abs_error=0.125,
            )
        ),
    )

  def test_condition_is_greater(self):
    self.assertEqual(
        reactions.Condition.is_greater_than('foo', 1.0).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                double_value=1.0,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_greater_than('foo', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_greater_than_or_equal(self):
    self.assertEqual(
        reactions.Condition.is_greater_than_or_equal('foo', 1.0).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.GREATER_THAN_OR_EQUAL,
                double_value=1.0,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_greater_than_or_equal('foo', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.GREATER_THAN_OR_EQUAL,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_less_than(self):
    self.assertEqual(
        reactions.Condition.is_less_than('foo', 1.0).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                double_value=1.0,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_less_than('foo', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_less_than_or_equal(self):
    self.assertEqual(
        reactions.Condition.is_less_than_or_equal('foo', 1.0).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.LESS_THAN_OR_EQUAL,
                double_value=1.0,
            )
        ),
    )
    self.assertEqual(
        reactions.Condition.is_less_than_or_equal('foo', 1).proto,
        types_pb2.Condition(
            comparison=types_pb2.Comparison(
                state_variable_name='foo',
                operation=types_pb2.Comparison.OpEnum.LESS_THAN_OR_EQUAL,
                int64_value=1,
            )
        ),
    )

  def test_condition_is_not(self):
    self.assertEqual(
        reactions.Condition.is_not(
            reactions.Condition.is_less_than_or_equal('foo', 1.0)
        ).proto,
        types_pb2.Condition(
            negated_condition=types_pb2.NegatedCondition(
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN_OR_EQUAL,
                        double_value=1.0,
                    )
                ),
            )
        ),
    )

  def test_condition_any_of_all_of(self):
    self.assertEqual(
        reactions.Condition.any_of(
            iter([
                reactions.Condition.all_of(
                    iter([
                        reactions.Condition.is_true('foo'),
                        reactions.Condition.is_greater_than('bar', 1.0),
                    ])
                ),
                reactions.Condition.is_false('baz'),
            ])
        ).proto,
        types_pb2.Condition(
            conjunction_condition=types_pb2.ConjunctionCondition(
                operation=types_pb2.ConjunctionCondition.ANY_OF,
                conditions=[
                    types_pb2.Condition(
                        conjunction_condition=types_pb2.ConjunctionCondition(
                            operation=types_pb2.ConjunctionCondition.ALL_OF,
                            conditions=[
                                types_pb2.Condition(
                                    comparison=types_pb2.Comparison(
                                        state_variable_name='foo',
                                        operation=types_pb2.Comparison.OpEnum.EQUAL,
                                        bool_value=True,
                                    )
                                ),
                                types_pb2.Condition(
                                    comparison=types_pb2.Comparison(
                                        state_variable_name='bar',
                                        operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                                        double_value=1.0,
                                    )
                                ),
                            ],
                        )
                    ),
                    types_pb2.Condition(
                        comparison=types_pb2.Comparison(
                            state_variable_name='baz',
                            operation=types_pb2.Comparison.OpEnum.EQUAL,
                            bool_value=False,
                        )
                    ),
                ],
            )
        ),
    )


if __name__ == '__main__':
  absltest.main()
