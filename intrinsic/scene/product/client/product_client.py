# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrapper around the product service."""

from __future__ import annotations

from typing import Sequence

import grpc
from intrinsic.scene.product.proto import product_pb2
from intrinsic.scene.product.proto import product_service_pb2
from intrinsic.scene.product.proto import product_service_pb2_grpc
from intrinsic.scene.proto.v1 import scene_object_pb2
from intrinsic.util.grpc import error_handling


class ProductClient:
  """Client for the Product Service."""

  def __init__(self, stub: product_service_pb2_grpc.ProductServiceStub):
    """Constructs a new ProductClient object.

    Args:
      stub: The gRPC stub to be used for communication with the product service.
    """
    self._stub: product_service_pb2_grpc.ProductServiceStub = stub

  @classmethod
  def connect(cls, grpc_channel: grpc.Channel) -> ProductClient:
    """Connects to a running product service.

    Args:
      grpc_channel: The gRPC channel to be used for communication with the
        product service.

    Returns:
      A new ProductClient object.
    """
    stub = product_service_pb2_grpc.ProductServiceStub(grpc_channel)
    return cls(stub)

  @error_handling.retry_on_grpc_unavailable
  def list_products(self) -> Sequence[product_pb2.Product]:
    """Lists all products."""
    return self._stub.ListProducts(
        product_service_pb2.ListProductsRequest()
    ).products

  @error_handling.retry_on_grpc_unavailable
  def get_product(self, name: str) -> product_pb2.Product:
    """Gets a product."""
    return self._stub.GetProduct(
        product_service_pb2.GetProductRequest(name=name)
    )

  @error_handling.retry_on_grpc_unavailable
  def get_product_geometry(self, name: str) -> scene_object_pb2.SceneObject:
    """Gets the geometry of a product."""
    return self._stub.GetProductGeometry(
        product_service_pb2.GetProductGeometryRequest(name=name)
    ).scene_object
