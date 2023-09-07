# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Tests for intrinsic.workcell.equipment."""

from unittest import mock

from absl.testing import absltest
from google.protobuf import text_format
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import equipment_registry_pb2
from intrinsic.solutions import equipment as equipment_mod
from intrinsic.solutions import equipment_registry as equipment_registry_mod


class EquipmentTest(absltest.TestCase):
  """Tests public methods of the skills wrapper class."""

  def test_list_equipment(self):
    """Tests general equipment listing and access."""
    equipment_name = 'my_equipment'
    equipment_info = text_format.Parse(
        """name: '%s'
           equipment_data {
             key: 'type-a'
             value {}
           }
        """ % equipment_name,
        equipment_pb2.EquipmentHandle(),
    )
    equipment_registry_stub = mock.MagicMock()
    equipment_registry_response = equipment_registry_pb2.ListEquipmentResponse()
    equipment_registry_response.handles.add().CopyFrom(equipment_info)
    equipment_registry_stub.ListEquipment.return_value = (
        equipment_registry_response
    )
    equipment_registry = equipment_registry_mod.EquipmentRegistry(
        equipment_registry_stub
    )

    equipment = equipment_mod.Equipment(equipment_registry)
    equipment_registry_stub.ListEquipment.assert_called_once_with(
        equipment_registry_pb2.ListEquipmentRequest()
    )

    self.assertEqual(dir(equipment), [equipment_name])

  def test_list_equipment_special_characters_in_name(self):
    """Tests general access for equipment with special characters in name."""
    equipment_name = 'my_equipment::some!strange+thing'
    cleaned_name = 'my_equipment__some_strange_thing'
    equipment_info = text_format.Parse(
        """name: '%s'
           equipment_data {
             key: 'type-a'
             value {}
           }
        """ % equipment_name,
        equipment_pb2.EquipmentHandle(),
    )
    equipment_registry_stub = mock.MagicMock()
    equipment_registry_response = equipment_registry_pb2.ListEquipmentResponse()
    equipment_registry_response.handles.add().CopyFrom(equipment_info)
    equipment_registry_stub.ListEquipment.return_value = (
        equipment_registry_response
    )
    equipment_registry = equipment_registry_mod.EquipmentRegistry(
        equipment_registry_stub
    )

    equipment = equipment_mod.Equipment(equipment_registry)
    equipment_registry_stub.ListEquipment.assert_called_once_with(
        equipment_registry_pb2.ListEquipmentRequest()
    )

    # Test dir() only returns cleaned names
    self.assertEqual([cleaned_name], dir(equipment))

    # Test we can access the equipment with the original and the cleaned name
    self.assertEqual(equipment[equipment_name].name, equipment_name)
    self.assertEqual(equipment[cleaned_name].name, equipment_name)

  def test_equipment_handle_repr(self):
    """Tests proper repr() implementation."""
    handle = equipment_mod.EquipmentHandle.create('Foo', ['type1', 'type2'])

    self.assertEqual(
        repr(handle),
        'EquipmentHandle.create(name="Foo", types=["type1", "type2"])',
    )


if __name__ == '__main__':
  absltest.main()
