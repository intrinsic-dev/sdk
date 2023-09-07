# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Defines wrapper around ProductPartReference."""

from intrinsic.config.proto import ppr_refs_pb2


class ProductPart:
  """A ProductPart is a part of the product defined in the product document.

  Attributes:
    name: the name of this ProductPart.
    proto: proto representation of this ProductPart.
  """

  def __init__(self, part_name: str):
    self._name: str = part_name

  @property
  def name(self) -> str:
    return self._name

  @property
  def proto(self) -> ppr_refs_pb2.ProductPartReference:
    return ppr_refs_pb2.ProductPartReference(product_part_name=self._name)
