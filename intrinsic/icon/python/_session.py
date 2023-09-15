# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Scopes control of a set of robot parts.

A Session is used to claim exclusive control over one or more parts. It provides
the ability to manipulate those parts by adding actions and/or reactions, and
bounds the lifetime of these server-side objects.

A Session should not be directly instantiated, but instead retrieved via the
the ICON Client. For example:

  connection_params = connection.ConnectionParams("host:port", "robot_name")
  icon_client = icon_api.Client.connect_with_params(connection_params)
  with icon_client.start_session(["robot_arm", "robot_gripper"]) as session:
    # ...
"""

import collections
import datetime
import itertools
import queue
import threading
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from absl import logging
from google.protobuf import message as _message
from google.rpc import code_pb2
from google.rpc import status_pb2
import grpc
from intrinsic.icon.proto import service_pb2
from intrinsic.icon.proto import service_pb2_grpc
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import actions as _actions
from intrinsic.icon.python import errors
from intrinsic.icon.python import reactions as _reactions
from intrinsic.logging.proto import context_pb2

ActionOrActionWithCondition = Union[
    _actions.Action, Tuple[_actions.Action, _reactions.Condition]
]


def _get_action_and_condition(
    element: ActionOrActionWithCondition,
) -> Tuple[_actions.Action, _reactions.Condition]:
  if isinstance(element, _actions.Action):
    return (element, _reactions.Condition.is_done())

  return element


def _format_rpc_status(status: status_pb2.Status) -> str:
  """Parses a status into a readable format."""
  return 'grpc.StatusCode.{} - {}. {}'.format(
      code_pb2.Code.Name(status.code), status.message, status.details
  )


class Session:
  """Internal Session object for scoping control of a set of robot parts."""

  def __init__(
      self,
      stub: service_pb2_grpc.IconApiStub,
      parts: List[str],
      context: Optional[context_pb2.Context] = None,
  ):
    """Creates a new Session to control the given parts.

    This constructor should not be called directly. A Session should instead
    be retrieved via the ICON Client. For example:

      connection_params = connection.ConnectionParams("host:port", "robot_name")
      icon_client = icon_api.Client.connect_with_params(connection_params)
      with icon_client.start_session(["robot_arm", "robot_gripper"]) as session:
        # ...

    Args:
      stub: The ICON service stub.
      parts: List of parts to control.
      context: The log context passed to the session. Needed to sync ICON logs
        to the cloud.

    Raises:
      grpc.RpcError: An error occurred establishing the Session. For example, if
        the given parts were already in use.
    """
    self._stub = stub
    self._request_stream = _RequestIterator()
    self._response_stream = stub.OpenSession(self._request_stream)
    request = service_pb2.OpenSessionRequest()
    request.initial_session_data.allocate_parts.part.extend(parts)
    if context:
      request.log_context.CopyFrom(context)

    self._latest_reaction_id = 0

    self._request_stream.write(request)
    # Get the next response from the stream. If there are any issues, such
    # as the parts already being in use, then this will raise a grpc.RpcError.
    response = next(self._response_stream)

    # Check the OpenSessionResponse's internal status field for any
    # further errors. We don't expect errors at this point during initialization
    # so if we do, end the stream.
    if response.status.code != grpc.StatusCode.OK.value[0]:
      self._response_stream.cancel()
      error_msg = 'Initializing failed with {}'.format(
          _format_rpc_status(response.status)
      )
      logging.error(error_msg)
      raise grpc.RpcError(error_msg)

    self._session_id = response.initial_session_data.session_id
    # Keep track of any action streams the user might initiate.
    self._action_streams_set = set()
    # Start watcher for Reactions and keep track of client-side responses.
    self._watcher_callbacks = collections.defaultdict(list)
    self._watcher_signal_flags = collections.defaultdict(list)
    self._watcher_response_stream = self._stub.WatchReactions(
        service_pb2.WatchReactionsRequest(session_id=self._session_id)
    )
    # Wait for the first response from the watcher stream. Receiving this
    # initial message means that the server-side is ready to serve up reactions.
    # If there are any issues, then this will raise a grpc.RpcError.
    response = next(self._watcher_response_stream)
    if response.HasField('reaction_event'):
      reaction_id = response.reaction_event.reaction_id
      raise grpc.RpcError(
          f'Initializing failed with non-empty watcher reaction {reaction_id}'
      )
    self._watcher_thread = threading.Thread(
        target=self._watch_reaction_responses
    )
    self._watcher_thread.start()
    self._reaction_responses_error = None
    self._ended = False
    logging.info('Started session with id: %d', self._session_id)

  def __enter__(self):
    """Allows usage in a with-statement context."""
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    """Allows usage in a with-statement context."""
    del exc_type, exc_value, traceback  # Unused.
    self.end()

  def _next_reaction_id(self) -> int:
    """Advances a counter which is used for this session's reaction IDs.

    Thread-safe.

    Returns:
      The first time this called, returns 1. Increases by 1 with each subsequent
      call.
    """
    mutex = threading.Lock()
    with mutex:
      self._latest_reaction_id += 1
      return self._latest_reaction_id

  def _watch_reaction_responses(self) -> None:
    """Triggers client-side responses when Reaction events occur."""
    try:
      for response in self._watcher_response_stream:
        reaction_id = response.reaction_event.reaction_id
        for callback in self._watcher_callbacks[reaction_id]:
          callback(
              response.timestamp.ToDatetime(),
              response.reaction_event.previous_action_instance_id
              if response.reaction_event.HasField('previous_action_instance_id')
              else None,
              response.reaction_event.current_action_instance_id
              if response.reaction_event.HasField('current_action_instance_id')
              else None,
          )
        for signal_flag in self._watcher_signal_flags[reaction_id]:
          signal_flag.signal()
    except grpc.RpcError as e:
      # Ignore the error if it's cancelled since this is expected when we are
      # done with watching, e.g. when the Session ends. Note: this grpc.RpcError
      # is also a grpc.Call, so it has the code() attribute. See details at
      # https://github.com/grpc/grpc/issues/10885#issuecomment-302581315.
      if e.code() != grpc.StatusCode.CANCELLED:  # type: ignore
        # store the exception so that it can be retrieved by the session user
        # for error handling
        self._reaction_responses_error = e
        logging.info('The action raised an error during execution: %r', e)

  def end(self) -> bool:
    """Attempts to end the Session.

    Allocated parts will return to a stopped and disabled state. Action streams
    and reaction watchers created within this session will also be ended.

    Does nothing if the session has already ended.

    Raises:
      grpc.RPCError: Raises received exception from watcher thread if any
        occurred.

    Returns:
      Whether the attempt was successful.
    """
    if self._ended:
      return False

    for stream in self._action_streams_set:
      if not stream.end():
        return False

    # Tell the server that we are done with this session by signalling there's
    # no write requests left.
    self._request_stream.end()
    try:
      for response in self._response_stream:
        logging.error(
            'Received unexpected response from the server: %s', response
        )
    except grpc.RpcError:
      logging.exception(
          'Unexpected server error while ending session %d', self._session_id
      )
      return False

    # The server should then have ended the watcher stream, so wait for the
    # thread to finish up.
    self._watcher_thread.join()

    # if there was an error in the watcher thread,
    # the execution failed and we should raise here to avoid a silent error
    if self._reaction_responses_error:
      raise self._reaction_responses_error

    self._ended = True
    logging.info('Ended session with id: %d', self._session_id)
    return self._ended

  def _raise_failed_response(
      self, status: status_pb2.Status, error_msg_format: str
  ):
    """Handles failed responses from the session stream.

    Args:
      status: The status of the failed response.
      error_msg_format: The message format to be displayed in logs and
        exceptions.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred.
      grpc.RpcError: The server returned an aborted error, and the session will
        be ended automatically.
    """
    error_msg = error_msg_format.format(_format_rpc_status(status))
    # Raise an exception to end the flow if the server decides to abort.
    if status.code == grpc.StatusCode.ABORTED.value[0]:
      self.end()
      logging.error(error_msg)
      raise grpc.RpcError(error_msg)
    raise errors.Session.ActionError(error_msg)

  def _add_reactions_to_proto(
      self,
      action_id: Optional[int],
      request: types_pb2.ActionsAndReactions,
      reactions: Iterable[_reactions.Reaction],
  ) -> None:
    """Adds new Reactions for the given Action to `request`.

    Args:
      action_id: The ID of the action to add to. Can be None, which means that
        the reaction is free-standing and not bound to an action.
      request: The proto that forms part of the add request to the server.
      reactions: List of Reactions to attach to the new Action.

    Raises:
      errors.Session.ActionError: Could not add an invalid Reaction.
    """
    for reaction in reactions:
      reaction_id = self._next_reaction_id()

      # Only real-time Responses, such as `StartActionInRealTime`, require a
      # Reaction proto to be added to the server request. However, at least one
      # Reaction proto must be added in order to trigger a Reaction event. This
      # event is still required for non-real-time Responses, so we need to keep
      # track of whether any have been added.
      added_reaction_proto = False

      for response in reaction.responses:
        if isinstance(response, _reactions.StartActionInRealTime) or isinstance(
            response, _reactions.StartParallelActionInRealTime
        ):
          # On the server-side, the Reaction proto only allows for a single
          # Response, so we need to replicate another Reaction for subsequent
          # `StartActionInRealTime`s. Since reaction IDs must be unique,
          # a new one will be generated.
          additional_reaction_id = (
              self._next_reaction_id() if added_reaction_proto else reaction_id
          )
          reaction_proto = types_pb2.Reaction(
              reaction_instance_id=additional_reaction_id,
              condition=reaction.condition.proto,
              response=response.proto,
          )
          if action_id is not None:
            reaction_proto.action_association.action_instance_id = action_id
            reaction_proto.action_association.stop_associated_action = (
                isinstance(response, _reactions.StartActionInRealTime)
            )
          request.reactions.append(reaction_proto)
          added_reaction_proto = True
        elif isinstance(response, _reactions.TriggerCallback):
          self._watcher_callbacks[reaction_id].append(response.callback)
        elif isinstance(response, _reactions.Signal):
          self._watcher_signal_flags[reaction_id].append(response.flag)
        else:
          raise errors.Session.ActionError(f'Unsupported response: {response}')

      if not added_reaction_proto:
        # Make sure at least one Reaction proto is added so that we can receive
        # the Reaction event later.
        reaction_proto = types_pb2.Reaction(
            reaction_instance_id=reaction_id,
            condition=reaction.condition.proto,
        )
        if action_id is not None:
          reaction_proto.action_association.action_instance_id = action_id
          reaction_proto.action_association.stop_associated_action = False
        request.reactions.append(reaction_proto)

  def add_action(self, action: _actions.Action) -> _actions.Action:
    """Creates and adds a new Action to the session.

    Args:
      action: The Action to add to the session.

    Returns:
      The Action if successful.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
        session has already ended.
      grpc.RpcError: An error occurred whilst adding the Action. If the server
        returned an aborted error then the session will be ended automatically.
    """
    self.add_actions([action])
    return action

  def add_actions(self, actions: Iterable[_actions.Action]) -> None:
    """Adds multiple Actions to the session.

    Args:
      actions: The Actions to add to the session.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
        session has already ended.
      grpc.RpcError: An error occurred whilst adding the Actions. If the server
        returned an aborted error then the session will be ended automatically.
    """
    if self._ended:
      raise errors.Session.ActionError(
          f'Cannot add actions to already ended session {self._session_id}'
      )

    request = service_pb2.OpenSessionRequest()
    for action in actions:
      request.add_actions_and_reactions.action_instances.append(action.proto)
      self._add_reactions_to_proto(
          action.id, request.add_actions_and_reactions, action.reactions
      )

    self._request_stream.write(request)
    response = next(self._response_stream)

    if response.status.code != grpc.StatusCode.OK.value[0]:
      self._raise_failed_response(
          response.status, 'Adding actions failed with {}'
      )

  def add_action_sequence(
      self,
      actions: Sequence[ActionOrActionWithCondition],
  ) -> _reactions.SignalFlag:
    """Adds a sequence of Actions to the session.

    Adds the actions to the session and connects them with transitions. The
    default transition contition is `is_done`. If a Tuple of (action, condition)
    is used in `actions`, this condition is used for that action. The syntax is
    the following for actions connected with `is_done`:

    final_action_done = session.add_action_sequence(
        [action_1, action_2, action_3])

    With custom conditions it can be used like this:

    final_action_settled = session.add_action_sequence([
          action_1,
          (action_2, _reactions.Condition.is_greater_than('my_variable', 15.3)),
          (action_3, _reactions.Condition.is_true('xfa.is_settled')),
      ])

    Args:
      actions: A sequence of actions or tuples of an action and a condition. If
        only an action is passed, `is_done` is used as condition for the
        transition to the next action.

    Returns:
      A SignalFlag on the last condition in the sequence.
    """
    request = service_pb2.OpenSessionRequest()

    for current_element, next_element in itertools.pairwise(actions):
      current_action, current_condition = _get_action_and_condition(
          current_element
      )
      next_action, _ = _get_action_and_condition(next_element)

      request.add_actions_and_reactions.action_instances.append(
          current_action.proto
      )
      self._add_reactions_to_proto(
          current_action.id,
          request.add_actions_and_reactions,
          [
              _reactions.Reaction(
                  current_condition,
                  responses=[
                      _reactions.StartActionInRealTime(next_action.id),
                  ],
              )
          ],
      )
      self._add_reactions_to_proto(
          current_action.id,
          request.add_actions_and_reactions,
          current_action.reactions,
      )

    # Create done_flag on last action in the sequence.
    last_action, last_condition = _get_action_and_condition(actions[-1])
    request.add_actions_and_reactions.action_instances.append(last_action.proto)

    done_flag = _reactions.SignalFlag()

    self._add_reactions_to_proto(
        last_action.id,
        request.add_actions_and_reactions,
        [
            _reactions.Reaction(
                last_condition,
                responses=[
                    _reactions.Signal(done_flag),
                ],
            )
        ],
    )

    self._request_stream.write(request)
    response = next(self._response_stream)

    if response.status.code != grpc.StatusCode.OK.value[0]:
      self._raise_failed_response(
          response.status, 'Adding actions failed with {}'
      )

    return done_flag

  def add_reactions(
      self,
      action: Optional[_actions.Action],
      reactions: Iterable[_reactions.Reaction],
  ) -> None:
    """Adds a reaction to the session.

    This method provides the full Reaction API. For simple use cases
    `add_transition`, `add_reaction` and `add_freestanding_reactions` can
    be used.

    Args:
      action: Action the reaction is associated with. If the action is None, a
        freestanding reaction is added.
      reactions: Iterable of reactions which are added to the action.
    """
    if self._ended:
      raise errors.Session.ActionError(
          f'Cannot add reactions to already ended session {self._session_id}'
      )

    request = service_pb2.OpenSessionRequest()

    action_id = None
    if action is not None:
      action_id = action.id
    self._add_reactions_to_proto(
        action_id, request.add_actions_and_reactions, reactions
    )

    self._request_stream.write(request)
    response = next(self._response_stream)

    if response.status.code != grpc.StatusCode.OK.value[0]:
      self._raise_failed_response(
          response.status, 'Adding actions failed with {}'
      )

  def add_transition(
      self,
      from_action: _actions.Action,
      to_action: _actions.Action,
      condition: Optional[_reactions.Condition] = None,
      callback: Optional[_reactions.ReactionCallback] = None,
  ) -> _reactions.SignalFlag:
    """Adds a transition from `from_action` to `to_action`.

    Adds a transition from one action to another action. This is a simple
    wrapper using StartActionInRealTime.

    Args:
      from_action: The start action.
      to_action: The target action.
      condition: Condition which triggers the transition. Defaults to `is_done`.
      callback: An optional callback to trigger by this transition.

    Returns:
      A SignalFlag triggered by this transition.
    """

    if condition is None:
      condition = _reactions.Condition.is_done()

    signal = _reactions.SignalFlag()
    responses = [
        _reactions.Signal(signal),
        _reactions.StartActionInRealTime(to_action.id),
    ]
    if callback is not None:
      responses.append(_reactions.TriggerCallback(callback))

    self.add_reactions(from_action, [_reactions.Reaction(condition, responses)])
    return signal

  def add_reaction(
      self,
      action: _actions.Action,
      condition: _reactions.Condition,
      callback: Optional[_reactions.ReactionCallback] = None,
  ) -> _reactions.SignalFlag:
    """Adds a reaction to the session.

    This adds a SignalFlag and optionally a callback reaction to the action,
    triggered on the given condition.

    Args:
      action: Action the reaction is associated with.
      condition: Condition which triggers the reaction.
      callback: Optional function to trigger by this reaction.

    Returns:
      A SignalFlag on the given condition.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
        session has already ended.
      grpc.RpcError: An error occurred whilst adding the reactions. If the
        server returned an aborted error then the session will be ended
        automatically.
    """
    signal = _reactions.SignalFlag()
    responses = [_reactions.Signal(signal)]
    if callback is not None:
      responses.append(_reactions.TriggerCallback(callback))

    self.add_reactions(action, [_reactions.Reaction(condition, responses)])
    return signal

  def add_freestanding_reactions(
      self, reactions: Sequence[_reactions.Reaction]
  ) -> None:
    """Adds free-standing reactions to the session.

    Free-standing reactions are not associated with any action and are active as
    long as the session is active.

    Args:
      reactions: Iterable container of reactions to add to the session.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
        session has already ended.
      grpc.RpcError: An error occurred whilst adding the reaations. If the
        server returned an aborted error then the session will be ended
        automatically.
    """

    self.add_reactions(None, reactions)

  def start_action(
      self, action_id: int, stop_active_actions: bool = True
  ) -> None:
    """Starts the given action on the server.

    Args:
      action_id: The ID of the action to be started.
      stop_active_actions: If true, stops the currently active actions.

    Returns:
      None

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
      session has already ended.
      grpc.RpcError: An error occurred whilst starting the Action. If the server
        returned an aborted error then the session will be ended automatically.
    """
    return self.start_parallel_actions([action_id], stop_active_actions)

  def start_parallel_actions(
      self, action_ids: Sequence[int], stop_active_actions: bool = True
  ) -> None:
    """Starts the given actions in parallel on the server.

    Args:
      action_ids: The ID of the action to be started.
      stop_active_actions: If true, stops the currently active actions. If
        false, all actions specified in `action_ids` start in parallel to the
        currently already active actions.

    Raises:
      errors.Session.ActionError: A non-session ending failure occurred, or
      session has already ended.
      grpc.RpcError: An error occurred whilst starting the Action. If the server
        returned an aborted error then the session will be ended automatically.
    """
    if self._ended:
      raise errors.Session.ActionError(
          f'Cannot start action in already ended session {self._session_id}'
      )
    start_actions_request = (
        service_pb2.OpenSessionRequest.StartActionsRequestData(
            action_instance_ids=action_ids,
            stop_active_actions=stop_active_actions,
        )
    )
    request = service_pb2.OpenSessionRequest(
        start_actions_request=start_actions_request
    )
    self._request_stream.write(request)
    response = next(self._response_stream)

    if response.status.code != grpc.StatusCode.OK.value[0]:
      self._raise_failed_response(
          response.status, 'Starting an action failed with {}'
      )

  def start_action_and_wait(
      self,
      action: _actions.Action,
      wait_for: Optional[_reactions.SignalFlag] = None,
      timeout_s: Optional[float] = None,
  ) -> bool:
    """Starts an action and waits for the finish signal.

    The wait_for SignalFlag defines the waiting condition. If the wait_for
    Signal is not defined, the `is_done` condition on the started action is
    used. This call stops all running actions before starting the new action.

    You must call `add_action` before calling `start_action_and_wait`.

    Args:
      action: The action to start.
      wait_for: The signal to wait for. Defaults to `is_done` on the started
        action.
      timeout_s: Optional timeout in seconds for specifying the maximum wait
        time.

    Returns:
      True unless a given timeout expired, in which case it is False.
    """
    if wait_for is None:
      wait_for = self.add_reaction(action, _reactions.Condition.is_done())

    self.start_action(action.id, stop_active_actions=True)
    return wait_for.wait(timeout_s)

  def open_stream(self, action_id: int, field_name: str) -> 'Stream':
    """Opens a stream for streaming data to the given action.

    Args:
      action_id: The ID of a streaming action.
      field_name: The name of the field to stream values to.

    Returns:
      A newly opened Stream if successful.

    Raises:
      errors.Session.StreamError: A non-session ending failure occurred, or
      session has already ended.
      grpc.RpcError: An error occurred whilst opening the Stream and the
        session will be ended automatically.
    """
    if self._ended:
      raise errors.Session.ActionError(
          f'Cannot open stream to already ended session {self._session_id}'
      )

    try:
      stream = Stream(self._stub, self._session_id, action_id, field_name)
      self._action_streams_set.add(stream)
      return stream
    except grpc.RpcError:
      self.end()
      raise

  def close_stream(self, stream: 'Stream') -> bool:
    """Closes a stream.

    Args:
      stream: The previously opened stream.

    Returns:
      Returns True if successful or if the stream was already closed.

    Raises:
      errors.Session.StreamError: The stream does not belong to this session.
    """
    if stream.session_id != self._session_id:
      raise errors.Session.ActionError(
          f'Cannot close stream {stream.id} from session {self._session_id} '
          + f'since it belongs to session {stream.session_id}'
      )

    res = stream.end()
    if res and stream in self._action_streams_set:
      self._action_streams_set.remove(stream)
    return res

  def get_latest_output(
      self, action_id: int, timeout: datetime.timedelta
  ) -> streaming_output_pb2.StreamingOutput:
    """Polls for the latest streaming output value from the given Action.

    Args:
      action_id: The ID of the Action of interest.
      timeout: Block at most until this expires, waiting for an output value to
        be published.

    Returns:
      A StreamingOutput proto that has the (server-side) timestamp of when the
      output was published, as well as the output itself, packed into an Any
      proto.
    """
    response = self._stub.GetLatestStreamingOutput(
        service_pb2.GetLatestStreamingOutputRequest(
            action_id=action_id, session_id=self._session_id
        ),
        timeout=timeout.total_seconds(),
    )
    return response.output

  def get_session_id(self) -> int:
    """Returns the session_id.

    This session may have ended, but we still allow retrieving the session_id
    for the purpose of looking up logs, etc.

    Returns:
      The session_id.
    """
    return self._session_id

  def get_reaction_responses_error(self) -> Optional[Exception]:
    """Returns the error received from ICON via grpc in the watch_reaction_responses thread.

    This function can be used to check if any error was received from ICON while
    executing an action.

    Returns: Returns received exception or None, if there wasn't any.
    """
    return self._reaction_responses_error


class Stream:
  """Streams allow users to stream data into actions.

  Attributes:
    session_id: The ID of the session this stream belongs to.
    field_name: The action-specific field name.
  """

  def __init__(
      self,
      stub: service_pb2_grpc.IconApiStub,
      session_id: int,
      action_id: int,
      field_name: str,
  ):
    """Creates a new Stream to stream data to the given action.

    Args:
      stub: The ICON service stub.
      session_id: The ID of the session this stream and action belong to.
      action_id: The ID of a streaming action.
      field_name: The name of the field to stream values to.

    Raises:
      errors.Session.StreamError: A non-session ending failure occurred.
      grpc.RpcError: An error occurred establishing the Stream.
    """
    self._request_stream = _RequestIterator()
    self._response_stream = stub.OpenWriteStream(self._request_stream)
    request = service_pb2.OpenWriteStreamRequest(
        add_write_stream=service_pb2.AddStreamRequest(
            action_id=action_id, field_name=field_name
        ),
        session_id=session_id,
    )
    self._request_stream.write(request)
    response = next(self._response_stream)

    status = response.add_stream_response.status
    if status.code != grpc.StatusCode.OK.value[0]:
      self._response_stream.cancel()
      error_msg = f'Opening stream failed with {_format_rpc_status(status)}'
      if status.code == grpc.StatusCode.ABORTED.value[0]:
        logging.error(error_msg)
        raise grpc.RpcError(error_msg)
      raise errors.Session.StreamError(error_msg)

    self.session_id = session_id
    self.field_name = field_name
    self._ended = False
    logging.info('Started stream: %s', self._format())

  def _format(self) -> str:
    """Returns a human-readable string identifying the stream.

    Returns:
      A string describing the stream.
    """
    return '{}(session_id={}, field_name={})'.format(
        self, self.session_id, self.field_name
    )

  def write(self, value: _message.Message) -> None:
    """Writes the value to the running action.

    Note that successful completion means that the value was *written* but does
    not guarantee that the message has been received or consumed by the
    underlying implementation of the corresponding action.

    Args:
      value: The value to stream to the action.

    Raises:
      errors.Session.StreamError: The value failed to be written.
      grpc.RpcError: An error occurred whilst communicating with the server.
    """
    if self._ended:
      raise errors.Session.StreamError(
          f'Cannot write to already ended stream {self._format()}'
      )

    request = service_pb2.OpenWriteStreamRequest()
    request.write_value.value.Pack(value)
    self._request_stream.write(request)
    response = next(self._response_stream)
    if response.write_value_response.code != grpc.StatusCode.OK.value[0]:
      error_msg = 'Writing to stream {} failed with {}'.format(
          self._format(), _format_rpc_status(response.write_value_response)
      )
      raise errors.Session.StreamError(error_msg)

  def end(self) -> bool:
    """Attempts to end the Stream.

    Returns:
      Whether the attempt was successful.
    """
    if self._ended:
      return True
    self._request_stream.end()
    try:
      for response in self._response_stream:
        logging.error(
            'Received unexpected response from the server: %s', response
        )
    except grpc.RpcError:
      logging.exception(
          'Unexpected server error while ending stream %s', self._format()
      )
      return False

    self._ended = True
    logging.info('Ended stream: %s', self._format())
    return self._ended


class _RequestIterator:
  """Iterator class for streaming gRPC requests."""

  def __init__(self):
    self._ended = False
    self._queue = queue.Queue()

  def __iter__(self) -> '_RequestIterator':
    return self

  def __next__(self) -> _message.Message:
    item = self._queue.get()
    if self._ended:
      raise StopIteration
    return item

  def write(self, message: _message.Message):
    if not self._ended:
      self._queue.put(message)

  def end(self):
    while not self._queue.empty():
      try:
        self._queue.get(False)
      except queue.Empty:
        continue
      self._queue.task_done()
    self._ended = True
    # Add a dud empty message to unblock getting from the queue.
    self._queue.put(_message.Message())
