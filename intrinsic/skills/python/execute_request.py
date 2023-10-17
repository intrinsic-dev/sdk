# Copyright 2023 Intrinsic Innovation LLC

"""ExecuteRequest type for calls to Skill.execute."""

import dataclasses
from typing import Generic, TypeVar

from google.protobuf import message

TParamsType = TypeVar('TParamsType', bound=message.Message)


@dataclasses.dataclass(frozen=True)
class ExecuteRequest(Generic[TParamsType]):
  """A request for a call to Skill.execute.

  Attributes:
    params: The skill parameters proto. For static typing, ExecuteRequest can be
      parameterized with the required type of this message.
  """

  params: TParamsType
