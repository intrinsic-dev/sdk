# Copyright 2023 Intrinsic Innovation LLC

"""Implementation of a basic calculator service."""

from absl import logging
import grpc
from intrinsic.assets.services.examples.calcserver import calc_server_pb2
from intrinsic.assets.services.examples.calcserver import calc_server_pb2_grpc


class CalculatorServiceServicer(calc_server_pb2_grpc.CalculatorServicer):
  """Performs basic calculator operations."""

  def __init__(self, config: calc_server_pb2.CalculatorConfig):
    """Initializes the object.

    Args:
      config: The calculator configuration.
    """
    self._config = config

  def Calculate(
      self,
      request: calc_server_pb2.CalculatorRequest,
      context: grpc.ServicerContext,
  ) -> calc_server_pb2.CalculatorResponse:
    result = 0

    if self._config.reverse_order:
      a = request.y
      b = request.x
    else:
      a = request.x
      b = request.y

    if request.operation == calc_server_pb2.CALCULATOR_OPERATION_ADD:
      result = a + b
      logging.info('%d + %d = %d', a, b, result)
    elif request.operation == calc_server_pb2.CALCULATOR_OPERATION_MULTIPLY:
      result = a * b
      logging.info('%d * %d = %d', a, b, result)
    elif request.operation == calc_server_pb2.CALCULATOR_OPERATION_SUBTRACT:
      result = a - b
      logging.info('%d - %d = %d', a, b, result)
    elif request.operation == calc_server_pb2.CALCULATOR_OPERATION_DIVIDE:
      if b == 0:
        logging.info('Cannot divide by 0 (%d / %d)', a, b)
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'Cannot divide by 0')
      result = a // b
      logging.info('%d / %d = %d', a, b, result)
    else:
      context.abort(
          grpc.StatusCode.INVALID_ARGUMENT,
          f'Invalid operation: {request.operation}',
      )

    return calc_server_pb2.CalculatorResponse(result=result)
