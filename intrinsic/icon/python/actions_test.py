# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.icon.python.actions."""

from absl.testing import absltest
from intrinsic.icon.actions import point_to_point_move_pb2
from intrinsic.icon.python import actions
from intrinsic.icon.python import icon_api


class ActionsTest(absltest.TestCase):

  def test_action_with_single_part_name(self):
    move_params = point_to_point_move_pb2.PointToPointMoveFixedParams()
    reactions = iter(
        [
            icon_api.Reaction(
                icon_api.Condition.is_done(), icon_api.StartActionInRealTime(1)
            )
        ]
    )
    action = actions.Action(0, 'foo', 'bar', move_params, reactions)
    self.assertEqual(action.id, 0)
    self.assertEqual(action.reactions, reactions)
    self.assertEqual(action.proto.action_instance_id, 0)
    self.assertEqual(action.proto.action_type_name, 'foo')
    self.assertEqual(action.proto.part_name, 'bar')
    params = point_to_point_move_pb2.PointToPointMoveFixedParams()
    action.proto.fixed_parameters.Unpack(params)
    self.assertEqual(params, move_params)

  def test_action_with_slot_part_map(self):
    move_params = point_to_point_move_pb2.PointToPointMoveFixedParams()
    reactions = iter(
        [
            icon_api.Reaction(
                icon_api.Condition.is_done(), icon_api.StartActionInRealTime(1)
            )
        ]
    )
    action = actions.Action(
        23, 'foo', {'bar_slot': 'bar'}, move_params, reactions
    )
    self.assertEqual(action.id, 23)
    self.assertEqual(action.reactions, reactions)
    self.assertEqual(action.proto.action_instance_id, 23)
    self.assertEqual(action.proto.action_type_name, 'foo')
    self.assertSameElements(
        action.proto.slot_part_map.slot_name_to_part_name, {'bar_slot': 'bar'}
    )
    params = point_to_point_move_pb2.PointToPointMoveFixedParams()
    action.proto.fixed_parameters.Unpack(params)
    self.assertEqual(params, move_params)

  def test_action_without_reaction(self):
    move_params = point_to_point_move_pb2.PointToPointMoveFixedParams()

    action = actions.Action(0, 'foo', 'bar', move_params)
    self.assertEqual(action.id, 0)
    self.assertEmpty(action.reactions)
    self.assertEqual(action.proto.action_instance_id, 0)
    self.assertEqual(action.proto.action_type_name, 'foo')
    self.assertEqual(action.proto.part_name, 'bar')
    params = point_to_point_move_pb2.PointToPointMoveFixedParams()
    action.proto.fixed_parameters.Unpack(params)
    self.assertEqual(params, move_params)


if __name__ == '__main__':
  absltest.main()
