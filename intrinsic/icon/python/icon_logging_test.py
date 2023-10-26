# Copyright 2023 Intrinsic Innovation LLC

from absl.testing import absltest
from google.protobuf import text_format
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.icon.python import icon_logging
from intrinsic.logging.proto import log_item_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.proto import vector3_pb2


class IconLoggingTest(absltest.TestCase):

  def test_unpack_streaming_output(self):
    item = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutputWithMetadata()
    expected_payload = text_format.Parse(
        'x:1.0 y:2.0 z: 3.0',
        vector3_pb2.Vector3(),
    )
    streamed_output.output.timestamp_ns = 1234
    streamed_output.output.payload.Pack(expected_payload)
    item.payload.any.Pack(streamed_output)

    (unpacked_payload, timestamp) = (
        icon_logging.unpack_streaming_output_logitem(item, vector3_pb2.Vector3)
    )

    self.assertEqual(expected_payload, unpacked_payload)
    self.assertEqual(timestamp, 1234 * 1e-9)

  def test_unpack_streaming_output_fails_for_other_item_payload(self):
    item = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutput()
    payload = text_format.Parse(
        'x:1.0 y:2.0 z: 3.0',
        vector3_pb2.Vector3(),
    )
    streamed_output.payload.Pack(payload)
    item.payload.any.Pack(streamed_output)

    with self.assertRaisesRegex(TypeError, 'Item.payload.any'):
      _ = icon_logging.unpack_streaming_output_logitem(
          item, vector3_pb2.Vector3
      )

  def test_unpack_streaming_output_fails_for_other_stream_payload(self):
    item = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutputWithMetadata()
    payload = text_format.Parse(
        'position:{x:1.0 y:2.0 z: 3.0}',
        pose_pb2.Pose(),
    )
    streamed_output.output.payload.Pack(payload)
    item.payload.any.Pack(streamed_output)

    with self.assertRaises(TypeError) as e:
      _ = icon_logging.unpack_streaming_output_logitem(
          item, vector3_pb2.Vector3
      )
    self.assertIn(
        'StreamingOutputWithMetadata.output.payload', str(e.exception)
    )

  def test_unpack_two_unpack_streaming_outputs(self):
    items = []
    item_1 = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutputWithMetadata()
    expected_payload_1 = text_format.Parse(
        'x:1.0 y:2.0 z: 3.0',
        vector3_pb2.Vector3(),
    )
    streamed_output.output.timestamp_ns = 1234
    streamed_output.output.payload.Pack(expected_payload_1)
    item_1.payload.any.Pack(streamed_output)
    items.append(item_1)

    item_2 = log_item_pb2.LogItem()
    streamed_output = streaming_output_pb2.StreamingOutputWithMetadata()
    expected_payload_2 = text_format.Parse(
        'x:4.0 y:5.0 z: 6.0',
        vector3_pb2.Vector3(),
    )
    streamed_output.output.timestamp_ns = 1235
    streamed_output.output.payload.Pack(expected_payload_2)
    item_2.payload.any.Pack(streamed_output)
    items.append(item_2)

    vectors, timestamps = icon_logging.unpack_streaming_outputs(
        items, vector3_pb2.Vector3
    )

    self.assertEqual(expected_payload_1, vectors[0])
    self.assertEqual(expected_payload_2, vectors[1])
    self.assertEqual(timestamps[0], 1234 * 1e-9)
    self.assertEqual(timestamps[1], 1235 * 1e-9)

  def test_action_topic_name(self):
    self.assertEqual(
        icon_logging.action_topic_name('robot', 2),
        '/icon/robot/output_streams/action_2',
    )


if __name__ == '__main__':
  absltest.main()
