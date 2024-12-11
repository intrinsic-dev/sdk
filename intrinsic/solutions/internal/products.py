# Copyright 2023 Intrinsic Innovation LLC

"""Provides access to products in a solution."""

import re

from google.protobuf import struct_pb2
from intrinsic.scene.product.client import product_client as product_client_mod
from intrinsic.scene.proto.v1 import scene_object_pb2
from intrinsic.solutions import provided
from intrinsic.solutions import providers

_REGEX_INVALID_PYTHON_VAR_CHARS = r"\W|^(?=\d)"


class ProductInMemory(provided.Product):
  """Implementation of the Product interface wrapping local copy of product data.

  Product is a named entity composed from a SceneObject and some metadata. This
  implementation of the Product interface wraps a local copy of the product
  SceneObject and metadata after fetching it from the product service.

  Attributes:
    name: The name of the product.
    scene_object: The scene object of the product.
    metadata: The metadata of the product.
  """

  _name: str
  _scene_object: scene_object_pb2.SceneObject
  _metadata: struct_pb2.Struct

  def __init__(
      self,
      name: str,
      scene_object: scene_object_pb2.SceneObject,
      metadata: struct_pb2.Struct,
  ):
    """Initializes a ProductInMemory.

    Args:
      name: The name of the product. This name is unique for each product in a
        solution.
      scene_object: The scene object of the product, representing the geometry
        of the product.
      metadata: The metadata of the product, a struct that contains arbitrary
        data about the product.
    """
    self._name = name
    self._scene_object = scene_object
    self._metadata = metadata

  @property
  def name(self) -> str:
    return self._name

  @property
  def scene_object(self) -> scene_object_pb2.SceneObject:
    return self._scene_object

  @property
  def metadata(self) -> struct_pb2.Struct:
    return self._metadata


class Products(providers.ProductProvider):
  """Wrapper to easily access products from a solution."""

  def __init__(self, product_client: product_client_mod.ProductClient):
    """Initializes a Products.

    Args:
      product_client: The product client to use to fetch products from the
        product service in the solution.
    """
    self._product_client = product_client

  def __getitem__(self, name: str) -> provided.Product:
    """Returns the product for the given name.

    Args:
      name: The name of the product to return.

    Returns:
      The product for the given name.

    Raises:
      KeyError: If the product named `name` is not available.
    """
    try:
      product = self._product_client.get_product(name)
      scene_object = self._product_client.get_product_geometry(name)
      return ProductInMemory(
          name=name,
          scene_object=scene_object,
          metadata=product.default_config.metadata,
      )
    except Exception as e:
      raise KeyError(f"Product '{name}' not available") from e

  def __getattr__(self, name: str) -> provided.Product:
    """Returns the product for the given name.

    Args:
      name: The name of the product to return.

    Returns:
      The product for the given name.

    Raises:
      KeyError: If the product named `name` is not available.
    """
    return self.__getitem__(name)

  def __dir__(self) -> list[str]:
    """Returns the names of the stored products in sorted order.

    Only returns names which are valid Python identifiers. Product names which
    are not valid Python identifiers are skipped.

    Returns:
      The names of the products in this solution in sorted order.
    """
    products = self._product_client.list_products()
    return sorted(
        filter(
            lambda x: not re.search(_REGEX_INVALID_PYTHON_VAR_CHARS, x),
            [product.name for product in products],
        )
    )
