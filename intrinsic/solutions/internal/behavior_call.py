# Copyright 2023 Intrinsic Innovation LLC

"""Lightweight Python wrappers around actions."""

from typing import Optional

from intrinsic.executive.proto import behavior_call_pb2
from intrinsic.solutions import providers
from intrinsic.solutions import utils
from intrinsic.solutions.internal import actions
from intrinsic.solutions.internal import skill_utils


class Action(actions.ActionBase):
  """Thin wrapper that encapsulates a behavior_call_pb2.BehaviorCall proto."""

  _proto: behavior_call_pb2.BehaviorCall

  def __init__(
      self,
      proto: Optional[behavior_call_pb2.BehaviorCall] = None,
      *,
      skill_id: Optional[str] = None,
  ):
    """Initialize an Action from an Action proto or skill ID.

    Args:
      proto: Action proto. Creates a copy (not reference).
      skill_id: The skill ID of the action (alternative to passing a full proto)
    """
    super().__init__()
    self._proto = behavior_call_pb2.BehaviorCall()
    if proto is not None:
      self._proto.CopyFrom(proto)
    elif skill_id is not None:
      self._proto.skill_id = skill_id

  @property
  def proto(self) -> behavior_call_pb2.BehaviorCall:
    if self._execute_timeout:
      self._proto.skill_execution_options.execute_timeout.FromTimedelta(
          self._execute_timeout
      )
    if self._project_timeout:
      self._proto.skill_execution_options.project_timeout.FromTimedelta(
          self._project_timeout
      )
    return self._proto

  @proto.setter
  def proto(self, proto) -> None:
    self._proto = proto

  def to_python(
      self,
      prefix_options: utils.PrefixOptions,
      identifier: str,
      skills: providers.SkillProvider,
  ) -> str:
    """Converts Action to valid Python representation.

    Args:
      prefix_options: The PrefixOptions for generating the python
        representation.
      identifier: Action identifier to be used in building the plan.
      skills: access to available skills for parameter resolution

    Returns:
       Valid python representation for action as string.
    """
    param = []

    if self.proto:
      skill_info = skills[self.proto.skill_id].skill_info
      if skill_info.skill_proto.HasField('parameter_description'):
        param_message = skill_info.create_param_message()
        self.proto.parameters.Unpack(param_message)
        for k, v in param_message.ListFields():
          python_repr = skill_utils.pythonic_field_to_python_string(
              v, k, prefix_options, self.proto.skill_id
          )
          param.append(f'{k.name}={python_repr}')
      for entry in self.proto.resources:
        resource_param = (
            f'{prefix_options.resource_prefix}.'
            f'{self.proto.resources[entry].handle.replace(":", "_")}'
        )
        param.append(f'{entry}={resource_param}')
      if self.proto.return_value_name:
        param.append(f'return_value_key="{self.proto.return_value_name}"')
      return (
          f'{identifier} ='
          f' {prefix_options.skill_prefix}.'
          f'{skill_info.skill_proto.skill_name}({", ".join(param)})'
      )
    return ''

  def __repr__(self) -> str:
    """Converts Action to Python (pseudocode) representation."""
    resources = ''
    if self.proto.resources:
      resources = ', '.join([
          f'{key}={{{repr(value).strip()}}}'
          for key, value in sorted(self.proto.resources.items())
      ])
      resources = f'.require({resources})'
    return f'Action(skill_id={repr(self.proto.skill_id)}){resources}'
  def require(self, **kwargs) -> 'Action':
    """Sets (and overwrites) resources of the action.

    Example usage:
    ```
    action = Action(skill_id="say").require(device="SomeSpeaker")
    print(action.proto())
    ```

    Note that this class does not have a skill info, so the validity of the
    resource (slot name) cannot be verified.

    Args:
      **kwargs: a map from slot name to resource name.

    Returns:
      self
    """
    self._proto.resources.clear()
    for slot, name in kwargs.items():
      self._proto.resources[slot].handle = name
    return self
