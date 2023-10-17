# Copyright 2023 Intrinsic Innovation LLC

"""GetFootprintRequest type for calls to Skill.get_footprint."""

import dataclasses
from typing import Generic, TypeVar

from google.protobuf import message

TParamsType = TypeVar('TParamsType', bound=message.Message)


@dataclasses.dataclass(frozen=True)
class GetFootprintRequest(Generic[TParamsType]):
  """A request for a call to Skill.get_footprint.

  Attributes:
    params: The skill parameters proto. For static typing, GetFootprintRequest
      can be parameterized with the required type of this message.
  """

  params: TParamsType
