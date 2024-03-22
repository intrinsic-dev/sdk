# Copyright 2023 Intrinsic Innovation LLC

"""Utility functions for handling skill parameters."""

from typing import List

from google.protobuf import descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import message

# This field can be used to determine if a field is a 'oneof'.
_ONEOF_INDEX = "oneof_index"


class SkillParameters:
  """A utility class which allows to inspect different skill parameters."""

  def __init__(
      self,
      default_message: message.Message,
      descriptor_proto: descriptor_pb2.DescriptorProto,
  ):
    """Creates an instance of the SkillParameters class.

    Args:
      default_message: A message which contains default parameters in all
        non-empty proto3 optional fields. Non-empty `repeated` and `oneof`
        fields are also considered default parameters.
      descriptor_proto: The proto descriptor of skill parameters.
    """

    self._default_message = default_message
    self._descriptor_proto = descriptor_pb2.DescriptorProto()
    self._descriptor_proto.CopyFrom(descriptor_proto)

  def _is_field_required(
      self, field_proto: descriptor_pb2.FieldDescriptorProto
  ) -> bool:
    """Returns True, if the field proto belongs to a required field.

    Args:
      field_proto: The field descriptor of the field which should be checked.
    """
    is_optional = field_proto.proto3_optional

    if field_proto.HasField(_ONEOF_INDEX) and not is_optional:
      # A oneof field is not considered required.
      return False
    elif field_proto.label == descriptor.FieldDescriptor.LABEL_REPEATED:
      # Repeated fields are considered required. If no clear user defined
      # default is specified, we return an empty list.
      return True
    elif not is_optional:
      # The field has no optional flag.
      # We can only check this after ruling out protos and repeated fields.
      return True

    # Return 'True' if the field is optional (declared by the user) and if it
    # has a default value.
    return is_optional and self._default_message.HasField(field_proto.name)

  def _is_field_optional(
      self, field_proto: descriptor_pb2.FieldDescriptorProto
  ) -> bool:
    """Returns True, if the field proto belongs to an optional field.

    Args:
      field_proto: The field descriptor of the field which should be checked.
    """
    is_optional = field_proto.proto3_optional

    if field_proto.HasField(_ONEOF_INDEX) and not is_optional:
      # A oneof field is not considered optional.
      return False
    elif field_proto.label == descriptor.FieldDescriptor.LABEL_REPEATED:
      # Repeated fields are considered required but have always a default value.
      return False

    return is_optional and not self._default_message.HasField(field_proto.name)

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

  def has_default_value(self, field_name: str) -> bool:
    """Returns True, if the field contains a default value.

    Args:
      field_name: The name of the field which should be checked.

    Raises:
      NameError: if the request field name cannot be found.
    """
    field_proto = self._get_field_proto(field_name)
    if (
        field_proto.proto3_optional
        or field_proto.HasField(_ONEOF_INDEX)
        and not field_proto.proto3_optional
    ):
      # This branch is hit if the field is 'optional' or a 'oneof'.
      return self._default_message.HasField(field_proto.name)
    # Repeated fields have always defaults and all else has no default value.
    return field_proto.label == descriptor.FieldDescriptor.LABEL_REPEATED

  def get_required_field_names(self) -> List[str]:
    """Returns all fields which must contain a parameter.

    This function is intended to be used to create a signature for a skill.
    Fields returned by this function will receive no special typing annotation.
    This is the reason why this function does not return 'oneof' entries. They
    are required in the signature but they need a special typing.Union
    annotation.

    Required fields are:
      * repeated fields
      * fields without optional keyword (user declared proto3 optional)

    Note: Fields which belong to a oneof are not returned as required fields.
          They require special handling.
    """
    return [
        field_proto.name
        for field_proto in self._descriptor_proto.field
        if self._is_field_required(field_proto)
    ]

  def get_optional_field_names(self) -> List[str]:
    """Returns all fields which are optional.

    This function is intended to be used to create a signature for a skill.
    Fields returned by this function will be annotated as typing.Optional.
    They are nullable, i.e. are not necessary to execute the function and they
    provide no default value.

    Optional fields are those proto fields which have a user specified
    'optional' flag and which have no default value assigned.
    """
    return [
        field_proto.name
        for field_proto in self._descriptor_proto.field
        if self._is_field_optional(field_proto)
    ]

  def message_has_optional_field(
      self, field_name: str, test_message: message.Message
  ) -> bool:
    """Returns True, if the field is present if required.

    A field is required if it is optional in the default message and actually
    provides an optional value.

    Important: The function is only a temporary bandaid and will be replaced
               with server side parameter checks. Client code should not try to
               do parameter validation on skills.

    Args:
      field_name: The name of the field which should be checked in the message.
      test_message: The message whose field will be checked.

    Raises:
      NameError: if the request field name cannot be found.
    """
    field_proto = self._get_field_proto(field_name)
    if field_proto.proto3_optional and self._default_message.HasField(
        field_proto.name
    ):
      return test_message.HasField(field_name)
    return True
