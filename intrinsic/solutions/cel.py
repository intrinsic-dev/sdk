# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for the Common Expression Language (CEL)."""


class CelExpression:
  """A CEL expression.

  Represents an expression to be evaluated in lieu of a skill parameter value or
  a BlackboardValue.
  """

  _expression: str

  def __init__(self, expression: str):
    self._expression = expression

  def __str__(self) -> str:
    return self._expression
