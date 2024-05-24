# Copyright 2023 Intrinsic Innovation LLC

"""Utility functions for handling skill parameters."""

from typing import Optional

from google.protobuf import descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import message
from intrinsic.skills.proto import skills_pb2

# This field can be used to determine if a field is a 'oneof'.
_ONEOF_INDEX = "oneof_index"


def _get_descriptor(
    parameter_description: skills_pb2.ParameterDescription,
    message_full_name: str,
) -> descriptor_pb2.DescriptorProto:
  """Pulls a message descriptor out of the descriptor fileset.

  Pulls the message descriptor for the given message name out of the descriptor
  fileset from the given parameter description of a skill.

  Args:
    parameter_description: The skill's parameter description proto.
    message_full_name: The full name of the message.

  Returns:
    A proto descriptor of the skill's top-level or nested parameter message.

  Raises:
    AttributeError: a descriptor matching the parameter's full message name
      cannot be found in the descriptor fileset.
  """

  def find_in_message_descriptor(
      msg: descriptor_pb2.DescriptorProto, relative_name: str
  ) -> Optional[descriptor_pb2.DescriptorProto]:
    if "." not in relative_name:
      return msg if msg.name == relative_name else None
    else:
      name, nested_relative_name = relative_name.split(".", 1)
      if msg.name != name:
        return None
      for nested_msg in msg.nested_type:
        if (
            found_msg := find_in_message_descriptor(
                nested_msg, nested_relative_name
            )
        ) is not None:
          return found_msg
      return None

  for file in parameter_description.parameter_descriptor_fileset.file:
    if not message_full_name.startswith(file.package):
      continue

    relative_name = message_full_name.removeprefix(file.package + ".")

    for msg in file.message_type:
      # Recursively search through message and its nested messages.
      if found_msg := find_in_message_descriptor(msg, relative_name):
        return found_msg

  raise AttributeError(
      f"Could not extract descriptor named {message_full_name} from "
      "parameter description"
  )


def _field_is_marked_optional(
    field_proto: descriptor_pb2.FieldDescriptorProto,
) -> bool:
  """Returns True if the given field is marked 'optional' in the proto source.

  Returns True if the given field is marked with the 'optional' keyword/label in
  the proto source file. This is not NOT about the 'optional' label in the field
  descriptor. For example, field descriptors for fields inside of a oneof
  implicitly have the 'optional' label set (but one cannot use the 'optional'
  label inside of a oneof in the proto source).

  Args:
    field_proto: The field descriptor of the field which should be checked.

  Returns:
    True if the given field is marked 'optional' in the proto source.
  """
  # Do not check field_proto.label against LABEL_OPTIONAL! Under the hood, many
  # fields are optional and have this label (e.g. fields in a oneof).
  return field_proto.proto3_optional


def _is_repeated_or_map_field(
    field_proto: descriptor_pb2.FieldDescriptorProto,
) -> bool:
  """Returns True if the given field is repeated or a map."""
  # Under the hood, maps are repeated fields.
  return field_proto.label == descriptor.FieldDescriptor.LABEL_REPEATED


def _is_oneof_field(field_proto: descriptor_pb2.FieldDescriptorProto) -> bool:
  """Returns True if the given field is inside of a oneof.

  Args:
    field_proto: The field descriptor of the field which should be checked.

  Returns:
    True if the given field is inside of a oneof in the actual proto definition.
  """
  # It's not enough to check for the presence of the oneof index. Plain
  # optional fields such as "optional double = 1;" also have a oneof index set
  # (pointing to a oneof set with only one member). We thus also check for the
  # absence of the proto3_optional flag (using the 'optional' keyword
  # inside of a oneof is not allowed).
  return field_proto.HasField(_ONEOF_INDEX) and not _field_is_marked_optional(
      field_proto
  )


