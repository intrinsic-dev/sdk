# Copyright 2023 Intrinsic Innovation LLC

"""Skills Python APIs and definitions."""

import abc
from typing import Generic, List, Mapping, Optional, TypeVar, Union

from google.protobuf import descriptor
from google.protobuf import message
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import footprint_pb2
from intrinsic.skills.proto import skill_service_pb2
from intrinsic.skills.python import execute_context
from intrinsic.skills.python import execute_request
from intrinsic.skills.python import get_footprint_context
from intrinsic.skills.python import get_footprint_request
from intrinsic.skills.python import skill_canceller

# Imported for convenience of skill implementations.
ExecuteContext = execute_context.ExecuteContext
ExecuteRequest = execute_request.ExecuteRequest
GetFootprintContext = get_footprint_context.GetFootprintContext
GetFootprintRequest = get_footprint_request.GetFootprintRequest
SkillCancelledError = skill_canceller.SkillCancelledError

TParamsType = TypeVar('TParamsType', bound=message.Message)
TResultType = TypeVar('TResultType', bound=Union[message.Message, None])


class InvalidSkillParametersError(ValueError):
  """Invalid arguments were passed to the skill parameters."""


class SkillSignatureInterface(metaclass=abc.ABCMeta):
  """Signature interface for skills.

  The signature interface presents metadata about skill, which is associated the
  skill class implementation.
  """

  @classmethod
  def default_parameters(cls) -> Optional[message.Message]:
    """Returns the default parameters for the Skill.

    Returns None if there are no defaults. Fields with default values must be
    marked as `optional` in the proto schema.
    """
    return None

  @classmethod
  def required_equipment(cls) -> Mapping[str, equipment_pb2.ResourceSelector]:
    """Returns the signature of the skill's required equipment.

    The return map includes the name of the equipment as the key and its
    selector type as value.
    """
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def name(cls) -> str:
    """Returns the name of the skill."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def package(cls) -> str:
    """Returns the package of the skill."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def get_parameter_descriptor(cls) -> descriptor.Descriptor:
    """Returns the descriptor for the parameter that this skill expects."""
    raise NotImplementedError('Method not implemented!')

  @classmethod
  def get_return_value_descriptor(cls) -> Optional[descriptor.Descriptor]:
    """Returns the descriptor for the value that this skill may output."""

    # By default, assume the skill has no value to return.
    return None

  @classmethod
  def supports_cancellation(cls) -> bool:
    """Returns True if the skill supports cancellation."""
    return False

  @classmethod
  def get_ready_for_cancellation_timeout(cls) -> float:
    """Returns the skill's ready for cancellation timeout, in seconds.

    If the skill is cancelled, its ExecuteContext's SkillCanceller waits for
    at most this timeout duration for the skill to have called `ready` before
    raising a timeout error.
    """
    return 30.0


class SkillExecuteInterface(abc.ABC, Generic[TParamsType, TResultType]):
  """Interface for skill executors.

  Implementations of the SkillExecuteInterface define how a skill behaves when
  it is executed.
  """

  @abc.abstractmethod
  def execute(
      self, request: ExecuteRequest[TParamsType], context: ExecuteContext
  ) -> TResultType:
    """Executes the skill.

    Skill authors should override this method with their implementation.

    Any error raised by the skill will be handled by the executive that runs the
    process to which the skill belongs. The effect of the error will depend on
    how the skill is integrated into that process' behavior tree. For instance,
    if the skill is part of a fallback node, a skill error will trigger the
    fallback behavior. If the skill is not part of any node that handles errors,
    then a skill error will cause the process to fail.

    Currently, there is no way to distinguish between potentially recoverable
    failures that should lead to fallback handling (e.g., failure to achieve the
    skill's objective) and other failures that should cause the entire process
    to abort (e.g., failure to connect to a gRPC service).

    Args:
      request: The execute request.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      The skill's result message, or None if it does not return a result.

    Raises:
      InvalidSkillParametersError: If the arguments provided to skill parameters
        are invalid.
      SkillCancelledError: If the skill is aborted due to a cancellation
        request.
    """
    raise NotImplementedError(
        f'Skill "{type(self).__name__!r} has not implemented `execute`.'
    )


class SkillProjectInterface(abc.ABC, Generic[TParamsType, TResultType]):
  """Interface for skill projectors.

  Implementations of the SkillProjectInterface define how predictive information
  about how a skill might behave during execution. The methods of this interface
  should be invokable prior to execution to allow a skill to, eg.:
  * precompute information that can be passed to the skill at execution time
  * predict its behavior given the current known information about the world,
    and any parameters that the skill depends on
  * provide an understanding of what the footprint of the skill on the workcell
    will be when it is executed
  """

  def get_footprint(
      self,
      request: GetFootprintRequest[TParamsType],
      context: GetFootprintContext,
  ) -> footprint_pb2.Footprint:
    """Returns the required resources for running this skill.

    Skill authors should override this method with their implementation.

    Args:
      request: The get footprint request.
      context: Provides access to the world and other services that a skill may
        use.

    Returns:
      The skill's footprint.
    """
    del request  # Unused in this default implementation.
    del context  # Unused in this default implementation.
    return footprint_pb2.Footprint(lock_the_universe=True)


class Skill(
    SkillSignatureInterface,
    SkillExecuteInterface[TParamsType, TResultType],
    SkillProjectInterface[TParamsType, TResultType],
    Generic[TParamsType, TResultType],
):
  """Interface for skills.

  Notes on skill implementations:

  If a skill implementation supports cancellation, it should:
  1) Stop as soon as possible and leave resources in a safe and recoverable
     state when a cancellation request is received (via its ExecuteContext).
     Cancelled skill executions should end by raising SkillCancelledError.
  2) Override `supports_cancellation` to return True.
  """
