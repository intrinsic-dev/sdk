# Copyright 2023 Intrinsic Innovation LLC

"""General utilities."""

import dataclasses
import enum
import functools
import time
from typing import Any, Callable, Optional, Type, TypeVar

from intrinsic.solutions import errors


class classproperty:  # pylint: disable=invalid-name
  """Decorator that can be used to make @classmethod like @properties.

  Functions annotated with this decorator may not raise any errors because this
  breaks pydoc (e.g. `help(MyClass)` will not work anymore). In particular,
  a @classproperty function that is also an @abc.abstractmethod may not raise a
  NotImplementedError but must provide a default implementation instead.
  """

  def __init__(self, fget):
    self.fget = fget

  def __get__(self, unused_obj, obj_type):
    return self.fget(obj_type)


def is_iterable(object_: Any) -> bool:
  """Checks if a given object is iterable.

  Args:
    object_: The object to check for iteration support.

  Returns:
    True if object_ is iterable, False otherwise.
  """
  try:
    iter(object_)
  except TypeError:
    return False
  else:
    return True


F = TypeVar("F", bound=Callable[..., Any])


def timing(f: F) -> F:
  """Decorator that prints timing information to the console."""

  @functools.wraps(f)
  def wrap(*args, **kwargs):
    t_start = time.time()
    result = f(*args, **kwargs)
    t_end = time.time()
    print(
        "func: %r args: [%r, %r] took: %2.4f sec"
        % (f.__name__, args, kwargs, t_end - t_start)
    )
    return result

  return wrap


@dataclasses.dataclass
class PrefixOptions:
  """Option class that describes the prefixes and import paths.

  This is used to generate valid Python code based on how the user has imported
  our modules/what kind of local variables have been bound.

  Attributes:
    xfa_prefix: Prefix for how the xfa module has been imported.
    world_prefix: Prefix for how the world can be accessed.
    skill_prefix: Prefix for how the skills can be accessed.
    equipment_prefix: Prefix for how equipment can be accessed.
  """

  xfa_prefix: str = "xfa"
  world_prefix: str = "world"
  skill_prefix: str = "skills"
  equipment_prefix: str = "solution.resources"


def protoenum(
    *,
    proto_enum_type: Type[Any],  # EnumTypeWrapper is internal, hence Any
    unspecified_proto_enum_map_to_none: Optional[int] = None,
    strip_prefix: Optional[str] = None,
) -> Callable[[Type[enum.Enum]], Type[Any]]:
  """Decorator to create Python wrappers for proto enums.

  The intention of enum wrappers are to decouple the Python API from the
  underlying protos. For example, consider an enum MyEnum (in a message
  MyMessage in a message module my_message_pb2) with their values
  MYENUM_UNSPECIFIED, MYENUM_A and MYENUM_B. Then the decorator invocation could
  look like this:

  @utils.protoenum(
      proto_enum_type=my_message_pb2.MyMessage.MyEnum,
      unspecified_proto_enum_map_to_none=my_message_pb2.MyMessage.MyEnum.MYENUM_UNSPECIFIED,
      strip_prefix="MYENUM_",
  )
  class MyEnum:
    pass  # or docstring

  The decorator creates an enum class with two members A and B (strip_prefix
  causes the MYENUM_ prefix to be removed). The value is the respective proto
  enum value. The decorator also adds a from_proto() class method that takes a
  proto enum value and converts it to the Python enum value. Here, the
  MYENUM_UNSPECIFIED value is mapped to none. Therefore, it is not made a member
  of the enum and when passed to from_proto() the function returns None.

  Args:
    proto_enum_type: the proto enum type class, e.g., for a MyEnum value in a
      message MyMessage in a message module my_message_pb2 your would pass
      my_message_pb2.MyMessage.MyEnum.
    unspecified_proto_enum_map_to_none: If the proto enum has a designated value
      for unspecified and that should be mapped to None during conversion (treat
      the enum as if it is optional) then add the unspecified value. For
      example, let a MyEnum value in a message MyMessage in a message module
      my_message_pb2 have an UNSPECIFIED entry, then pass
      my_message_pb2.MyMessage.MyEnum.UNSPECIFIED. If you use this feature, you
      must not add the unspecified value as an entry in the enum class.
    strip_prefix: the given string is removed from the proto enum names before
      adding them to the Python enum class.

  Returns:
    Decorator function.
  """

  def protoenum_decorator(cls: Type[enum.Enum]) -> Type[Any]:
    @classmethod
    def from_proto(
        cls, value: Optional[proto_enum_type.__class__]
    ) -> Optional[cls]:
      """Converts a proto enum value to enum value.

      Args:
        value: The proto value to convert.

      Returns:
        Corresponding value from Python enum.

      Raises:
        errors.InvalidArgumentError: Unknown proto enum value passed.
      """
      if value is None:
        return None

      if value == unspecified_proto_enum_map_to_none:
        return None

      for enum_item in list(cls):
        if enum_item.value == value:
          return enum_item

      raise errors.InvalidArgumentError(f"Unknown {cls.__name__} proto type")

    def remove_prefix(string: str, prefix: Optional[str]) -> str:
      if prefix is not None and string.startswith(prefix):
        return string[len(prefix) :]
      return string

    custom_enum = enum.Enum(
        cls.__name__,
        {
            remove_prefix(name, strip_prefix): value
            for name, value in proto_enum_type.items()
            if value != unspecified_proto_enum_map_to_none
        },
    )
    custom_enum.from_proto = from_proto

    return enum.unique(custom_enum)

  return protoenum_decorator
