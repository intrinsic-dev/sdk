# Copyright 2023 Intrinsic Innovation LLC

"""Utils for Skill implementations."""

from __future__ import annotations

from intrinsic.skills.internal import execute_context_impl
from intrinsic.skills.internal import preview_context_impl
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.python import skill_interface


def preview_via_execute(
    skill: skill_interface.Skill[
        skill_interface.TParamsType, skill_interface.TResultType
    ],
    request: skill_interface.PreviewRequest[skill_interface.TParamsType],
    context: skill_interface.PreviewContext,
) -> skill_interface.TResultType:
  """Implements Skill.preview by calling Skill.execute.

  A skill can use this function to implement `preview` by calling
  `preview_via_execute` from within its implementation. E.g.:
  ```
  class MySkill(Skill):
    def preview(self, request: PreviewRequest, context: PreviewContext) -> ...:
      ...
      return preview_via_execute(self, request, context)
  ```

  A skill should only use this util to implement `preview` if its `execute`
  method does not require resources or modify the object world.

  Args:
    skill: The skill instance.
    request: The preview request.
    context: The preview context.

  Returns:
    The response from calling `skill.execute`.
  """
  return skill.execute(
      preview_to_execute_request(request),
      preview_to_execute_context(
          context=context,
          resource_handles={},
      ),
  )


def preview_to_execute_request(
    request: skill_interface.PreviewRequest[skill_interface.TParamsType],
) -> skill_interface.ExecuteRequest[skill_interface.TParamsType]:
  """Converts a PreviewRequest to an ExecuteRequest."""
  return skill_interface.ExecuteRequest(
      params=request.params,
  )


def preview_to_execute_context(
    context: skill_interface.PreviewContext,
    pub_sub_instance: skill_pubsub.SkillPubSubInstance,
    resource_handles: dict[str, equipment_pb2.ResourceHandle],
) -> skill_interface.ExecuteContext:
  """Converts a PreviewContext to an ExecuteContext."""
  return execute_context_impl.ExecuteContextImpl(
      canceller=context.canceller,
      logging_context=context.logging_context,
      motion_planner=context.motion_planner,
      object_world=context.object_world,
      resource_handles=resource_handles,
  )
