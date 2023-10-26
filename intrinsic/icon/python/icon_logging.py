# Copyright 2023 Intrinsic Innovation LLC

"""Helpers to handle ICON logs."""

from typing import List, Tuple, Type, TypeVar

from google.protobuf import message as proto_message
from intrinsic.icon.proto import streaming_output_pb2
from intrinsic.logging.proto import log_item_pb2


TPayload = TypeVar("TPayload", bound=proto_message.Message)


def unpack_streaming_output_logitem(
    item: log_item_pb2.LogItem, class_to_unpack_to: Type[TPayload]
) -> Tuple[TPayload, float]:
  """Unpacks the payload in a StreamingOutputWithMetadata LogItem.

  Args:
    item: The LogItem proto.
    class_to_unpack_to: The proto type the payload should be unpacked to.

  Returns:
    A tuple with payload proto and the icon timestamp in seconds.
  """
  streaming_output = streaming_output_pb2.StreamingOutputWithMetadata()
  if not item.payload.any.Unpack(streaming_output):
    raise TypeError(
        "Item.payload.any cannot be unpacked as StreamingOutputWithMetadata."
    )
  unpacked = class_to_unpack_to()
  if not streaming_output.output.payload.Unpack(unpacked):
    raise TypeError(
        "StreamingOutputWithMetadata.output.payload cannot be unpacked to %s."
        % class_to_unpack_to.__name__,
    )
  t = streaming_output.output.timestamp_ns * 1e-9
  return (unpacked, t)


def unpack_streaming_outputs(
    items: List[log_item_pb2.LogItem], class_to_unpack_to: Type[TPayload]
) -> Tuple[List[TPayload], List[float]]:
  """Unpacks the payload in a list of StreamingOutputWithMetadata LogItems.

  Args:
    items: A list of LogItem protos.
    class_to_unpack_to: The proto type the payload should be unpacked to.

  Returns:
    A tuple with payload protos and the icon timestamps in seconds.
  """
  unpacked_items = []
  icon_ts = []
  for item in items:
    unpacked, t = unpack_streaming_output_logitem(item, class_to_unpack_to)
    unpacked_items.append(unpacked)
    icon_ts.append(t)
  return (unpacked_items, icon_ts)


def action_topic_name(robot_name: str, action_id: int) -> str:
  return f"/icon/{robot_name}/output_streams/action_{action_id}"
