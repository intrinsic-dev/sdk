# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for equipment_registry_external."""

from unittest import mock
from absl.testing import absltest
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import equipment_registry_pb2
from intrinsic.solutions import equipment_registry


class EquipmentRegistryExternalTest(absltest.TestCase):

  def test_smoke(self):
    stub = mock.MagicMock()
    registry = equipment_registry.EquipmentRegistry(stub)
    response = equipment_registry_pb2.ListEquipmentResponse(
        handles=[
            equipment_pb2.EquipmentHandle(name='a'),
            equipment_pb2.EquipmentHandle(name='b'),
        ]
    )
    stub.ListEquipment.return_value = response

    self.assertCountEqual(registry.list_equipment(), response.handles)


if __name__ == '__main__':
  absltest.main()
