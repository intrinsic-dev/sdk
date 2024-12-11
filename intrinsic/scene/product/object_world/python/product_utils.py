# Copyright 2023 Intrinsic Innovation LLC

"""A module for product world objects based on a user_data field convention."""

from typing import Optional

from google.protobuf import any_pb2
from google.protobuf import struct_pb2
from intrinsic.math.python import data_types
from intrinsic.scene.product.proto import product_world_object_data_pb2
from intrinsic.scene.proto.v1 import scene_object_pb2
from intrinsic.world.python import object_world_client
from intrinsic.world.python import object_world_ids
from intrinsic.world.python import object_world_resources


PRODUCT_USER_DATA_KEY = 'FLOWSTATE_product'

def is_product(world_object: object_world_resources.WorldObject) -> bool:
  """Returns whether the given world object is a product object.

  Args:
    world_object: The world object to check.

  Returns:
    True if the world object contains a valid product user data, otherwise
    False.

  Raises:
    ValueError: If the world object contains a invalid type of user data under
    the PRODUCT_USER_DATA_KEY.
  """
  if PRODUCT_USER_DATA_KEY not in world_object.user_data:
    return False
  if not world_object.user_data[PRODUCT_USER_DATA_KEY].Is(
      product_world_object_data_pb2.ProductWorldObjectData.DESCRIPTOR
  ):
    raise ValueError(
        'World object user data does not contain a valid product user data.'
    )
  return True


def get_product_name(
    world_object: object_world_resources.WorldObject,
) -> str | None:
  """Returns the product name of the given product object.

  Args:
    world_object: The world object to get the product name from.

  Returns:
    The product name of the given object contains valid product user data,
    otherwise None.

  Raises:
    ValueError: If the world object contains a invalid type of user data under
    the PRODUCT_USER_DATA_KEY.
  """
  if not is_product(world_object):
    return None
  world_object_data = product_world_object_data_pb2.ProductWorldObjectData()
  if not world_object.user_data[PRODUCT_USER_DATA_KEY].Unpack(
      world_object_data
  ):
    raise ValueError('Failed to unpack ProductWorldObjectData.')
  return world_object_data.product_name


def get_product_metadata(
    world_object: object_world_resources.WorldObject,
) -> struct_pb2.Struct | None:
  """Returns the product metadata of the given product object.

  Args:
    world_object: The world object to get the metadata from.

  Returns:
    The product metadata of the given object contains valid product user data,
    otherwise None.

  Raises:
    ValueError: If the world object contains a invalid type of user data under
    the PRODUCT_USER_DATA_KEY.
  """
  if not is_product(world_object):
    return None
  world_object_data = product_world_object_data_pb2.ProductWorldObjectData()
  if not world_object.user_data[PRODUCT_USER_DATA_KEY].Unpack(
      world_object_data
  ):
    raise ValueError('Failed to unpack ProductWorldObjectData.')
  return world_object_data.metadata


def create_object_from_product(
    world: object_world_client.ObjectWorldClient,
    object_name: object_world_ids.WorldObjectName,
    product_name: str,
    scene_object: scene_object_pb2.SceneObject,
    product_metadata: Optional[struct_pb2.Struct] = None,
    parent: Optional[object_world_resources.WorldObject] = None,
    parent_object_t_created_object: data_types.Pose3 = data_types.Pose3(),
):
  """Creates an objecf from product data.

  Args:
    world: The object world client.
    object_name: The name of the object to create.
    product_name: The name of the product.
    scene_object: The scene object to create.
    product_metadata: The product metadata to set.
    parent: The parent object to set.
    parent_object_t_created_object: The transformation from the parent object to
      the created object.

  Raises:
    object_world_client.CreateObjectError: If create object fails.
  """
  world_object_data = product_world_object_data_pb2.ProductWorldObjectData(
      product_name=product_name, metadata=product_metadata
  )
  world_object_data_any = any_pb2.Any()
  world_object_data_any.Pack(world_object_data)
  user_data = {PRODUCT_USER_DATA_KEY: world_object_data_any}

  world.create_object(
      object_name=object_name,
      geometry_spec=scene_object,
      parent=parent,
      parent_object_t_created_object=parent_object_t_created_object,
      user_data=user_data,
  )

