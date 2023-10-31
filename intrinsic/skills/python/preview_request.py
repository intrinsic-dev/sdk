# Copyright 2023 Intrinsic Innovation LLC

"""PreviewRequest type for calls to Skill.preview."""

import dataclasses
from typing import Generic, TypeVar

from google.protobuf import message

TParamsType = TypeVar('TParamsType', bound=message.Message)


@dataclasses.dataclass(frozen=True)
class PreviewRequest(Generic[TParamsType]):
  """A request for a call to Skill.preview.

  Attributes:
    params: The skill parameters proto. For static typing, PreviewRequest can be
      parameterized with the required type of this message.
  """

  params: TParamsType
