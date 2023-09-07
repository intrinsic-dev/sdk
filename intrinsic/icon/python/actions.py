# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Classes for describing Actions in the ICON Python Client API.

An Action describes how the real-time control layer should control one or more
parts.
"""

from typing import Iterable, Mapping, Optional, Union

from google.protobuf import any_pb2
from google.protobuf import message as _message
from intrinsic.icon.proto import types_pb2
from intrinsic.icon.python import reactions as _reactions


class Action:
  """Instantiation of an Action that controls one or more parts.

  This class thinly wraps types_pb2.Action and keeps track of attached
  Reactions. Use `.proto` to access the proto representation.

  Attributes:
    id: The action instance ID.
    proto: The types_pb2.Action proto representation of this condition.
    reactions: The Reactions to attach to the new Action.
  """

  def __init__(
      self,
      action_id: int,
      action_type: str,
      part_name_or_slot_part_map: Union[str, Mapping[str, str]],
      params: Optional[_message.Message],
      reactions: Optional[Iterable[_reactions.Reaction]] = None,
  ):
    """Creates an instance of an Action.

    Args:
      action_id: The client-assigned ID for this action. Must be unique for the
        duration of the session.
      action_type: The type of action, corresponding to the type of an available
        ActionSignature on the server (e.g. 'xfa.point_to_point_move').
      part_name_or_slot_part_map: Takes either the name of a single part for the
        action to control, or a map from the action's slot names to part names.
      params: Fixed parameters specific to this action, corresponding to the
        parameter info from the ActionSignature.
      reactions: List of Reactions to attach to the new Action.
    """
    self.id = action_id
    any_params = any_pb2.Any()
    if params:
      any_params.Pack(params)
    if isinstance(part_name_or_slot_part_map, str):
      self.proto = types_pb2.ActionInstance(
          action_instance_id=action_id,
          action_type_name=action_type,
          fixed_parameters=any_params,
          part_name=part_name_or_slot_part_map,
      )
    elif isinstance(part_name_or_slot_part_map, Mapping):
      self.proto = types_pb2.ActionInstance(
          action_instance_id=action_id,
          action_type_name=action_type,
          fixed_parameters=any_params,
          slot_part_map=types_pb2.SlotPartMap(
              slot_name_to_part_name=part_name_or_slot_part_map
          ),
      )
    else:
      raise TypeError(
          "Unsupported part_name_or_slot_part_map type:"
          f" {type(part_name_or_slot_part_map)}",
      )
    self.reactions: Iterable[_reactions.Reaction] = []
    if reactions:
      self.reactions = reactions
