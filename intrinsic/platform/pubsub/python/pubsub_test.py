# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.platform.pubsub.python.pubsub."""

import threading

from absl.testing import absltest
from absl.testing import parameterized
from intrinsic.platform.common.proto import test_pb2
from intrinsic.platform.pubsub.python import pubsub
from intrinsic.solutions.testing import compare


class CallbackType:
  NONE = 0
  OK = 1
  ERROR = 2


class SubCallbackChecker:

  def __init__(self, pubsub_impl):
    self.pubsub_impl = pubsub_impl
    self.call_type = CallbackType.NONE
    self.condition = threading.Condition()

  def notify(self, callback_type):
    with self.condition:
      self.call_type = callback_type
      self.condition.notify()

  def subscribe(
      self, topic, config, exemplar, msg_callback=None, error_callback=None
  ):
    def msg_callback_wrapper(message):
      if msg_callback:
        msg_callback(message)
      self.notify(CallbackType.OK)

    def error_callback_wrapper(packet, error):
      if error_callback:
        error_callback(packet, error)
      self.notify(CallbackType.OK)

    self.sub = self.pubsub_impl.CreateSubscription(
        topic, config, exemplar, msg_callback_wrapper, error_callback_wrapper
    )

  def get_call_type(self):
    with self.condition:
      return self.call_type

  def wait_for_call(self):
    with self.condition:
      # 1 second timeout.
      self.condition.wait_for(lambda: self.call_type != CallbackType.NONE, 1)
      return self.call_type


def make_test_proto():
  return test_pb2.TestMessageString(data='Test')


class PubsubTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.pubsub = pubsub.PubSub()
    config = pubsub.TopicConfig()
    self.pub = self.pubsub.CreatePublisher('news', config)
    self.callback_checker = SubCallbackChecker(self.pubsub)

  @parameterized.named_parameters(('proto', make_test_proto()))
  def test_pubsub(self, value):
    def msg_callback(message):
      compare.assertProto2Equal(self, message, value)

    config = pubsub.TopicConfig()
    self.callback_checker.subscribe(
        topic='news',
        config=config,
        exemplar=test_pb2.TestMessageString(),
        msg_callback=msg_callback,
    )
    self.pub.Publish(value)
    self.assertEqual(self.callback_checker.wait_for_call(), CallbackType.OK)

  def test_error(self):
    self.message_callback_called = False

    def message_callback(_):
      self.message_callback_called = True

    self.error_callback_called = False

    def error_callback(packet, error):
      del packet
      del error
      self.error_callback_called = True

    # Pass an exemplar of type TestMessageString.
    config = pubsub.TopicConfig()
    self.callback_checker.subscribe(
        topic='news',
        config=config,
        exemplar=test_pb2.TestMessageString(),
        msg_callback=message_callback,
        error_callback=error_callback,
    )

    # Publish a message of type TestMessageStock.
    self.pub.Publish(test_pb2.TestMessageStock())
    self.assertEqual(self.callback_checker.wait_for_call(), CallbackType.OK)
    self.assertTrue(self.error_callback_called)
    self.assertFalse(self.message_callback_called)

  def test_simple_pubsub(self):
    config = pubsub.TopicConfig()
    publisher = self.pubsub.CreatePublisher('news', config)

    condition = threading.Condition()
    call_type = CallbackType.NONE

    stock_message = test_pb2.TestMessageStock(symbol='Some stock', value=23)

    def stock_callback(message: test_pb2.TestMessageStock):
      nonlocal condition
      nonlocal call_type
      compare.assertProto2Equal(self, message, stock_message)
      call_type = CallbackType.OK
      with condition:
        condition.notify()

    subscription = self.pubsub.CreateSubscription(  # pylint:disable=unused-variable
        'news', config, stock_message, stock_callback
    )
    publisher.Publish(stock_message)

    with condition:
      condition.wait_for(lambda: call_type != CallbackType.NONE, 1)


if __name__ == '__main__':
  absltest.main()
