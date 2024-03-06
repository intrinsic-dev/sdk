# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.icon.python._session."""

import collections
import datetime
import threading
from unittest import mock

from absl.testing import absltest
from google.protobuf import any_pb2
from google.protobuf import empty_pb2
from google.protobuf import timestamp_pb2
import grpc
from intrinsic.icon.proto import service_pb2
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import _session
from intrinsic.icon.python import actions as _actions
from intrinsic.icon.python import errors
from intrinsic.icon.python import reactions as _reactions


class SessionTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    # Use `MagicMock` instead of the more constrained autospec for
    # `service_pb2_grpc.IconApiStub` since the auto-generated interface doesn't
    # contain the OpenSession attribute.
    self._stub = mock.MagicMock()
    # As above, use `MagicMock` instead of `grpc.StreamStreamMultiCallable`
    # since it's missing the __next__ and cancel attributes.
    self._response_stream = mock.MagicMock()
    self._watcher_response_stream = mock.MagicMock()
    self._stub.OpenSession.return_value = self._response_stream
    self._mock_thread_cls = self.enter_context(
        mock.patch.object(threading, 'Thread', autospec=True)
    )
    self._stub.WatchReactions.return_value = self._watcher_response_stream

  def _prepare_initial_response(self, response_code=grpc.StatusCode.OK):
    response = mock.create_autospec(service_pb2.OpenSessionResponse)
    response.status.code = response_code.value[0]
    response.initial_session_data.session_id = 1
    self._response_stream.__next__.return_value = response
    watcher_response = mock.create_autospec(service_pb2.WatchReactionsResponse)
    watcher_response.HasField.return_value = False
    self._watcher_response_stream.__next__.return_value = watcher_response

  def _prepare_session_with_response(self, response_code):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    response = mock.create_autospec(service_pb2.OpenSessionResponse)
    response.status.code = response_code.value[0]
    self._response_stream.__next__.return_value = response
    return session

  def test_start_session(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    self.assertEqual(session._session_id, 1)
    self._response_stream.cancel.assert_not_called()
    self._stub.WatchReactions.assert_called_once_with(
        service_pb2.WatchReactionsRequest(session_id=session._session_id)
    )
    self._mock_thread_cls.assert_called_once_with(
        target=session._watch_reaction_responses
    )
    session._watcher_thread.start.assert_called_once_with()

  def test_start_session_next_response_error(self):
    self._response_stream.__next__.side_effect = grpc.RpcError('uh oh')

    with self.assertRaises(grpc.RpcError):
      _session.Session(self._stub, ['foo'])
    self._response_stream.cancel.assert_not_called()
    self._watcher_response_stream.__next__.assert_not_called()

  def test_start_session_status_error(self):
    self._prepare_initial_response(grpc.StatusCode.CANCELLED)

    with self.assertRaisesRegex(
        grpc.RpcError, 'Initializing failed with grpc.StatusCode.CANCELLED'
    ):
      _session.Session(self._stub, ['foo'])
    self._response_stream.cancel.assert_called_with()
    self._watcher_response_stream.__next__.assert_not_called()

  def test_start_session_watcher_response_error(self):
    self._prepare_initial_response()
    watcher_response = mock.create_autospec(service_pb2.WatchReactionsResponse)
    watcher_response.reaction_event.reaction_id = 2
    self._watcher_response_stream.__next__.return_value = watcher_response

    with self.assertRaisesRegex(
        grpc.RpcError, 'Initializing failed with non-empty watcher reaction 2'
    ):
      _session.Session(self._stub, ['foo'])
    self._watcher_response_stream.__next__.assert_called_once()
    self._mock_thread_cls.assert_not_called()

  def test_end(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    self.assertFalse(session._ended)
    stream = mock.create_autospec(_session.Stream)
    session._action_streams_set = {stream}

    self.assertTrue(session.end())
    self.assertTrue(session._ended)
    stream.end.assert_called_once_with()
    session._watcher_thread.join.assert_called_once_with()

  def test_end_unsuccessful(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    self.assertFalse(session._ended)
    error = grpc.RpcError()
    error.code = mock.Mock()
    error.code.return_value = grpc.StatusCode.INTERNAL
    session._response_stream = _RaiseExceptionIterable(error)

    self.assertFalse(session.end())
    self.assertFalse(session._ended)

  def test_end_action_stream_unsuccessful(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    self.assertFalse(session._ended)
    stream = mock.create_autospec(_session.Stream)
    stream.end.return_value = False
    session._action_streams_set = {stream}

    self.assertFalse(session.end())
    self.assertFalse(session._ended)
    self._response_stream.cancel.assert_not_called()
    stream.end.assert_called_once_with()

  def test_end_already_ended(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    session.end()
    self.assertTrue(session._ended)

    self.assertFalse(session.end())
    self.assertTrue(session._ended)

  def test_context_manager(self):
    """The context manager should end the Session once out of scope."""
    self._prepare_initial_response()
    self._response_stream.cancel.return_value = True

    with _session.Session(self._stub, ['foo']) as session:
      self.assertFalse(session._ended)
    self.assertTrue(session._ended)

  def test_add_reactions_to_proto(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    request = types_pb2.ActionsAndReactions()
    callback = mock.Mock()
    flag = _reactions.EventFlag()
    reactions = [
        _reactions.Reaction(
            _reactions.Condition.is_true('some_condition_var'),
            [
                _reactions.StartActionInRealTime(start_action_id=20),
                _reactions.Event(flag),
            ],
        ),
        _reactions.Reaction(
            _reactions.Condition.is_greater_than('another_condition_var', 2.0),
            [
                _reactions.StartActionInRealTime(start_action_id=30),
                _reactions.TriggerCallback(callback),
            ],
        ),
        _reactions.Reaction(
            _reactions.Condition.is_greater_than(
                'yet_another_condition_var', 2.0
            ),
            [
                _reactions.StartParallelActionInRealTime(start_action_id=40),
                _reactions.TriggerCallback(callback),
            ],
        ),
    ]
    expected_request = types_pb2.ActionsAndReactions(
        reactions=[
            types_pb2.Reaction(
                reaction_instance_id=1,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10, stop_associated_action=True
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='some_condition_var',
                        operation=types_pb2.Comparison.OpEnum.EQUAL,
                        bool_value=True,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=20)),
            ),
            types_pb2.Reaction(
                reaction_instance_id=2,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10, stop_associated_action=True
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='another_condition_var',
                        operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                        double_value=2.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=30)),
            ),
            types_pb2.Reaction(
                reaction_instance_id=3,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10, stop_associated_action=False
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='yet_another_condition_var',
                        operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                        double_value=2.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=40)),
            ),
        ],
    )

    session._add_reactions_to_proto(10, request, iter(reactions))
    self.assertEqual(expected_request, request)
    self.assertSequenceEqual(session._watcher_callbacks[2], [callback])
    self.assertSequenceEqual(session._watcher_signal_flags[1], [flag])

  def test_add_reactions_to_proto_multiple_real_time(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    request = types_pb2.ActionsAndReactions()
    callback = mock.Mock()
    reactions = [
        _reactions.Reaction(
            _reactions.Condition.is_less_than('foo_var', 1.0),
            [
                _reactions.StartActionInRealTime(start_action_id=20),
                _reactions.TriggerRealtimeSignal(
                    realtime_signal_name='foo_signal'
                ),
                _reactions.StartParallelActionInRealTime(start_action_id=40),
                _reactions.TriggerCallback(callback),
            ],
        )
    ]
    expected_request = types_pb2.ActionsAndReactions(
        reactions=[
            types_pb2.Reaction(
                reaction_instance_id=1,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=0, stop_associated_action=True
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=20)),
            ),
            types_pb2.Reaction(
                reaction_instance_id=2,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=0,
                    stop_associated_action=False,
                    triggered_signal_name='foo_signal',
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
            ),
            types_pb2.Reaction(
                reaction_instance_id=3,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=00, stop_associated_action=False
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=40)),
            ),
            types_pb2.Reaction(
                reaction_instance_id=4,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10, stop_associated_action=True
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=20)),
            ),
            types_pb2.Reaction(
                reaction_instance_id=5,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10,
                    stop_associated_action=False,
                    triggered_signal_name='foo_signal',
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
            ),
            types_pb2.Reaction(
                reaction_instance_id=6,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10, stop_associated_action=False
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='foo_var',
                        operation=types_pb2.Comparison.OpEnum.LESS_THAN,
                        double_value=1.0,
                    )
                ),
                response=(types_pb2.Response(start_action_instance_id=40)),
            ),
        ],
    )

    session._add_reactions_to_proto(0, request, iter(reactions))
    session._add_reactions_to_proto(10, request, iter(reactions))
    self.assertEqual(expected_request, request)
    self.assertSequenceEqual(session._watcher_callbacks[1], [callback])

  def test_add_reactions_to_proto_without_real_time(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    request = types_pb2.ActionsAndReactions()
    callback = mock.Mock()
    reactions = [
        _reactions.Reaction(
            _reactions.Condition.is_true('some_condition_var'),
            [_reactions.TriggerCallback(callback)],
        ),
    ]
    expected_request = types_pb2.ActionsAndReactions(
        reactions=[
            types_pb2.Reaction(
                reaction_instance_id=1,
                action_association=types_pb2.Reaction.ActionAssociation(
                    action_instance_id=10,
                ),
                condition=types_pb2.Condition(
                    comparison=types_pb2.Comparison(
                        state_variable_name='some_condition_var',
                        operation=types_pb2.Comparison.OpEnum.EQUAL,
                        bool_value=True,
                    )
                ),
            ),
        ],
    )

    session._add_reactions_to_proto(10, request, iter(reactions))
    self.assertEqual(expected_request, request)
    self.assertSequenceEqual(session._watcher_callbacks[1], [callback])

  def test_add_reactions(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    callback = mock.Mock()

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      flag = _reactions.EventFlag()

      session.add_reactions(
          _actions.Action(3, 'bar', 'foo', None, []),
          reactions=[
              _reactions.Reaction(
                  _reactions.Condition.is_true('some_condition_var'),
                  [
                      _reactions.TriggerCallback(callback),
                      _reactions.Event(flag),
                  ],
              ),
              _reactions.Reaction(
                  _reactions.Condition.is_greater_than(
                      'another_condition_var', 2.0
                  ),
                  [_reactions.StartActionInRealTime(start_action_id=34)],
              ),
          ],
      )

      mock_request_stream.write.assert_called_with(
          service_pb2.OpenSessionRequest(
              add_actions_and_reactions=types_pb2.ActionsAndReactions(
                  reactions=[
                      types_pb2.Reaction(
                          reaction_instance_id=1,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='some_condition_var',
                                  operation=types_pb2.Comparison.OpEnum.EQUAL,
                                  bool_value=True,
                              )
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3,
                          ),
                      ),
                      types_pb2.Reaction(
                          reaction_instance_id=2,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='another_condition_var',
                                  operation=types_pb2.Comparison.OpEnum.GREATER_THAN,
                                  double_value=2.0,
                              )
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3,
                              stop_associated_action=True,
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=34
                          ),
                      ),
                  ],
              ),
          )
      )
      self.assertSequenceEqual(session._watcher_signal_flags[1], [flag])
    self.assertSequenceEqual(session._watcher_callbacks[1], [callback])

  def test_add_reaction(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    callback = mock.Mock()

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      flag = session.add_reaction(
          _actions.Action(3, 'bar', 'foo', None, []),
          _reactions.Condition.is_true('some_condition_var'),
          callback,
          'foo_signal',
      )

      mock_request_stream.write.assert_called_with(
          service_pb2.OpenSessionRequest(
              add_actions_and_reactions=types_pb2.ActionsAndReactions(
                  reactions=[
                      types_pb2.Reaction(
                          reaction_instance_id=1,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='some_condition_var',
                                  operation=types_pb2.Comparison.OpEnum.EQUAL,
                                  bool_value=True,
                              )
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3,
                              triggered_signal_name='foo_signal',
                          ),
                      ),
                  ],
              ),
          )
      )
      self.assertSequenceEqual(session._watcher_signal_flags[1], [flag])
    self.assertSequenceEqual(session._watcher_callbacks[1], [callback])

  def test_add_transition(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    callback = mock.Mock()

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      flag = session.add_transition(
          _actions.Action(3, 'bar', 'foo', None, iter([])),
          _actions.Action(4, 'bar', 'foo', None, iter([])),
          condition=_reactions.Condition.is_true('custom_variable'),
          callback=callback,
      )

      mock_request_stream.write.assert_called_with(
          service_pb2.OpenSessionRequest(
              add_actions_and_reactions=types_pb2.ActionsAndReactions(
                  reactions=[
                      types_pb2.Reaction(
                          reaction_instance_id=1,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='custom_variable',
                                  operation=types_pb2.Comparison.OpEnum.EQUAL,
                                  bool_value=True,
                              )
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3,
                              stop_associated_action=True,
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=4
                          ),
                      ),
                  ],
              ),
          )
      )
      self.assertSequenceEqual(session._watcher_signal_flags[1], [flag])
    self.assertSequenceEqual(session._watcher_callbacks[1], [callback])

  def test_add_reactions_to_proto_unsupported(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    reactions = [
        _reactions.Reaction(
            _reactions.Condition.is_true('some_condition_var'),
            [
                _reactions.StartActionInRealTime(start_action_id=20),
                _reactions.Condition.is_done(),
            ],
        ),
    ]

    with self.assertRaises(errors.Session.ActionError):
      session._add_reactions_to_proto(
          1, types_pb2.ActionsAndReactions(), reactions
      )

  def test_add_freestanding_reactions_request(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    callback = mock.Mock()
    flag = _reactions.EventFlag()
    reactions = [
        _reactions.Reaction(
            _reactions.Condition.is_true('some_condition_var'),
            [
                _reactions.StartActionInRealTime(start_action_id=20),
                _reactions.Event(flag),
            ],
        ),
        _reactions.Reaction(
            _reactions.Condition.is_greater_than('another_condition_var', 2.0),
            [
                _reactions.StartActionInRealTime(start_action_id=30),
                _reactions.TriggerCallback(callback),
            ],
        ),
    ]

    session.add_freestanding_reactions(reactions)
    self.assertSequenceEqual(session._watcher_callbacks[2], [callback])
    self.assertSequenceEqual(session._watcher_signal_flags[1], [flag])

  def test_add_action_with_part_name(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    with mock.patch.object(
        session, 'add_actions', autospec=True
    ) as mock_add_actions:
      action_id = 0
      action = session.add_action(
          _actions.Action(action_id, 'bar', 'foo', None, [])
      )
      self.assertEqual(action.id, action_id)
      mock_add_actions.assert_called_once_with([action])

  def test_add_action_with_slot_part_map(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    with mock.patch.object(
        session, 'add_actions', autospec=True
    ) as mock_add_actions:
      action_id = 12
      action = session.add_action(
          _actions.Action(action_id, 'bar', {'slot_name': 'foo'}, None, [])
      )
      self.assertEqual(action.id, action_id)
      mock_add_actions.assert_called_once_with([action])

  def test_add_actions(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    empty = empty_pb2.Empty()
    any_params = any_pb2.Any()
    any_params.Pack(empty)
    mock_request = service_pb2.OpenSessionRequest(
        add_actions_and_reactions=types_pb2.ActionsAndReactions(
            action_instances=[
                types_pb2.ActionInstance(
                    action_instance_id=0,
                    part_name='foo',
                    action_type_name='bar',
                    fixed_parameters=any_params,
                ),
                types_pb2.ActionInstance(
                    action_instance_id=1,
                    part_name='foo',
                    action_type_name='bar',
                    fixed_parameters=any_params,
                ),
            ],
            reactions=[],
        )
    )
    mock_reactions = iter([])

    with (
        mock.patch.object(
            session, '_request_stream', autospec=True
        ) as mock_request_stream,
        mock.patch.object(
            session, '_add_reactions_to_proto', autospec=True
        ) as mock_add_reactions_to_proto,
    ):
      action_0 = _actions.Action(0, 'bar', 'foo', empty, mock_reactions)
      action_1 = _actions.Action(1, 'bar', 'foo', empty, mock_reactions)
      session.add_actions([action_0, action_1])
      expected_add_reactions_to_proto_call_args = [
          mock.call(
              action_0.id,
              mock_request.add_actions_and_reactions,
              mock_reactions,
          ),
          mock.call(
              action_1.id,
              mock_request.add_actions_and_reactions,
              mock_reactions,
          ),
      ]
      self.assertSequenceEqual(
          expected_add_reactions_to_proto_call_args,
          mock_add_reactions_to_proto.call_args_list,
      )
      mock_request_stream.write.assert_called_once_with(mock_request)

  def test_add_action_sequence(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    action_1 = _actions.Action(1, 'action_1_type', 'my_part', None, [])
    action_2 = _actions.Action(2, 'action_2_type', 'my_part', None, [])
    action_3 = _actions.Action(3, 'action_3_type', 'my_part', None, [])

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      flag = session.add_action_sequence([action_1, action_2, action_3])

      mock_request_stream.write.assert_called_with(
          service_pb2.OpenSessionRequest(
              add_actions_and_reactions=types_pb2.ActionsAndReactions(
                  action_instances=[
                      types_pb2.ActionInstance(
                          action_instance_id=1,
                          part_name='my_part',
                          action_type_name='action_1_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                      types_pb2.ActionInstance(
                          action_instance_id=2,
                          part_name='my_part',
                          action_type_name='action_2_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                      types_pb2.ActionInstance(
                          action_instance_id=3,
                          part_name='my_part',
                          action_type_name='action_3_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                  ],
                  reactions=[
                      types_pb2.Reaction(
                          reaction_instance_id=1,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='xfa.is_done',
                                  operation=types_pb2.Comparison.EQUAL,
                                  bool_value=True,
                              ),
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=2
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=1, stop_associated_action=True
                          ),
                      ),
                      types_pb2.Reaction(
                          reaction_instance_id=2,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='xfa.is_done',
                                  operation=types_pb2.Comparison.EQUAL,
                                  bool_value=True,
                              ),
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=3
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=2, stop_associated_action=True
                          ),
                      ),
                      types_pb2.Reaction(
                          reaction_instance_id=3,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='xfa.is_done',
                                  operation=types_pb2.Comparison.EQUAL,
                                  bool_value=True,
                              ),
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3
                          ),
                      ),
                  ],
              ),
          )
      )

    self.assertSequenceEqual(session._watcher_signal_flags[3], [flag])

  def test_add_action_sequence_with_custom_condition(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    action_1 = _actions.Action(1, 'action_1_type', 'my_part', None, [])
    action_2 = _actions.Action(2, 'action_2_type', 'my_part', None, [])
    action_3 = _actions.Action(3, 'action_3_type', 'my_part', None, [])

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      flag = session.add_action_sequence([
          action_1,
          (
              action_2,
              _reactions.Condition.is_greater_than('my_variable', 15.3),
          ),
          (action_3, _reactions.Condition.is_true('xfa.is_settled')),
      ])

      mock_request_stream.write.assert_called_with(
          service_pb2.OpenSessionRequest(
              add_actions_and_reactions=types_pb2.ActionsAndReactions(
                  action_instances=[
                      types_pb2.ActionInstance(
                          action_instance_id=1,
                          part_name='my_part',
                          action_type_name='action_1_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                      types_pb2.ActionInstance(
                          action_instance_id=2,
                          part_name='my_part',
                          action_type_name='action_2_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                      types_pb2.ActionInstance(
                          action_instance_id=3,
                          part_name='my_part',
                          action_type_name='action_3_type',
                          fixed_parameters=any_pb2.Any(),
                      ),
                  ],
                  reactions=[
                      types_pb2.Reaction(
                          reaction_instance_id=1,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='xfa.is_done',
                                  operation=types_pb2.Comparison.EQUAL,
                                  bool_value=True,
                              ),
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=2
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=1, stop_associated_action=True
                          ),
                      ),
                      types_pb2.Reaction(
                          reaction_instance_id=2,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='my_variable',
                                  operation=types_pb2.Comparison.GREATER_THAN,
                                  double_value=15.3,
                              ),
                          ),
                          response=types_pb2.Response(
                              start_action_instance_id=3
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=2, stop_associated_action=True
                          ),
                      ),
                      types_pb2.Reaction(
                          reaction_instance_id=3,
                          condition=types_pb2.Condition(
                              comparison=types_pb2.Comparison(
                                  state_variable_name='xfa.is_settled',
                                  operation=types_pb2.Comparison.EQUAL,
                                  bool_value=True,
                              ),
                          ),
                          action_association=types_pb2.Reaction.ActionAssociation(
                              action_instance_id=3
                          ),
                      ),
                  ],
              ),
          )
      )
      self.assertSequenceEqual(session._watcher_signal_flags[3], [flag])

  def test_add_action_error(self):
    session = self._prepare_session_with_response(
        grpc.StatusCode.INVALID_ARGUMENT
    )

    with self.assertRaisesRegex(
        errors.Session.ActionError,
        'Adding actions failed with grpc.StatusCode.INVALID_ARGUMENT',
    ):
      session.add_action(_actions.Action(0, 'bar', 'foo', None, []))
    self._response_stream.cancel.assert_not_called()

  def test_add_action_aborted(self):
    session = self._prepare_session_with_response(grpc.StatusCode.ABORTED)

    with self.assertRaisesRegex(
        grpc.RpcError, 'Adding actions failed with grpc.StatusCode.ABORTED'
    ):
      session.add_action(_actions.Action(0, 'bar', 'foo', None, []))
    self.assertTrue(session._ended)

  def test_add_action_already_ended(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    session._ended = True

    with self.assertRaisesRegex(
        errors.Session.ActionError,
        'Cannot add actions to already ended session 1',
    ):
      session.add_action(_actions.Action(0, 'bar', 'foo', None, []))

  def test_start_action(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      session.start_action(0)
      mock_request = service_pb2.OpenSessionRequest(
          start_actions_request=service_pb2.OpenSessionRequest.StartActionsRequestData(
              action_instance_ids=[0], stop_active_actions=True
          )
      )
      mock_request_stream.write.assert_called_once_with(mock_request)

  def test_start_action_failed(self):
    session = self._prepare_session_with_response(
        grpc.StatusCode.FAILED_PRECONDITION
    )
    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      with self.assertRaisesRegex(
          errors.Session.ActionError,
          'Starting an action failed with grpc.StatusCode.FAILED_PRECONDITION',
      ):
        session.start_action(0)
      mock_request = service_pb2.OpenSessionRequest(
          start_actions_request=service_pb2.OpenSessionRequest.StartActionsRequestData(
              action_instance_ids=[0], stop_active_actions=True
          )
      )
      mock_request_stream.write.assert_called_once_with(mock_request)

  def test_start_action_already_ended(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    session._ended = True

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      with self.assertRaisesRegex(
          errors.Session.ActionError,
          'Cannot start action in already ended session 1',
      ):
        session.start_action(0)
      mock_request_stream.write.assert_not_called()

  def test_start_action_and_wait(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)

    with mock.patch.object(
        session, '_request_stream', autospec=True
    ) as mock_request_stream:
      session.start_action_and_wait(
          _actions.Action(3, 'bar', 'foo', None, []),
          timeout_s=2.0,
      )

      add_reaction_request = service_pb2.OpenSessionRequest(
          add_actions_and_reactions=types_pb2.ActionsAndReactions(
              reactions=[
                  types_pb2.Reaction(
                      reaction_instance_id=1,
                      condition=types_pb2.Condition(
                          comparison=types_pb2.Comparison(
                              state_variable_name='xfa.is_done',
                              operation=types_pb2.Comparison.OpEnum.EQUAL,
                              bool_value=True,
                          )
                      ),
                      action_association=types_pb2.Reaction.ActionAssociation(
                          action_instance_id=3,
                      ),
                  ),
              ],
          ),
      )

      start_request = service_pb2.OpenSessionRequest(
          start_actions_request=service_pb2.OpenSessionRequest.StartActionsRequestData(
              action_instance_ids=[3],
              stop_active_actions=True,
          )
      )

      mock_request_stream.write.assert_has_calls(
          [
              mock.call(add_reaction_request),
              mock.call(start_request),
          ],
          any_order=False,
      )

  @mock.patch.object(_session, 'Stream', autospec=True)
  def test_open_stream(self, mock_stream_cls):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    self.assertIsNotNone(session.open_stream(0, 'baz'))
    mock_stream_cls.assert_called_once_with(
        session._stub, session._session_id, 0, 'baz'
    )

  @mock.patch.object(_session, 'Stream', autospec=True)
  def test_open_stream_error(self, mock_stream_cls):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    mock_stream_cls.side_effect = grpc.RpcError('uh oh')
    with self.assertRaises(grpc.RpcError):
      session.open_stream(0, 'baz')
    mock_stream_cls.assert_called_once_with(
        session._stub, session._session_id, 0, 'baz'
    )
    self.assertTrue(session._ended)

  @mock.patch.object(_session, 'Stream', autospec=True)
  def test_open_stream_already_ended(self, mock_stream_cls):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    session._ended = True
    with self.assertRaises(errors.Session.ActionError):
      session.open_stream(0, 'baz')
    mock_stream_cls.assert_not_called()

  def test_close_stream(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    stream = mock.create_autospec(_session.Stream)
    stream.end.return_value = True
    stream.session_id = 1
    session._action_streams_set = {stream}

    res = session.close_stream(stream)

    self.assertTrue(res)
    stream.end.assert_called_once_with()
    self.assertNotIn(stream, session._action_streams_set)

    # Removing the stream and closing again should still return True.
    self.assertTrue(session.close_stream(stream))

  def test_close_stream_from_another_session_error(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    stream = mock.create_autospec(_session.Stream)
    stream.id = 0
    stream.session_id = 10
    session._action_streams_set = {stream}

    with self.assertRaises(errors.Session.ActionError):
      session.close_stream(stream)
    stream.end.assert_not_called()

  def test_watch_reaction_responses(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    # Set up two reaction events, 1 and 2.
    session._watcher_response_stream = iter([
        service_pb2.WatchReactionsResponse(
            timestamp=timestamp_pb2.Timestamp(),
            reaction_event=types_pb2.ReactionEvent(
                previous_action_instance_id=1,
                current_action_instance_id=1,
                reaction_id=1,
            ),
        ),
        service_pb2.WatchReactionsResponse(
            timestamp=timestamp_pb2.Timestamp(),
            reaction_event=types_pb2.ReactionEvent(
                previous_action_instance_id=None,
                current_action_instance_id=None,
                reaction_id=2,
            ),
        ),
        service_pb2.WatchReactionsResponse(
            timestamp=timestamp_pb2.Timestamp(),
            reaction_event=types_pb2.ReactionEvent(
                previous_action_instance_id=3,
                current_action_instance_id=3,
                reaction_id=3,
            ),
        ),
    ])

    # Add callbacks to be triggered for 1 and 2 but not for 3, and a dummy 4.
    session._watcher_callbacks = collections.defaultdict(list)
    session._watcher_callbacks[1] = [mock.Mock(), mock.Mock()]
    session._watcher_callbacks[2] = [mock.Mock()]
    session._watcher_callbacks[4] = [mock.Mock()]
    # Add signals to be flagged for 3 but not for 1 and 2, and a dummy 4.
    session._watcher_signal_flags = collections.defaultdict(list)
    session._watcher_signal_flags[3] = [
        mock.create_autospec(_reactions.EventFlag),
        mock.create_autospec(_reactions.EventFlag),
    ]
    session._watcher_signal_flags[4] = [
        mock.create_autospec(_reactions.EventFlag)
    ]

    session._watch_reaction_responses()
    for callback in session._watcher_callbacks[1]:
      callback.assert_called_with(datetime.datetime(1970, 1, 1), 1, 1)
    for callback in session._watcher_callbacks[2]:
      callback.assert_called_with(datetime.datetime(1970, 1, 1), None, None)
    for callback in session._watcher_callbacks[4]:
      callback.assert_not_called()
    for signal_flag in session._watcher_signal_flags[3]:
      signal_flag.signal.assert_called_once_with()
    for signal_flag in session._watcher_signal_flags[4]:
      signal_flag.signal.assert_not_called()
    self.assertIsNone(session.get_reaction_responses_error())

  def test_watch_reaction_responses_cancelled(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    error = grpc.RpcError()
    error.code = mock.Mock()
    error.code.return_value = grpc.StatusCode.CANCELLED
    session._watcher_response_stream = _RaiseExceptionIterable(error)

    session._watch_reaction_responses()
    self.assertIsNone(session.get_reaction_responses_error())
    error.code.assert_called_once_with()

  def test_watch_reaction_responses_error(self):
    session = self._prepare_session_with_response(grpc.StatusCode.OK)
    error = grpc.RpcError()
    error.code = mock.Mock()
    error.code.return_value = grpc.StatusCode.ABORTED
    session._watcher_response_stream = _RaiseExceptionIterable(error)

    session._watch_reaction_responses()
    self.assertIsNotNone(session.get_reaction_responses_error())
    self.assertEqual(
        session.get_reaction_responses_error().code.return_value,
        grpc.StatusCode.ABORTED,
    )
    error.code.assert_called_once_with()
    with self.assertRaises(grpc.RpcError):
      session.end()

  def test_get_latest_output_calls_correct_grpc_method(self):
    self._prepare_initial_response()
    session = _session.Session(self._stub, ['foo'])
    expected_output = streaming_output_pb2.StreamingOutput(timestamp_ns=128)

    action_id = 123
    self._stub.GetLatestStreamingOutput.return_value = (
        service_pb2.GetLatestStreamingOutputResponse(output=expected_output)
    )
    self.assertEqual(
        expected_output,
        session.get_latest_output(
            action_id=action_id, timeout=datetime.timedelta.max
        ),
    )
    self._stub.GetLatestStreamingOutput.assert_called_once()
    mock_args, mock_kwargs = self._stub.GetLatestStreamingOutput.call_args
    self.assertEqual(
        mock_args[0],
        service_pb2.GetLatestStreamingOutputRequest(
            action_id=action_id, session_id=session._session_id
        ),
    )
    self.assertEqual(
        mock_kwargs['timeout'], datetime.timedelta.max.total_seconds()
    )


class StreamTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    # Use `MagicMock` instead of the more constrained autospec for
    # `service_pb2_grpc.IconApiStub` since the auto-generated interface doesn't
    # contain the OpenWriteStream attribute.
    self._stub = mock.MagicMock()
    # As above, use `MagicMock` instead of `grpc.StreamStreamMultiCallable`
    # since it's missing the __next__ attribute.
    self._response_stream = mock.MagicMock()
    self._stub.OpenWriteStream.return_value = self._response_stream

  def _prepare_initial_response(self, response_code=grpc.StatusCode.OK):
    response = mock.create_autospec(service_pb2.OpenWriteStreamResponse)
    response.add_stream_response.status.code = response_code.value[0]
    self._response_stream.__next__.return_value = response

  def test_start_stream(self):
    self._prepare_initial_response()
    _session.Stream(self._stub, 2, 0, 'baz')
    self._response_stream.cancel.assert_not_called()

  def test_start_stream_error(self):
    self._prepare_initial_response(grpc.StatusCode.CANCELLED)
    with self.assertRaisesRegex(
        errors.Session.StreamError,
        'Opening stream failed with grpc.StatusCode.CANCELLED',
    ):
      _session.Stream(self._stub, 2, 0, 'baz')
    self._response_stream.cancel.assert_called_with()

  def test_start_stream_abort_error(self):
    self._prepare_initial_response(grpc.StatusCode.ABORTED)

    with self.assertRaisesRegex(
        grpc.RpcError, 'Opening stream failed with grpc.StatusCode.ABORTED'
    ):
      _session.Stream(self._stub, 2, 0, 'baz')
    self._response_stream.cancel.assert_called_with()

  def test_write(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    response = mock.create_autospec(service_pb2.OpenWriteStreamResponse)
    response.write_value_response.code = grpc.StatusCode.OK.value[0]
    self._response_stream.__next__.return_value = response

    stream.write(empty_pb2.Empty())

  def test_write_error(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    response = mock.create_autospec(service_pb2.OpenWriteStreamResponse)
    response.write_value_response.code = grpc.StatusCode.UNAVAILABLE.value[0]
    self._response_stream.__next__.return_value = response

    with self.assertRaisesRegex(
        errors.Session.StreamError,
        'Writing to stream .* failed with grpc.StatusCode.UNAVAILABLE',
    ):
      stream.write(empty_pb2.Empty())

  def test_write_to_ended_stream(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    stream._ended = True

    with self.assertRaisesRegex(
        errors.Session.StreamError, 'Cannot write to already ended stream .*'
    ):
      stream.write(empty_pb2.Empty())

  def test_end(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    self.assertFalse(stream._ended)

    self.assertTrue(stream.end())
    self.assertTrue(stream._ended)

  def test_end_unsuccessful(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    self.assertFalse(stream._ended)
    error = grpc.RpcError()
    error.code = mock.Mock()
    error.code.return_value = grpc.StatusCode.INTERNAL
    stream._response_stream = _RaiseExceptionIterable(error)

    self.assertFalse(stream.end())
    self.assertFalse(stream._ended)

  def test_end_already_ended(self):
    self._prepare_initial_response()
    stream = _session.Stream(self._stub, 2, 0, 'baz')
    stream.end()
    self.assertTrue(stream._ended)

    self.assertTrue(stream.end())
    self.assertTrue(stream._ended)


class RequestIteratorTest(absltest.TestCase):

  def test_read_write_request(self):
    stream = _session._RequestIterator()
    stream.write('foo')
    self.assertEqual(next(stream), 'foo')

  def test_end_requests(self):
    stream = _session._RequestIterator()
    self.assertFalse(stream._ended)
    stream.write('foo')
    self.assertFalse(stream._queue.empty())

    stream.end()

    # Ending should prevent further reads/writes.
    self.assertTrue(stream._ended)
    with self.assertRaises(StopIteration):
      next(stream)
    stream.write('foo')
    self.assertTrue(stream._queue.empty())


class _RaiseExceptionIterable:
  """Helper class for mocking raising exceptions during iteration."""

  def __init__(self, exception):
    self.exception = exception

  def __iter__(self):
    raise self.exception


if __name__ == '__main__':
  absltest.main()