class SkillParameters:
  """A utility class which allows to inspect different skill parameters."""

  _default_message: message.Message
  _descriptor_proto: descriptor_pb2.DescriptorProto

  def __init__(
      self,
      default_message: message.Message,
      parameter_description: skills_pb2.ParameterDescription,
  ):
    """Creates an instance of the SkillParameters class.

    Args:
      default_message: A message which contains default parameters in all
        non-empty proto3 optional fields. Non-empty `repeated` and `oneof`
        fields are also considered default parameters.
      parameter_description: The skill's parameter description.
    """

    self._default_message = default_message
    # We need the descriptor *proto* (descriptor_pb2.DescriptorProto and
    # friends) and not just its Python representation (
    # 'default_message.DESCRIPTOR' of type google.protobuf.descriptor.Descriptor
    # and friends). For example, in the Python representation we cannot reliably
    # check for the presence of the 'optional' keyword on message fields.
    self._descriptor_proto = _get_descriptor(
        parameter_description, default_message.DESCRIPTOR.full_name
    )

  def _get_field_proto(
      self, field_name: str
  ) -> descriptor_pb2.FieldDescriptorProto:
    """Returns the first field from the descriptor which matches the field name.

    Args:
      field_name: The name of the field for which the descriptor is returned.

    Raises:
      NameError: if the request field name cannot be found.
    """
    field_proto = next(
        (
            field_proto
            for field_proto in self._descriptor_proto.field
            if field_proto.name == field_name
        ),
        None,
    )
    if not field_proto:
      raise NameError(
          "Field proto for field with name '{}' could not be found.".format(
              field_name
          )
      )
    return field_proto

  def is_oneof_field(self, field_name: str) -> bool:
    """Returns True if the given field is inside of a oneof.

    Args:
        field_name: The name of the field which should be checked.

    Returns:
      True if the given field is inside of a oneof in the actual proto
      definition.
    """
    field_proto = self._get_field_proto(field_name)
    return _is_oneof_field(field_proto)

  def is_repeated_or_map_field(self, field_name: str) -> bool:
    """Returns True if the given field is a map or a repeated field.

    Args:
      field_name: The name of the field which should be checked.

    Returns:
      True if the given field is a map or a repeated field.
    """
    field_proto = self._get_field_proto(field_name)
    return _is_repeated_or_map_field(field_proto)

  def is_map_field(self, field_name: str) -> bool:
    """Returns True if the given field is a map.

    Args:
      field_name: The name of the field which should be checked.

    Returns:
      True if the given field is a map.
    """
    field = self._default_message.DESCRIPTOR.fields_by_name[field_name]
    return (
        field.label == descriptor.FieldDescriptor.LABEL_REPEATED
        # Under the hood, a map is a repeated field with a special,
        # auto-generated message type. This type has the 'map_entry' flag set.
        and field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
        and field.message_type.GetOptions().map_entry
    )

  def is_repeated_field(self, field_name: str) -> bool:
    """Returns True if the given field is a repeated field (but not a map!).

    Args:
      field_name: The name of the field which should be checked.

    Returns:
      True if the given field is a repeated field (but not a map!).
    """
    return self.is_repeated_or_map_field(field_name) and not self.is_map_field(
        field_name
    )

  def field_is_marked_optional(self, field_name: str) -> bool:
    """Returns True if the given field is marked 'optional' in the proto source.

    Returns True if the given field is marked with the 'optional' keyword/label
    in the proto source file. This is not NOT about the 'optional' label in the
    field descriptor. For example, field descriptors for fields inside of a
    oneof implicitly have the 'optional' label set (but one cannot use the
    'optional' label inside of a oneof in the proto source).

    Args:
     field_name: The name of the field which should be checked.

    Returns:
      True if the given field is marked 'optional' in the proto source.
    """
    field_proto = self._get_field_proto(field_name)
    return _field_is_marked_optional(field_proto)

  def is_optional_in_python_signature(self, field_name: str) -> bool:
    """Returns True if the field has an Optional type in Python.

    Returns True if the type of the field in the Python signature of a skill or
    message wrapper class has an Optional type, i.e., it is possible to pass
    None.

    Args:
      field_name: The name of the field which should be checked.

    Returns:
      True if the field has an Optional type in the Python signature.
    """
    field_proto = self._get_field_proto(field_name)
    if _is_oneof_field(field_proto):
      return True
    if _is_repeated_or_map_field(field_proto):
      return False
    return _field_is_marked_optional(
        field_proto
    ) and not self._default_message.HasField(field_proto.name)
