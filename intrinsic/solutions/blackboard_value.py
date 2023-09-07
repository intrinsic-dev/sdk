# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""A thin wrapper around the blackboard which can be accessed via the executive."""

from typing import Any, Dict, Optional, Type, Union

from google.protobuf import descriptor
from google.protobuf import message


class BlackboardValue:
  """Wrapper around values on blackboard.

  Provides access to values and enables auto-completion to parameterize skills
  with/access parts of the value.

  Attributes:
    parent: Parent value, if this value refers to a sub-field
    name: Sub-field name to access this blackboard value in CEL.
    scope: Blackboard scope, if used for blackboard service lookups.
    repeated: True, if this is a repeated field.
    result_type: Fields that this blackboard value has.
    toplevel_value_type: Message type this value refers to, if it is a toplevel
      value.
    fields: Sub-fields of this value.
    root_value_access_path: If set, refer to this value not via its name or its
      parents value_access_path, but use this as the root of the
      value_access_path.
    is_toplevel_value: True, if this value directly refers to a message.
    is_repeated: True, if the value refers to a repeated field.
    value_type: The type of the underlying message. Only valid for toplevel
      values.
  """

  _parent: Optional["BlackboardValue"]
  _name: str
  _scope: Optional[str]
  _repeated: bool
  _result_type: Dict[str, descriptor.FieldDescriptor]
  _toplevel_value_type: Optional[Type[message.Message]]
  _fields: Dict[str, descriptor.FieldDescriptor]
  _root_value_access_path: Optional[str] = None

  def __init__(
      self,
      fields: Dict[str, descriptor.FieldDescriptor],
      name: str,
      toplevel_value_type: Optional[Type[message.Message]],
      parent: Optional["BlackboardValue"],
      repeated: bool = False,
      scope: Optional[str] = None,
  ):
    """Creates a new BlackboardValue object.

    All entries of fields are registered as top level attributes and will be
    created as soon as they are accessed.

    Args:
      fields: Dictionary of field names and the corresponding descriptor for the
        given blackboard value. This is extracted from the descriptor of the
        original message and relevant in order to facilitate auto-completion for
        this wrapper.
      name: The field name in the original message or the result key, if this is
        a top level blackboard value. This will be used to create the CEL
        expression to access the value on the blackboard.
      toplevel_value_type: Message definition for the complete wrapped value,
        None for child values.
      parent: None if this references a top level blackboard expression,
        otherwise a reference to the blackboard value wrapping the parent
        message of the wrapped field.
      repeated: Indicates whether the field is repeated.
      scope: The scope for lookups, if the BlackboardValue has an explicit scope
        set.
    """

    self._parent = parent
    self._name = name
    self._repeated = repeated
    self._result_type = fields
    self._toplevel_value_type: Optional[Type[message.Message]] = (
        toplevel_value_type
    )
    self._fields = fields
    self._scope = scope

    # register all message fields as attributes to facilitate auto-completion
    for field_name in fields.keys():
      setattr(self, field_name, None)

  def __getattribute__(self, name: str) -> Any:
    """Returns the named attribute of BlackboardValue.

    If the requested name is part of the attributes which got registered in
    __init__, extract the relevant type information, create the corresponding
    BlackboardValue and return it. Fallback to default behavior otherwise.

    This way we can handle protos which contain themselves as only the
    currently accessed value gets computed.

    We are overriding __getattribute__ instead of __getattr__ as it is invoked
    before checking the actual attributes. Since we have added the attributes,
    which should become BlackboardValues once accessed, and given
    them a None value, __getattr__ would simply return this as it is only
    called as a fallback, in case an attribute is not found. However, we need
    to add the attributes before constructing them to facilitate
    auto-completion.

    Args:
      name: the name of attribute to return.

    Returns:
      The requested attribute, computing it in case it is supposed to be a
      BlackboardValue.
    """
    if name == "_result_type" or name not in self._result_type.keys():
      return super().__getattribute__(name)

    v = self._result_type[name]
    if v.containing_type and v.containing_type.full_name in [
        "google.protobuf.Duration",
        "google.protobuf.Timestamp",
    ]:
      if name == "seconds":
        name = "getSeconds()"
      elif name == "nanos":
        name = "getMilliseconds() * 1000000"
    repeated = v.label == descriptor.FieldDescriptor.LABEL_REPEATED
    if v.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
      return BlackboardValue(
          v.message_type.fields_by_name, name, None, self, repeated
      )
    return BlackboardValue({}, name, None, self, repeated)

  def __getitem__(
      self, key: Union[int, str, "BlackboardValue"]
  ) -> "BlackboardValue":
    if not isinstance(key, (int, BlackboardValue, str)):
      raise ValueError(
          "Expected an int value, string value or BlackboardValue for the key."
      )
    if isinstance(key, BlackboardValue):
      key = key.value_access_path()
    if self._repeated:
      return BlackboardValue(self._fields, f"[{key}]", None, self, False)
    raise ValueError("Not a repeated field.")

  def set_root_value_access_path(self, cel_path: str):
    """Make this BlackboardValue referred to by cel_path.

    This is usually used to create a BlackboardValue with the type information
    of a sub-field of another known value, where this sub-field is available on
    the blackboard under another name.

    Args:
      cel_path: The path to use for this blackboard value.
    """
    self._root_value_access_path = cel_path

  def value_access_path(self) -> str:
    """Provides access to the CEL expression for the blackboard.

    The returned string is used when accessing the value on the blackboard,
    which may not yet exist. This way we can also use parts of a message for
    parameterizing another skill or computing additional values.

    Returns:
      Its name if no parent is present, otherwise concatenates the name to the
      value_access_path of the parent. If root_value_access_path is set, returns
      that value instead. This will be used to access values within messages on
      the blackboard.
    """
    if self._root_value_access_path is not None:
      return self._root_value_access_path
    elif self._parent is None:
      return self._name
    else:
      if self._parent.is_repeated:
        return self._parent.value_access_path() + self._name
      return self._parent.value_access_path() + "." + self._name

  def scope(self) -> Optional[str]:
    return self._scope

  @property
  def is_toplevel_value(self) -> bool:
    return self._parent is None

  @property
  def is_repeated(self) -> bool:
    return self._repeated

  @property
  def value_type(self) -> Type[message.Message]:
    if self._toplevel_value_type:
      return self._toplevel_value_type
    raise ValueError(
        "Not a top-level blackboard value, type information not available."
    )
