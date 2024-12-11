# Copyright 2023 Intrinsic Innovation LLC

from unittest import mock

from absl.testing import absltest
from google.protobuf import struct_pb2
from intrinsic.scene.product.proto import product_pb2
from intrinsic.scene.proto.v1 import scene_object_pb2
from intrinsic.solutions.internal import products as products_mod


class ProductsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._product_client = mock.MagicMock()

  def test_dir_products(self):
    self._product_client.list_products.return_value = [
        product_pb2.Product(name="product_1"),
        product_pb2.Product(name="product_2"),
        product_pb2.Product(name="product invalid python identifier"),
    ]
    products = products_mod.Products(self._product_client)
    self.assertEqual(
        dir(products),
        ["product_1", "product_2"],
    )

  def test_access_products(self):
    self._product_client.get_product.return_value = product_pb2.Product(
        name="product_1",
        default_config=product_pb2.ProductConfig(
            metadata=struct_pb2.Struct(
                fields={
                    "sku": struct_pb2.Value(string_value="123456"),
                }
            )
        ),
    )
    self._product_client.get_product_geometry.return_value = (
        scene_object_pb2.SceneObject(name="scene_object")
    )

    products = products_mod.Products(self._product_client)
    self.assertEqual(products.product_1.scene_object.name, "scene_object")
    self.assertEqual(
        products.product_1.metadata.fields["sku"].string_value, "123456"
    )

    self.assertEqual(products["product_1"].scene_object.name, "scene_object")
    self.assertEqual(
        products["product_1"].metadata.fields["sku"].string_value, "123456"
    )


if __name__ == "__main__":
  absltest.main()
