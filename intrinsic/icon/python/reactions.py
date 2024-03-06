# Copyright 2023 Intrinsic Innovation LLC

"""Classes for describing Reactions in the ICON Python Client API.

A Reaction is a Condition that is monitored in real-time by the ICON Control
Layer, along with a Response describing what should happen when the Condition is
satisfied.
"""

import datetime
import threading
from typing import Callable, Iterable, Optional, Sequence, Union
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import errors
ReactionCallback = Callable[
    [datetime.datetime, Optional[int], Optional[int]], None
]
"""Reaction callback type.

Function to trigger of the form `callback(timestamp, previous_action_id,
current_action_id)` where `timestamp` is the time when the Reaction occurred,
`previous_action_id` is the id of the action transitioned away from (if any),
and `current_action_id` is the id of the action transitioned to (if any).
"""


class Condition:
  """Describes a real-time condition.

  This class thinly wraps types_pb2.Condition. Use `.proto` to
  access the proto representation.

  A real-time condition is part of a Reaction. It describes the circumstances
  under which the reaction's response(s) should be triggered. There are three
  types of Conditions:

  1) A simple comparison between a state variable and a value, e.g.:
  ```
  icon.Condition.is_less_than("distance_to_goal", 0.25)
  ```
    or a part status field and a value, e.g.:
  ```
  icon.Condition.is_less_than(icon.StateVariablePath.Arm.sensed_position(0),
  3.14)
  ```

  2) A conjunction of other Conditions (all_of, any_of), e.g.:
  ```
  icon.Condition.any_of([
      icon.Condition.is_greater_than("action_time_elapsed", 10.0),
      icon.Condition.is_less_than("distance_to_goal", 0.25)])
  ```

  3) A negated condition, e.g.:
  ```
  icon.Condition.is_not(icon.Condition.is_less_than("distance_to_goal", 0.25)]
  ```

  Attributes:
    proto: The types_pb2.Condition proto representation of this condition.
  """

  def __init__(
      self,
      condition: Union[
          types_pb2.Comparison,
          types_pb2.ConjunctionCondition,
          types_pb2.NegatedCondition,
      ],
  ):
    """Creates a Condition from either a comparison, conjunction or negated condition proto.

    This constructor should not be called directly. Use the class methods
    instead.

    Args:
      condition: Union type of different condition types that should be wrapped
        in this class.

    Raises:
      errors.Client.InvalidArgumentError: Unexpected condition type.
    """

    if isinstance(condition, types_pb2.Comparison):
      self.proto = types_pb2.Condition(comparison=condition)
    elif isinstance(condition, types_pb2.ConjunctionCondition):
      self.proto = types_pb2.Condition(conjunction_condition=condition)
    elif isinstance(condition, types_pb2.NegatedCondition):
      self.proto = types_pb2.Condition(negated_condition=condition)
    else:
      raise errors.Client.InvalidArgumentError(
          'Encountered unexpected condition type: ', type(condition)
      )

  @classmethod
  def is_done(cls) -> 'Condition':
    """Describes a comparison with whether an action has completed.

    The condition is satisfied when the builtin state variable 'xfa.is_done'
    is `True`.

    Returns:
      A Condition object.
    """
    return Condition.is_true('xfa.is_done')

  @classmethod
  def is_true(cls, state_variable_name: str) -> 'Condition':
    """Describes a comparison with `True`.

    The condition is satisfied when the state variable's value is `True`.

    Args:
      state_variable_name: State variable operand.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.Comparison(
            state_variable_name=state_variable_name,
            operation=types_pb2.Comparison.OpEnum.EQUAL,
            bool_value=True,
        )
    )

  @classmethod
  def is_false(cls, state_variable_name: str) -> 'Condition':
    """Describes a comparison with `False`.

    The condition is satisfied when the state variable's value is `False`.

    Args:
      state_variable_name: State variable operand.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.Comparison(
            state_variable_name=state_variable_name,
            operation=types_pb2.Comparison.OpEnum.EQUAL,
            bool_value=False,
        )
    )

  @classmethod
  def is_equal(
      cls, state_variable_name: str, value: Union[float, int, bool]
  ) -> 'Condition':
    """Describes a equality comparison.

    The condition is satisfied when the state variable's value exactly equals
    `value`.

    Depending on the type of `value` this function creates and returns the
    corresponding proto Comparison wrapped in a Condition.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, bool):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.EQUAL,
              bool_value=value,
          )
      )
    elif isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.EQUAL,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.EQUAL,
              double_value=value,
          )
      )

  @classmethod
  def is_not_equal(
      cls, state_variable_name: str, value: Union[float, int, bool]
  ) -> 'Condition':
    """Describes a "not equal" comparison with `value`.

    The condition is satisfied when the state variable's value does not exactly
    equal `value`.

    Depending on the type of `value` this function creates and returns the
    corresponding proto Comparison wrapped in a Condition.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, bool):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
              bool_value=value,
          )
      )
    elif isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.NOT_EQUAL,
              double_value=value,
          )
      )

  @classmethod
  def is_approx_equal(
      cls, state_variable_name: str, value: float, max_abs_error: float = 0.001
  ) -> 'Condition':
    """Describes an "approximately equal" comparison.

    The condition is satisfied when the state variable's value is within
    `max_abs_error` of `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.
      max_abs_error: Comparison tolerance.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.Comparison(
            state_variable_name=state_variable_name,
            operation=types_pb2.Comparison.OpEnum.APPROX_EQUAL,
            double_value=value,
            max_abs_error=max_abs_error,
        )
    )

  @classmethod
  def is_not_approx_equal(
      cls, state_variable_name: str, value: float, max_abs_error: float = 0.001
  ) -> 'Condition':
    """Describes an "approximately not equal" comparison.

    The condition is satisfied when the state variable's value is not within
    `max_abs_error` of `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.
      max_abs_error: Comparison tolerance.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.Comparison(
            state_variable_name=state_variable_name,
            operation=types_pb2.Comparison.OpEnum.APPROX_NOT_EQUAL,
            double_value=value,
            max_abs_error=max_abs_error,
        )
    )

  @classmethod
  def is_greater_than(
      cls, state_variable_name: str, value: Union[float, int]
  ) -> 'Condition':
    """Describes a "greater than" comparison.

    The condition is satisfied when the state variable's value is greater than
    `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
              double_value=value,
          )
      )

  @classmethod
  def is_greater_than_or_equal(
      cls, state_variable_name: str, value: Union[float, int]
  ) -> 'Condition':
    """Describes a "greater than or equal" comparison.

    The condition is satisfied when the state variable's value is greater than
    or equal to `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.GREATER_THAN_OR_EQUAL,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.GREATER_THAN_OR_EQUAL,
              double_value=value,
          )
      )

  @classmethod
  def is_less_than(
      cls, state_variable_name: str, value: Union[float, int]
  ) -> 'Condition':
    """Describes a "less than" comparison.

    The condition is satisfied when the state variable's value is less than
    `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.LESS_THAN,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.LESS_THAN,
              double_value=value,
          )
      )

  @classmethod
  def is_less_than_or_equal(
      cls, state_variable_name: str, value: Union[float, int]
  ) -> 'Condition':
    """Describes a "less than or equal" comparison.

    The condition is satisfied when the state variable's value is less than or
    equal to `value`.

    Args:
      state_variable_name: State variable operand.
      value: Value to compare against.

    Returns:
      A Condition object.
    """
    if isinstance(value, int):
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.LESS_THAN_OR_EQUAL,
              int64_value=value,
          )
      )
    else:
      return Condition(
          condition=types_pb2.Comparison(
              state_variable_name=state_variable_name,
              operation=types_pb2.Comparison.OpEnum.LESS_THAN_OR_EQUAL,
              double_value=value,
          )
      )

  @classmethod
  def is_not(cls, condition: 'Condition') -> 'Condition':
    """Describes a negated condition.

    The condition is satisfied when the given child condition is not satisfied.

    Args:
      condition: Condition to negate.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.NegatedCondition(
            condition=condition.proto,
        )
    )

  @classmethod
  def any_of(cls, conditions: Iterable['Condition']) -> 'Condition':
    """Describes an "any_of" conjunction condition.

    The condition is satisfied when at least one of the child `conditions` are
    satisfied.

    Args:
      conditions: Child conditions.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.ConjunctionCondition(
            operation=types_pb2.ConjunctionCondition.ANY_OF,
            conditions=[condition.proto for condition in conditions],
        )
    )

  @classmethod
  def all_of(cls, conditions: Iterable['Condition']) -> 'Condition':
    """Describes an "all_of" conjunction condition.

    The condition is satisfied when all of the child `conditions` are
    satisfied.

    Args:
      conditions: Child conditions.

    Returns:
      A Condition object.
    """
    return Condition(
        condition=types_pb2.ConjunctionCondition(
            operation=types_pb2.ConjunctionCondition.ALL_OF,
            conditions=[condition.proto for condition in conditions],
        )
    )


class EventFlag:
  """Provides the signalling mechanism for waiting on Reactions."""

  def __init__(self):
    # Use an Event Object as the underlying mechanism. This is specifically
    # chosen so that `wait` calls return immediately if the flag has already
    # been signalled. Such a case can happen if the action->reaction completes
    # faster than the actual call to wait for it.
    self._ev = threading.Event()

  def signal(self) -> None:
    """Signals the flag."""
    self._ev.set()

  def wait(self, timeout: Optional[float] = None) -> bool:
    """Waits until the flag is signalled, or until a timeout occurs.

    If the flag has already been signalled, then this will immediately return
    True.

    Args:
      timeout: Optional timeout in seconds for specifying the maximum wait time.

    Returns:
      True unless a given timeout expired, in which case it is False.
    """
    return self._ev.wait(timeout=timeout)


class _Response:
  """Base type class for responses to a real-time condition."""


class StartActionInRealTime(_Response):
  """Starts another action in response to a real-time condition.

  Attributes:
    proto: The types_pb2.Response proto representation of this response.
  """

  def __init__(self, start_action_id: int):
    """Constructs a Response that starts the given action.

    Args:
      start_action_id: The ID of the action to start. The action is started by
        the ICON Control Layer the next control cycle after the condition is
        satisfied.
    """
    self.proto = types_pb2.Response(start_action_instance_id=start_action_id)


class StartParallelActionInRealTime(_Response):
  """Starts another action in parallel in response to a real-time condition.

  Attributes:
    proto: The types_pb2.Response proto representation of this response.
  """

  def __init__(self, start_action_id: int):
    """Constructs a Response that starts the given action.

    Args:
      start_action_id: The ID of the action to start. The action is started by
        the ICON Control Layer the next control cycle after the condition is
        satisfied.
    """
    self.proto = types_pb2.Response(start_action_instance_id=start_action_id)


class TriggerCallback(_Response):
  """Triggers a callback in response to a real-time condition.

  Attributes:
    callback: The callback to trigger in response.
  """

  def __init__(
      self,
      callback: ReactionCallback,
  ):
    """Constructs a Response that triggers the given callback.

    Args:
      callback: The function to trigger of the form `callback(timestamp,
        previous_action_id, current_action_id)` where `timestamp` is the time
        when the Reaction occurred, `previous_action_id` is the id of the action
        transitioned away from (if any), and `current_action_id` is the id of
        the action transitioned to (if any).
    """
    self.callback = callback


class TriggerRealtimeSignal(_Response):
  """Triggers a realtime signal.

  This response requires the reaction to be associated with an action. The
  real-time signal is triggered the first time the reaction condition is met,
  and never switches back.

  Attributes:
    realtime_signal_name: The realtime signal to trigger in response.
  """

  def __init__(
      self,
      realtime_signal_name: str,
  ):
    """Constructs a Response that triggers the named realtime signal.

    Args:
      realtime_signal_name: The realtime signal to be triggered. The signal is
        declared in the associated action signature.
    """
    self.realtime_signal_name = realtime_signal_name


class Event(_Response):
  """Signals an event flag in response to a real-time condition.

  Attributes:
    flag: The flag to be signalled in response.
  """

  def __init__(self, flag: EventFlag):
    """Constructs a Response that signals the given flag.

    Args:
      flag: The flag to be signalled in response.
    """
    self.flag = flag


class Reaction:
  """Describes a reaction, which is a real-time condition along with responses.

  The condition is monitored every control cycle by the ICON Control Layer. The
  responses are triggered when the condition is satisfied.

  Attributes:
    condition: The condition that the Control Layer should monitor.
    responses: The responses that should occur when the condition is satisfied.
  """

  def __init__(self, condition: Condition, responses: Sequence[_Response]):
    self.condition = condition
    self.responses = responses
