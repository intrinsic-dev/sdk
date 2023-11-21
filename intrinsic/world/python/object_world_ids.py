# Copyright 2023 Intrinsic Innovation LLC

"""Defines ID types used in the object world.

The ID types are used in the object world to identify objects and frames.

The IDs are classes inheritating from str to improve the type safety in type
checked code. In unchecked code like Jupyter notebooks the types have no effect
and can be directliy replaced by native strings:
  'my_object' can be used instead of WorldObjectName('my_object')

Typing.NewType is not used, because it generates unreadable types in the
signature in Jupyter environments. The class definition shows a better signature
and only results in small execution overhead.
"""


class ObjectWorldResourceId(str):
  """A unique id for a resource in the object-based world view.

  All resources (objects and frames) share the same id-namespace. Treat this as
  an opaque value. There are no guarantees on character set, formatting or
  length.
  """


class WorldObjectName(str):
  """A human-readable, unique name for an object in the object-based world view.

  The WorldObjectName complies with the character set and rules for variable
  names in Python.
  """


class FrameName(str):
  """A human-readable name of the frame.

  Guaranteed to be non-empty and unique among all frames under the same object.
  Allowed characters are letters, numbers, and underscore, with the first
  character a letter, the last a letter or a number.
  """


# The id of the root object which is present in every object world.
ROOT_OBJECT_ID = ObjectWorldResourceId('root')

# The name of the root object which is present in every object world.
ROOT_OBJECT_NAME = WorldObjectName('root')
