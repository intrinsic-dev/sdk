# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.solutions.structured_logging."""

import datetime
from typing import Optional
from unittest import mock

from absl.testing import absltest
from google.protobuf import empty_pb2
from google.protobuf import message as proto_message
from google.protobuf import text_format
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.logging.proto import log_item_pb2
from intrinsic.logging.proto import logger_service_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.proto import vector3_pb2
from intrinsic.solutions import structured_logging
import pandas as pd


# Make sure all log items are considered.
_TIMESTAMP = 2147483647


class StructuredLoggingTest(absltest.TestCase):

  def _create_mock_stub(
      self, event_source: str, data: list[log_item_pb2.LogItem]
  ):
    stub = mock.MagicMock()
    list_log_sources_response = logger_service_pb2.ListLogSourcesResponse()
    list_log_sources_response.event_sources.append(event_source)
    stub.ListLogSources.return_value = list_log_sources_response

    get_log_items_response = logger_service_pb2.GetLogItemsResponse()
    for item in data:
      item.metadata.acquisition_time.seconds = _TIMESTAMP
      if item.metadata.event_source == event_source:
        get_log_items_response.log_items.append(item)
    stub.GetLogItems.return_value = get_log_items_response

    return stub

  def mock_read(
      self, event_source: str, data: list[log_item_pb2.LogItem]
  ) -> structured_logging.DataSource:
    stub = self._create_mock_stub(event_source, data)

    reader = structured_logging.EventSourceReader(stub, event_source)
    return reader.read(seconds_to_read=60)

  def test_get_num_events(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "some.event.source"
>
blob_payload <
  blob_id: "/tmp/a.png"
>""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "some.event.source"
>
blob_payload <
  blob_id: "/tmp/b.png"
>""",
            log_item_pb2.LogItem(),
        ),
    ]
    source = self.mock_read('some.event.source', data)
    self.assertEqual(source.num_events, 2)

  def test_get_event_sources(self):
    stub = mock.MagicMock()
    response = logger_service_pb2.ListLogSourcesResponse()
    response.event_sources.append('ev1')
    response.event_sources.append('ev2')
    stub.ListLogSources.return_value = response
    logs = structured_logging.StructuredLogs(stub)

    result = logs.get_event_sources()

    self.assertListEqual(result, ['ev1', 'ev2'])

  def test_set_log_options(self):
    stub = mock.MagicMock()
    stub.SetLogOptions.return_value = logger_service_pb2.SetLogOptionsResponse()
    event_source = 'ev1'
    log_options = logger_service_pb2.LogOptions(max_buffer_size=10)
    logs = structured_logging.StructuredLogs(stub)

    result = logs.set_log_options(event_source, log_options)

    # At least sends the expected argument type
    self.assertEqual(
        type(stub.SetLogOptions.call_args.args[0]),
        logger_service_pb2.SetLogOptionsRequest,
    )
    # Sends the expected buffer size
    self.assertEqual(
        stub.SetLogOptions.call_args.args[0].log_options.max_buffer_size,
        10,
    )
    # Receives the expected return value
    self.assertIsNone(result)

  def test_get_log_options(self):
    stub = mock.MagicMock()
    log_options = logger_service_pb2.LogOptions(max_buffer_size=10)
    response = logger_service_pb2.GetLogOptionsResponse(log_options=log_options)
    stub.GetLogOptions.return_value = response
    logs = structured_logging.StructuredLogs(stub)

    result = logs.get_log_options('ev1')

    stub.GetLogOptions.assert_called_once()
    # At least sends the expected argument type
    self.assertEqual(
        type(stub.GetLogOptions.call_args.args[0]),
        logger_service_pb2.GetLogOptionsRequest,
    )
    # At least receives expected response type
    self.assertEqual(type(result), logger_service_pb2.LogOptions)
    # Receives the expected buffer size
    self.assertEqual(result.max_buffer_size, 10)

  def test_peek(self):
    stub = mock.MagicMock()
    list_log_sources_response = logger_service_pb2.ListLogSourcesResponse()
    list_log_sources_response.event_sources.append('ev1')
    stub.ListLogSources.return_value = list_log_sources_response

    response = logger_service_pb2.GetMostRecentItemResponse()
    response.item.metadata.event_source = 'ev1'
    stub.GetMostRecentItem.return_value = response
    logs = structured_logging.StructuredLogs(stub)
    item = logs.ev1.peek()
    self.assertEqual(item.metadata.event_source, 'ev1')

  def test_query(self):
    """Tests that a simple query requests to the logger works."""
    pb1 = text_format.Parse(
        """
metadata <
  event_source: "event_source"
>
payload <
  skills_execution_summary <
    error_code: 1
  >
>
""",
        log_item_pb2.LogItem(),
    )
    stub = mock.MagicMock()
    response = logger_service_pb2.GetLogItemsResponse()
    response.log_items.append(pb1)
    stub.GetLogItems.return_value = response
    logs = structured_logging.StructuredLogs(stub)

    seconds_to_read = 1234
    logs.query('event_source', seconds_to_read=seconds_to_read)

    stub.GetLogItems.assert_called_once()
    get_request = stub.GetLogItems.call_args.args[0]
    get_request_delta = (
        get_request.end_time.ToDatetime() - get_request.start_time.ToDatetime()
    )
    self.assertEqual(
        get_request_delta, datetime.timedelta(seconds=seconds_to_read)
    )

  def test_query_for_time_range(self):
    """Tests that a simple query requests to the logger works."""
    pb1 = text_format.Parse(
        """
metadata <
  event_source: "mock_event_source"
>
payload <
  skills_execution_summary <
    error_code: 1
  >
>
""",
        log_item_pb2.LogItem(),
    )
    stub = mock.MagicMock()
    response = logger_service_pb2.GetLogItemsResponse()
    response.log_items.append(pb1)
    stub.GetLogItems.return_value = response
    logs = structured_logging.StructuredLogs(stub)

    # Arbitrary test time
    req_end = datetime.datetime.strptime('7/20/1969 20:17', '%m/%d/%Y %H:%M')
    req_start = req_end - datetime.timedelta(seconds=10)

    items = logs.query_for_time_range('query_event_source', req_start, req_end)

    stub.GetLogItems.assert_called_once()
    get_request = stub.GetLogItems.call_args.args[0]
    self.assertIsInstance(get_request, logger_service_pb2.GetLogItemsRequest)
    self.assertEqual(get_request.event_sources, ['query_event_source'])
    call_start = get_request.start_time.ToDatetime()
    self.assertEqual(call_start - req_start, datetime.timedelta(seconds=0))

    self.assertLen(items, 1)
    self.assertEqual(items[0].metadata.event_source, 'mock_event_source')
    self.assertEqual(items[0].payload.skills_execution_summary.error_code, 1)

  def test_truncated_query_warning(self):
    """Tests proper warning sent if response is truncated."""
    pb1 = text_format.Parse(
        """
metadata <
  event_source: "mock_event_source"
>
payload <
  skills_execution_summary <
    error_code: 1
  >
>
""",
        log_item_pb2.LogItem(),
    )
    stub = mock.MagicMock()
    response = logger_service_pb2.GetLogItemsResponse()
    response.log_items.append(pb1)
    response.truncated = True
    response.truncation_cause = 'mock cause'
    stub.GetLogItems.return_value = response
    logs = structured_logging.StructuredLogs(stub)

    # Response num items is lower than expected, mocking response byte limit
    with self.assertLogs(level='WARNING') as cm:
      logs.query('event_source', max_num_items=1)
      self.assertRegex(cm.output[0], 'mock cause')

  def test_log(self):
    pb1 = text_format.Parse(
        """
metadata <
  event_source: "event_source"
>
payload <
  skills_execution_summary <
    error_code: 1
  >
>
""",
        log_item_pb2.LogItem(),
    )
    stub = mock.MagicMock()
    response = empty_pb2.Empty()
    stub.Log.return_value = response
    request = logger_service_pb2.LogRequest()
    metadata = request.item.metadata
    metadata.event_source = 'test_request.info'
    metadata.acquisition_time.GetCurrentTime()
    request.item.CopyFrom(pb1)
    logs = structured_logging.StructuredLogs(stub)
    logs.log(request)

  def test_dir_returns_methods_and_sources(self):
    stub = mock.MagicMock()
    response = logger_service_pb2.ListLogSourcesResponse()
    response.event_sources.append('ev1')
    response.event_sources.append('ev2')
    stub.ListLogSources.return_value = response

    logs = structured_logging.StructuredLogs(stub)

    self.assertCountEqual(
        logs.__dir__(),
        [
            'connect',
            'for_solution',
            'ev1',
            'ev2',
            'get_event_source',
            'get_event_sources',
            'get_log_options',
            'log',
            'query',
            'query_for_time_range',
            'set_log_options',
            'sync_and_rotate_logs',
        ],
    )

  def test_read_timewindow(self):
    # This test is quite weak because the time window filtering is done on the
    # server which is mocked out here. This only tests the interface itself.
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "ev1"
>
blob_payload <
  blob_id: "/tmp/a.png"
>""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "ev1"
>
blob_payload <
  blob_id: "/tmp/b.png"
>""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('ev1', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.ev1.read(
        time_window=structured_logging.EventSourceWindow(
            start_time=datetime.datetime(2023, 1, 1, 1, 1, 1),
            end_time=datetime.datetime(2023, 1, 1, 1, 2, 1),
        ),
        sampling_period_ms=100,
        max_num_items=500,
    )

    self.assertEqual(items.num_events, 2)

  def test_read_base_t_tip_sensed(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1200000000
            base_t_tip_sensed:<
                pos: <
                    x: 1 y: 2 z: 3
                >
                rot: <
                  qx: 0.1 qy: 0.2 qz: 0.3 qw: 0.4
                >
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1300000000
            base_t_tip_sensed:<
                pos: <
                    x: 1 y: 2 z: 4
                >
                rot: <
                  qw: 1.0
                >
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    poses = items.my_robot.get_base_t_tip_sensed()

    pd.testing.assert_frame_equal(
        poses['pos'],
        pd.DataFrame(
            [
                [1.0, 2.0, 3.0],
                [1.0, 2.0, 4.0],
            ],
            columns=[
                'x',
                'y',
                'z',
            ],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

    pd.testing.assert_frame_equal(
        poses['rot'],
        pd.DataFrame(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.0, 0.0, 0.0, 1.0],
            ],
            columns=[
                'qx',
                'qy',
                'qz',
                'qw',
            ],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

  def test_read_joint_states(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 1
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1200000000
            joint_states: <
              position_commanded_last_cycle: 1.0
              position_sensed: 1.1
            >
            joint_states: <
              position_commanded_last_cycle: 2.0
              position_sensed: 2.1
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 2
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1300000000
            joint_states: <
              position_commanded_last_cycle: 3.0
              position_sensed: 3.1
            >
            joint_states: <
              position_commanded_last_cycle: 4.0
              position_sensed: 4.1
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    joint_states = items.my_robot.get_joint_states()

    pd.testing.assert_frame_equal(
        joint_states['position_sensed'],
        pd.DataFrame(
            [[1.1, 2.1], [3.1, 4.1]],
            columns=['0', '1'],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )
    pd.testing.assert_frame_equal(
        joint_states['position_commanded_last_cycle'],
        pd.DataFrame(
            [[1.0, 2.0], [3.0, 4.0]],
            columns=['0', '1'],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

    pd.testing.assert_frame_equal(
        joint_states['skill_log_id'],
        pd.DataFrame(
            [[12345], [12345]],
            columns=['0'],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )
    pd.testing.assert_frame_equal(
        joint_states['icon_action_id'],
        pd.DataFrame(
            [[1], [2]],
            columns=['0'],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

  def test_get_event_source(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "ev1"
>
blob_payload <
  blob_id: "/tmp/a.png"
>""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('ev1', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.get_event_source('ev1').read(seconds_to_read=10)

    self.assertEqual(items.num_events, 1)

  def make_streaming_output_log_item(
      self,
      *,
      timestamp_ns: int,
      event_source: str,
      payload: proto_message.Message,
      action_id: Optional[int] = None,
  ) -> log_item_pb2.LogItem:
    item = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutputWithMetadata()
    streamed_output.output.timestamp_ns = timestamp_ns
    streamed_output.output.payload.Pack(payload)
    item.payload.any.Pack(streamed_output)
    item.metadata.event_source = event_source
    item.context.skill_id = 37
    if action_id is not None:
      item.context.icon_action_id = action_id
    return item

  def test_read_streaming_vector_output(self):
    items = []
    items.append(
        self.make_streaming_output_log_item(
            timestamp_ns=1234000000,
            event_source='action_output',
            payload=text_format.Parse(
                'x:1.0 y:2.0 z: 3.0',
                vector3_pb2.Vector3(),
            ),
        )
    )

    items.append(
        self.make_streaming_output_log_item(
            timestamp_ns=1235000000,
            event_source='action_output',
            payload=text_format.Parse(
                'x:4.0 y:5.0 z: 6.0',
                vector3_pb2.Vector3(),
            ),
            action_id=1234,
        )
    )

    stub = self._create_mock_stub('action_output', items)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.action_output.read(seconds_to_read=10)
    vectors = items.get_payload(vector3_pb2.Vector3)

    pd.testing.assert_frame_equal(
        vectors,
        pd.DataFrame(
            [[1.0, 2.0, 3.0, 37, None], [4.0, 5.0, 6.0, 37, 1234]],
            columns=['x', 'y', 'z', 'skill_log_id', 'icon_action_id'],
            index=pd.Index([1.234, 1.235], name='time_s'),
        ),
    )

  def test_read_streaming_pose_output(self):
    items = []
    items.append(
        self.make_streaming_output_log_item(
            timestamp_ns=1234000000,
            event_source='action_output',
            payload=text_format.Parse(
                """
        position: <
          x:1.0 y:2.0 z: 3.0
        >
        orientation: <
          x:1.0 y:2.0 z: 3.0 w: 4.0
        >
        """,
                pose_pb2.Pose(),
            ),
        )
    )

    items.append(
        self.make_streaming_output_log_item(
            timestamp_ns=1235000000,
            event_source='action_output',
            payload=text_format.Parse(
                """
        position: <
          x:1.1 y:2.1 z: 3.1
        >
        orientation: <
          x:1.0 y:2.0 z: 3.0 w: 4.0
        >
        """,
                pose_pb2.Pose(),
            ),
        )
    )

    stub = self._create_mock_stub('action_output', items)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.action_output.read(seconds_to_read=10)
    vectors = items.get_payload(pose_pb2.Pose)

    pd.testing.assert_frame_equal(
        vectors['position'],
        pd.DataFrame(
            [
                [1.0, 2.0, 3.0],
                [1.1, 2.1, 3.1],
            ],
            columns=[
                'x',
                'y',
                'z',
            ],
            index=pd.Index([1.234, 1.235], name='time_s'),
        ),
    )
    pd.testing.assert_frame_equal(
        vectors['orientation'],
        pd.DataFrame(
            [
                [1.0, 2.0, 3.0, 4.0],
                [1.0, 2.0, 3.0, 4.0],
            ],
            columns=[
                'x',
                'y',
                'z',
                'w',
            ],
            index=pd.Index([1.234, 1.235], name='time_s'),
        ),
    )

  def test_read_rangefinder_status(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 1
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'rangefinder'
        value: <
            timestamp_ns: 1200000000
            rangefinder_status: <
              distance: 1.0
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 2
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'rangefinder'
        value: <
            timestamp_ns: 1300000000
            rangefinder_status: <
              distance: 2.3
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    rangefinder_status = items.rangefinder.get_rangefinder_status()

    pd.testing.assert_frame_equal(
        rangefinder_status,
        pd.DataFrame(
            [[1.0, 12345, 1], [2.3, 12345, 2]],
            columns=['distance', 'skill_log_id', 'icon_action_id'],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

  def test_read_wrench(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 1
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1200000000
            wrench_at_tip: <
              x: 1.0
              y: 2.0
              z: 3.0
              rx: 4.0
              ry: 5.0
              rz: 6.0
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
context <
  skill_id: 12345
  icon_action_id: 2
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1300000000
            wrench_at_tip: <
              x: 1.1
              y: 2.1
              z: 3.1
              rx: 4.1
              ry: 5.1
              rz: 6.1
            >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    wrench = items.my_robot.get_wrench_at_tip()

    pd.testing.assert_frame_equal(
        wrench,
        pd.DataFrame(
            [
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 12345, 1],
                [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 12345, 2],
            ],
            columns=[
                'x',
                'y',
                'z',
                'rx',
                'ry',
                'rz',
                'skill_log_id',
                'icon_action_id',
            ],
            index=pd.Index([1.2, 1.3], name='time_s'),
        ),
    )

  def make_base_t_tip_sensed_item(
      self,
      *,
      event_source: str,
      timestamp_ns: int,
      x: float,
      y: float,
      z: float,
  ) -> log_item_pb2.LogItem:
    return text_format.Parse(
        f"""
metadata <
  event_source: '{event_source}'
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: {timestamp_ns}
            base_t_tip_sensed:<
                pos: <
                    x: {x} y: {y} z: {z}
                >
            >
        >
    >
  >
>
""",
        log_item_pb2.LogItem(),
    )

  def test_read_every_n_item(self):
    data = [
        self.make_base_t_tip_sensed_item(
            event_source='robot_status',
            timestamp_ns=1200000000,
            x=1.0,
            y=2.0,
            z=3.0,
        ),
        self.make_base_t_tip_sensed_item(
            event_source='robot_status',
            timestamp_ns=1300000000,
            x=1.0,
            y=2.0,
            z=4.0,
        ),
        self.make_base_t_tip_sensed_item(
            event_source='robot_status',
            timestamp_ns=1400000000,
            x=1.0,
            y=2.0,
            z=5.0,
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    poses = items.my_robot.get_base_t_tip_sensed(every_n=2)

    pd.testing.assert_frame_equal(
        poses['pos'],
        pd.DataFrame(
            [
                [1.0, 2.0, 3.0],
                [1.0, 2.0, 5.0],
            ],
            columns=[
                'x',
                'y',
                'z',
            ],
            index=pd.Index([1.2, 1.4], name='time_s'),
        ),
    )

  def make_joint_states_item(
      self, *, event_source: str, timestamp_ns: int, position_sensed: float
  ) -> log_item_pb2.LogItem:
    return text_format.Parse(
        f"""
  metadata <
    event_source: '{event_source}'
  >
  payload:<
    icon_robot_status: <
      status_map: <
          key: 'my_robot'
          value: <
              timestamp_ns: {timestamp_ns}
              joint_states: <
                position_sensed: {position_sensed}
              >
              joint_states: <
                position_sensed: {position_sensed}
              >
          >
      >
    >
  >
  """,
        log_item_pb2.LogItem(),
    )

  def test_read_ever_n_repeated_item(self):
    data = [
        self.make_joint_states_item(
            event_source='robot_status',
            timestamp_ns=1200000000,
            position_sensed=1.1,
        ),
        self.make_joint_states_item(
            event_source='robot_status',
            timestamp_ns=1300000000,
            position_sensed=2.1,
        ),
        self.make_joint_states_item(
            event_source='robot_status',
            timestamp_ns=1400000000,
            position_sensed=3.1,
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)
    joint_states = items.my_robot.get_joint_states(every_n=2)

    pd.testing.assert_frame_equal(
        joint_states['position_sensed'],
        pd.DataFrame(
            [[1.1, 1.1], [3.1, 3.1]],
            columns=['0', '1'],
            index=pd.Index([1.2, 1.4], name='time_s'),
        ),
    )

  def test_part_status_dir_shows_get_methods(self):
    data = [
        text_format.Parse(
            """
metadata <
  event_source: "robot_status"
>
payload:<
  icon_robot_status: <
    status_map: <
        key: 'my_robot'
        value: <
            timestamp_ns: 1300000000
            wrench_at_tip: <
              x: 1.1
              y: 2.1
              z: 3.1
              rx: 4.1
              ry: 5.1
              rz: 6.1
            >
            joint_states: <
                position_sensed: 1.0
              >
              joint_states: <
                position_sensed: 2.0
              >
        >
    >
  >
>
""",
            log_item_pb2.LogItem(),
        ),
    ]
    stub = self._create_mock_stub('robot_status', data)
    logs = structured_logging.StructuredLogs(stub)

    items = logs.robot_status.read(seconds_to_read=10)

    self.assertCountEqual(
        items.my_robot.__dir__(),
        [
            'get_joint_states',
            'get_timestamp_ns',
            'get_wrench_at_tip',
            'log_items',
            'num_events',
        ],
    )

  def test_format_robot_status_event_source(self):
    formatted = structured_logging.format_event_source(
        '/icon/robot-sim/robot_status'
    )

    self.assertEqual(formatted, 'icon_robot_sim_robot_status')


if __name__ == '__main__':
  absltest.main()
