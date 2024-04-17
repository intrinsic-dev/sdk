# Copyright 2023 Intrinsic Innovation LLC

"""Utility functions for working with skill classes."""

from __future__ import annotations

import collections
import dataclasses
import datetime
import inspect
import textwrap
import time
from typing import AbstractSet, Any, Callable, Container, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Type, Union

from google.protobuf import descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import duration_pb2
from google.protobuf import message
from google.protobuf import message_factory
import grpc
from intrinsic.icon.proto import joint_space_pb2
from intrinsic.math.proto import pose_pb2
from intrinsic.math.python import data_types
from intrinsic.math.python import proto_conversion as math_proto_conversion
from intrinsic.motion_planning.proto import motion_target_pb2
from intrinsic.skills.client import skill_registry_client
from intrinsic.skills.proto import skills_pb2
from intrinsic.solutions import blackboard_value
from intrinsic.solutions import cel
from intrinsic.solutions import utils
from intrinsic.solutions import worlds
from intrinsic.solutions.internal import skill_parameters
from intrinsic.util.proto import descriptors
from intrinsic.world.proto import collision_settings_pb2
from intrinsic.world.proto import object_world_refs_pb2
from intrinsic.world.python import object_world_resources

_PYTHON_PACKAGE_SEPARATOR = "."
_PROTO_PACKAGE_SEPARATOR = "."

RESOURCE_SLOT_DECONFLICT_SUFFIX = "_resource"


def module_for_generated_skill(skill_package: str) -> str:
  """Generates the module name for a generated skill class.

  This module does not exist at runtime but there may be a type stub for it.

  Args:
    skill_package: The skill package name, e.g., 'ai.intrinsic'.

  Returns:
    A module name string, e.g., 'intrinsic.solutions.skills.ai.intrinsic'.
  """
  skills_python_package = __name__.replace(".internal.skill_utils", ".skills")
  if skill_package:
    return skills_python_package + "." + skill_package
  else:
    return skills_python_package


@dataclasses.dataclass
class ParameterInformation:
  """Class for collecting information about a parameter."""

  has_default: bool
  name: str
  default: Any
  doc_string: List[str]


# This must map according to:
# https://developers.google.com/protocol-buffers/docs/proto3#scalar
_PYTHONIC_SCALAR_FIELD_TYPE = {
    descriptor.FieldDescriptor.TYPE_BOOL: bool,
    descriptor.FieldDescriptor.TYPE_BYTES: bytes,
    descriptor.FieldDescriptor.TYPE_DOUBLE: float,
    # NB: In Python Protobuf enums are just ints with generated constants
    descriptor.FieldDescriptor.TYPE_ENUM: int,
    descriptor.FieldDescriptor.TYPE_FIXED32: int,
    descriptor.FieldDescriptor.TYPE_FIXED64: int,
    descriptor.FieldDescriptor.TYPE_FLOAT: float,
    descriptor.FieldDescriptor.TYPE_INT32: int,
    descriptor.FieldDescriptor.TYPE_INT64: int,
    descriptor.FieldDescriptor.TYPE_SFIXED32: int,
    descriptor.FieldDescriptor.TYPE_SFIXED64: int,
    descriptor.FieldDescriptor.TYPE_SINT32: int,
    descriptor.FieldDescriptor.TYPE_SINT64: int,
    descriptor.FieldDescriptor.TYPE_STRING: str,
    descriptor.FieldDescriptor.TYPE_UINT32: int,
    descriptor.FieldDescriptor.TYPE_UINT64: int,
}

_PYTHONIC_SCALAR_DEFAULT_VALUE = {
    descriptor.FieldDescriptor.TYPE_BOOL: False,
    descriptor.FieldDescriptor.TYPE_BYTES: b"",
    descriptor.FieldDescriptor.TYPE_DOUBLE: 0.0,
    descriptor.FieldDescriptor.TYPE_ENUM: 0,
    descriptor.FieldDescriptor.TYPE_FIXED32: 0,
    descriptor.FieldDescriptor.TYPE_FIXED64: 0,
    descriptor.FieldDescriptor.TYPE_FLOAT: 0.0,
    descriptor.FieldDescriptor.TYPE_INT32: 0,
    descriptor.FieldDescriptor.TYPE_INT64: 0,
    descriptor.FieldDescriptor.TYPE_SFIXED32: 0,
    descriptor.FieldDescriptor.TYPE_SFIXED64: 0,
    descriptor.FieldDescriptor.TYPE_SINT32: 0,
    descriptor.FieldDescriptor.TYPE_SINT64: 0,
    descriptor.FieldDescriptor.TYPE_STRING: "",
    descriptor.FieldDescriptor.TYPE_UINT32: 0,
    descriptor.FieldDescriptor.TYPE_UINT64: 0,
}


def _dict_from_proto(proto: Any) -> Dict[str, Tuple[Optional[str], Any]]:
  """Creates dict of pythonic field values for all values in proto.

  Args:
    proto: Proto to transform to dict

  Returns:
    dict of pythonic field values
  """
  collect = {}
  for k, v in proto.ListFields():
    message_name = _get_message_name(v, k)
    if k.label == descriptor.FieldDescriptor.LABEL_REPEATED and isinstance(
        v, Iterable
    ):
      python_repr = []
      for value in v:
        x = pythonic_field_value(value, k)
        python_repr.append((message_name, x))
    else:
      python_repr = pythonic_field_value(v, k)
    collect[k.name] = (message_name, python_repr)

  return collect


_MESSAGE_NAME_TO_PYTHON_VALUE = {
    "intrinsic_proto.skills.StringVector": lambda f: list(f.values),
    "intrinsic_proto.skills.VectorNdArray": lambda f: list(f.array),
    "intrinsic_proto.skills.VectorNdValue": lambda f: list(f.value),
    "intrinsic_proto.Pose": math_proto_conversion.pose_from_proto,
}

_MESSAGE_NAME_TO_PYTHONIC_TYPE = {
    "intrinsic_proto.skills.StringVector": Sequence[str],
    "intrinsic_proto.skills.VectorNdArray": Sequence[skills_pb2.VectorNdValue],
    "intrinsic_proto.skills.VectorNdValue": Sequence[float],
    duration_pb2.Duration.DESCRIPTOR.full_name: Union[
        int, float, datetime.timedelta, duration_pb2.Duration
    ],
}


def repeated_pythonic_field_type(
    field_descriptor: descriptor.FieldDescriptor,
    wrapper_classes: dict[str, Type[MessageWrapper]],
) -> Type[Sequence[Any]]:
  """Returns a 'pythonic' type based on the field_descriptor.

  Can be a Protobuf message for types for which we provide no native conversion.

  Args:
    field_descriptor: The Protobuf descriptor for the field
    wrapper_classes: Map from proto message names to corresponding message
      wrapper classes.

  Returns:
    The Python type of the field.
  """
  if field_descriptor.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
    if field_descriptor.message_type.GetOptions().map_entry:
      raise TypeError("Cannot get repeated pythonic type for proto map as list")
    if (
        field_descriptor.message_type.full_name
        in _MESSAGE_NAME_TO_PYTHONIC_TYPE
    ):
      return Sequence[
          _MESSAGE_NAME_TO_PYTHONIC_TYPE[
              field_descriptor.message_type.full_name
          ]
      ]
    return Sequence[wrapper_classes[field_descriptor.message_type.full_name]]

  return Sequence[_PYTHONIC_SCALAR_FIELD_TYPE[field_descriptor.type]]


def pythonic_field_type(
    field_descriptor: descriptor.FieldDescriptor,
    wrapper_classes: dict[str, Type[MessageWrapper]],
) -> Type[Any]:
  """Returns a 'pythonic' type based on the field_descriptor.

  Can be a Protobuf message for types for which we provide no native conversion.

  Args:
    field_descriptor: The Protobuf descriptor for the field
    wrapper_classes: Map from proto message names to corresponding message
      wrapper classes.

  Returns:
    The Python type of the field.
  """
  if field_descriptor.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
    message_full_name = field_descriptor.message_type.full_name
    if message_full_name in _MESSAGE_NAME_TO_PYTHONIC_TYPE:
      return _MESSAGE_NAME_TO_PYTHONIC_TYPE[message_full_name]
    return wrapper_classes[field_descriptor.message_type.full_name]

  return _PYTHONIC_SCALAR_FIELD_TYPE[field_descriptor.type]


def _field_to_string_vector(
    field_value: Union[Sequence[str], skills_pb2.StringVector],
) -> skills_pb2.StringVector:
  """Converts the field_value to skills_pb2.StringVector."""
  if isinstance(field_value, list) and all(
      isinstance(s, str) for s in field_value
  ):
    field_message = skills_pb2.StringVector()
    field_message.values.extend(field_value)
    return field_message
  elif isinstance(field_value, skills_pb2.StringVector):
    return field_value
  raise TypeError(f"Value {field_value} not a list of strings")


def _field_to_vector_nd_array(
    field_value: Union[
        Sequence[skills_pb2.VectorNdValue], skills_pb2.VectorNdArray
    ],
) -> skills_pb2.VectorNdArray:
  """Converts the field_value to skills_pb2.VectorNdArray."""
  if isinstance(field_value, list) and all(
      isinstance(v, skills_pb2.VectorNdValue) for v in field_value
  ):
    field_message = skills_pb2.VectorNdArray()
    field_message.array.extend(field_value)
    return field_message
  elif isinstance(field_value, skills_pb2.VectorNdArray):
    return field_value
  raise TypeError(f"Value {field_value} is not convertible to a VectorNdArray")


def _field_to_vector_nd_value(
    field_value: Union[skills_pb2.VectorNdValue, Sequence[float]],
) -> skills_pb2.VectorNdValue:
  """Converts the field_value to skills_pb2.VectorNdValue."""
  if isinstance(field_value, skills_pb2.VectorNdValue):
    return field_value
  elif isinstance(field_value, list) and all(
      isinstance(s, float) for s in field_value
  ):
    field_message = skills_pb2.VectorNdValue()
    field_message.value.extend(field_value)
    return field_message
  raise TypeError(f"Value {field_value} not a VectorNdValue")


def _field_to_pose_3d(field_value: data_types.Pose3) -> pose_pb2.Pose:
  """Converts the field_value to pose_pb2.Pose."""
  if not isinstance(field_value, data_types.Pose3):
    raise TypeError(f"Value {field_value} not a Pose3")
  return math_proto_conversion.pose_to_proto(field_value)


def _field_to_object_reference(
    field_value: Union[
        object_world_resources.WorldObject,
        object_world_refs_pb2.ObjectReference,
    ],
) -> object_world_refs_pb2.ObjectReference:
  """Converts a field_value to object_world_refs_pb2.ObjectReference."""
  if isinstance(field_value, object_world_refs_pb2.ObjectReference):
    return field_value
  elif isinstance(field_value, object_world_resources.WorldObject):
    return field_value.reference
  raise TypeError(
      f"Value: {field_value} is not convertible to an ObjectReference."
  )


def _field_to_frame_reference(
    field_value: Union[
        object_world_resources.Frame, object_world_refs_pb2.FrameReference
    ],
) -> object_world_refs_pb2.FrameReference:
  """Converts a field_value to object_world_refs_pb2.FrameReference."""
  if isinstance(field_value, object_world_refs_pb2.FrameReference):
    return field_value
  elif isinstance(field_value, object_world_resources.Frame):
    return field_value.reference
  raise TypeError(
      f"Value: {field_value} is not convertible to an FrameReference."
  )


def _field_to_transform_node_reference(
    field_value: Union[
        object_world_resources.WorldObject,
        object_world_resources.Frame,
        object_world_refs_pb2.TransformNodeReference,
    ],
) -> object_world_refs_pb2.TransformNodeReference:
  """Converts a field_value to TransformNodeReference.

  The object_world_refs_pb2.TransformNodeReference either contains an
  id or a TransformNodeReferenceByName.

  Args:
    field_value: The value that should be converted.

  Returns:
    A TransformNodeReference with an object or frame reference.
  """
  if isinstance(field_value, object_world_refs_pb2.TransformNodeReference):
    return field_value
  elif isinstance(field_value, object_world_resources.WorldObject):
    return object_world_refs_pb2.TransformNodeReference(id=field_value.id)
  elif isinstance(field_value, object_world_resources.Frame):
    return object_world_refs_pb2.TransformNodeReference(id=field_value.id)
  raise TypeError(
      f"Value: {field_value} is not convertible to a TransformNodeReference."
  )


def _field_to_object_or_entity_reference(
    field_value: object_world_resources.WorldObject,
) -> collision_settings_pb2.ObjectOrEntityReference:
  """Converts a field_value to ObjectOrEntityReference.

  Args:
    field_value: The value that should be converted. Currently, only world
      objects are supported because entities are not yet accessible (i.e., there
      is no object_world_resources.ObjectEntity type).

  Returns:
    An ObjectOrEntityReference containing an object reference.
  """
  if not isinstance(field_value, object_world_resources.WorldObject):
    raise TypeError(
        f"Value: {field_value} is not convertible to an"
        " ObjectOrEntityReference."
    )
  return collision_settings_pb2.ObjectOrEntityReference(
      object=field_value.reference
  )


def _field_to_motion_planning_cartesian_motion_target(
    field_value: worlds.CartesianMotionTarget,
) -> motion_target_pb2.CartesianMotionTarget:
  """Converts a field_value to the object world CartesianMotionTarget."""
  if isinstance(field_value, worlds.CartesianMotionTarget):
    return field_value.proto
  raise TypeError(
      f"Value: {field_value} is not convertible to a CartesianMotionTarget."
  )


def _field_to_joint_vec_target(
    field_value: object_world_resources.JointConfiguration,
) -> joint_space_pb2.JointVec:
  field_message = joint_space_pb2.JointVec()
  if isinstance(field_value, object_world_resources.JointConfiguration):
    field_message.joints.extend(field_value.joint_position)
    return field_message
  raise TypeError(f"Cannot convert {field_value} to JointVec.")


def _field_to_collision_settings(
    field_value: worlds.CollisionSettings,
) -> collision_settings_pb2.CollisionSettings:
  if isinstance(field_value, worlds.CollisionSettings):
    return field_value.proto
  raise TypeError(f"Cannot convert {field_value} to CollisionSettings.")


def _field_to_duration(
    field_value: Union[datetime.timedelta, float, int, duration_pb2.Duration],
) -> duration_pb2.Duration:
  """Create a Duration object from various inputs.

  This will transform datetime.timedelta and ints/floats while also accepting an
  already created Duration object.

  Args:
    field_value: The value to transform to duration_pb2.Duration. If it is a
      float or int value the value is interpreted as seconds.

  Returns:
    duration_pb2.Duration object from the input.

  Raises:
    TypeError if the field_value is not one of the expected types.
  """
  if isinstance(field_value, duration_pb2.Duration):
    return field_value
  elif isinstance(field_value, datetime.timedelta):
    duration_proto = duration_pb2.Duration()
    duration_proto.FromTimedelta(field_value)
    return duration_proto
  elif isinstance(field_value, int):
    duration_proto = duration_pb2.Duration()
    duration_proto.FromSeconds(field_value)
    return duration_proto
  elif isinstance(field_value, float):
    duration_proto = duration_pb2.Duration()
    i, d = divmod(field_value, 1)
    duration_proto.seconds = int(i)
    duration_proto.nanos = int(d * 1e9)
    return duration_proto
  raise TypeError(
      "Expected value of type int, float, datetime.timedelta or"
      f" duration_pb2.Duration, got {type(field_value)}"
  )


_PYTHONIC_MESSAGE_FIELD_TYPE = {
    skills_pb2.StringVector.DESCRIPTOR.full_name: _field_to_string_vector,
    skills_pb2.VectorNdArray.DESCRIPTOR.full_name: _field_to_vector_nd_array,
    skills_pb2.VectorNdValue.DESCRIPTOR.full_name: _field_to_vector_nd_value,
    pose_pb2.Pose.DESCRIPTOR.full_name: _field_to_pose_3d,
    joint_space_pb2.JointVec.DESCRIPTOR.full_name: _field_to_joint_vec_target,
    collision_settings_pb2.CollisionSettings.DESCRIPTOR.full_name: (
        _field_to_collision_settings
    ),
    collision_settings_pb2.ObjectOrEntityReference.DESCRIPTOR.full_name: (
        _field_to_object_or_entity_reference
    ),
    motion_target_pb2.CartesianMotionTarget.DESCRIPTOR.full_name: (
        _field_to_motion_planning_cartesian_motion_target
    ),
    duration_pb2.Duration.DESCRIPTOR.full_name: _field_to_duration,
    object_world_refs_pb2.FrameReference.DESCRIPTOR.full_name: (
        _field_to_frame_reference
    ),
    object_world_refs_pb2.TransformNodeReference.DESCRIPTOR.full_name: (
        _field_to_transform_node_reference
    ),
    object_world_refs_pb2.ObjectReference.DESCRIPTOR.full_name: (
        _field_to_object_reference
    ),
}


def pythonic_to_proto_message(
    field_value: Any, message_descriptor: descriptor.Descriptor
) -> message.Message:
  """Performs a conversion to a Protobuf message from 'pythonic' field_value.

  If there is no special conversion, or the field_value is already
  in the correct message type, then the field_value is returned untouched.

  Args:
    field_value: The value to be placed in the corresponding message field.
    message_descriptor: The Protobuf descriptor for the message.

  Returns:
    A Protobuf message containing the desire value from field_value.

  Raises:
    TypeError if the field_value is not convertible to a message of the type
    indicated by message_descriptor.
  """
  if (
      isinstance(field_value, message.Message)
      and field_value.DESCRIPTOR.full_name == message_descriptor.full_name
  ):
    return field_value
  if isinstance(field_value, MessageWrapper):
    return field_value.wrapped_message
  # Provide implicit conversion for some non-message types.
  if message_descriptor.full_name in _PYTHONIC_MESSAGE_FIELD_TYPE:
    return _PYTHONIC_MESSAGE_FIELD_TYPE[message_descriptor.full_name](
        field_value
    )
  raise TypeError(
      "Type of value {} is of type {}. Must be convertible to message type {}"
      .format(field_value, type(field_value), message_descriptor.full_name)
  )


def _dict_to_python_string(
    value: Dict[Any, Any],
    message_name: Optional[str],
    prefix_options: utils.PrefixOptions,
    skill_name: str,
) -> str:
  """Generates Python representation given a dict and its message name.

  Args:
    value: The dict to transcribe to Python code.
    message_name: The full message name.
    prefix_options: The PrefixOptions for generating the Python representation.
    skill_name: name of the skill the value belongs to

  Returns:
    String containing Python representation for given dict.
  """
  collect = []
  for name, (inner_message, python_value) in value.items():
    python_value = _to_python_string(
        python_value, inner_message, prefix_options, skill_name
    )
    collect.append(f"{name}={python_value}")
  return (
      f'{prefix_options.skill_prefix}["'
      f'{skill_name}"].message_classes["{message_name}"]'
      f'({", ".join(collect)})'
  )


def _to_python_string(
    value: Any,
    message_name: Optional[str],
    prefix_options: utils.PrefixOptions,
    skill_name: str,
) -> str:
  """Generates Python representation given a value and its message name.

  Args:
    value: The value to transcribe to Python code.
    message_name: The full message name.
    prefix_options: The PrefixOptions for generating the Python representation.
    skill_name: name of the skill the value belongs to

  Returns:
    String containing Python representation for given value.
  """
  if isinstance(value, dict) and message_name:
    return _dict_to_python_string(
        value, message_name, prefix_options, skill_name
    )
  if isinstance(value, list):
    collect_entries = []
    for elem in value:
      if isinstance(elem, Tuple):
        (message_name, elem) = elem
      collect_entries.append(
          _to_python_string(elem, message_name, prefix_options, skill_name)
      )
    return f"[{', '.join(collect_entries)}]"
  return str(value)


def _get_message_name(
    field_value: Any, field_descriptor: descriptor.FieldDescriptor
) -> Optional[str]:
  """Retrieves the message name from a given proto.

  In case of a repeated field uses the first of the given values.
  Returns None if the given value is no message or has no DESCRIPTOR field

  Args:
    field_value: The Protobuf value to retrieve the message name from.
    field_descriptor: The FieldDescriptor for the field in the message.

  Returns:
    message_name for the given value, None if the value is no message
  """

  if hasattr(field_value, "DESCRIPTOR"):
    return field_value.DESCRIPTOR.full_name
  if (
      field_descriptor.label == descriptor.FieldDescriptor.LABEL_REPEATED
      and isinstance(field_value, Sequence)
  ):
    if field_value and hasattr(field_value[0], "DESCRIPTOR"):
      return field_value[0].DESCRIPTOR.full_name
  return None


def pythonic_field_to_python_string(
    field_value: Any,
    field_descriptor: descriptor.FieldDescriptor,
    prefix_options: utils.PrefixOptions,
    skill_name: str,
) -> str:
  """Returns Python representation for a set of 'special' message types.

  Args:
    field_value: The Protobuf default value.
    field_descriptor: The FieldDescriptor for the field in the message.
    prefix_options: The PrefixOptions for generating the Python representation.
    skill_name: name of the skill the value belongs to

  Returns:
    String containing Python representation for given field.
  """

  value = pythonic_field_value(field_value, field_descriptor)
  if hasattr(value, "to_python_string"):
    return value.to_python_string(prefix_options)
  message_name = _get_message_name(field_value, field_descriptor)

  return _to_python_string(value, message_name, prefix_options, skill_name)


def pythonic_field_value(
    field_value: Any, field_descriptor: descriptor.FieldDescriptor
) -> Any:
  """Performs conversion for a protobuf value to pythonic types.

  Args:
    field_value: The Protobuf value.
    field_descriptor: The FieldDescriptor for the field in the message.

  Returns:
    The field value, possibly converted to another type.
  """
  # If it's a string return its representation
  if field_descriptor.type == descriptor.FieldDescriptor.TYPE_STRING:
    return repr(field_value)

  # No conversion needed if it is not a message.
  if field_descriptor.type != descriptor.FieldDescriptor.TYPE_MESSAGE:
    return field_value

  if (
      field_descriptor.label == descriptor.FieldDescriptor.LABEL_REPEATED
      and field_descriptor.message_type.GetOptions().map_entry
      and isinstance(field_value, Mapping)
  ):
    value_type = field_descriptor.message_type.fields_by_name["value"]
    values = {}
    for k, v in field_value.items():
      values[k] = pythonic_field_value(v, value_type)
    return values

  if (
      field_descriptor.label == descriptor.FieldDescriptor.LABEL_REPEATED
      and isinstance(field_value, Iterable)
  ):
    values = []
    for value in field_value:
      values.append(pythonic_field_value(value, field_descriptor))
    return values

  # For any other message, we have no special conversion
  return _dict_from_proto(field_value)


def pythonic_field_default_value(
    field_value: Any, field_descriptor: descriptor.FieldDescriptor
) -> Any:
  """Performs conversion for a set of 'special' message types to pythonic types.

  Args:
    field_value: The Protobuf default value.
    field_descriptor: The FieldDescriptor for the field in the message.

  Returns:
    The default field value, possibly converted to another type.
  """
  # No conversion needed if it is not a message.
  if field_descriptor.type != descriptor.FieldDescriptor.TYPE_MESSAGE:
    return field_value

  if field_value.DESCRIPTOR.full_name in _MESSAGE_NAME_TO_PYTHON_VALUE:
    return _MESSAGE_NAME_TO_PYTHON_VALUE[field_value.DESCRIPTOR.full_name](
        field_value
    )

  if (
      field_descriptor.label == descriptor.FieldDescriptor.LABEL_REPEATED
      and field_descriptor.message_type.GetOptions().map_entry
  ):
    return {m["key"]: m["value"] for m in field_value}

  # For any other message, we have no special conversion
  return field_value


def _check_no_multiply_defined_oneof(
    field_descriptor_map: Mapping[str, descriptor.FieldDescriptor],
    field_names: Iterable[str],
):
  """Checks that no elements of field_names are associated with the same oneof.

  All field_names must be contained in field_descriptor_map.keys().

  Args:
    field_descriptor_map: A map of field_names to FieldDescriptors.
    field_names: A list of field names to check.

  Raises:
    ValueError if multiple elements of field_names are fields of the same
    containing oneof.
  """
  oneofs = {}
  for field_name in field_names:
    containing_oneof = field_descriptor_map[field_name].containing_oneof
    if containing_oneof is not None:
      if containing_oneof in oneofs.keys():
        raise ValueError(
            "Multiple fields have the same containing oneof . "
            f"Fields: '{field_name}' and '{oneofs[containing_oneof].name}'. "
            f"Oneof: '{containing_oneof.name}'"
        )
      oneofs[containing_oneof] = field_descriptor_map[field_name]


def set_fields_in_msg(
    msg: message.Message, fields: Dict[str, Any]
) -> List[str]:
  """Sets the fields in the msg.

  Args:
    msg: Protobuf message to set fields of.
    fields: Dictionary of the fields to set in the message keyed by field name.

  Returns:
    List of keys in fields applied to msg.

  Raises:
    KeyError: If a set of fields in fields would apply to the same oneof in msg.
    TypeError: A field in fields has a mismatched type compared to the field in
      msg.
  """
  field_descriptor_map = msg.DESCRIPTOR.fields_by_name
  params_set = []

  for field_name in fields.keys():
    if field_name not in field_descriptor_map:
      raise KeyError(
          f'Field "{field_name}" does not exist in message'
          f' "{msg.DESCRIPTOR.full_name}".'
      )

  try:
    _check_no_multiply_defined_oneof(field_descriptor_map, fields.keys())
  except ValueError as e:
    raise KeyError(
        "Multiple parameters to be set are part of the same oneof"
    ) from e

  for field_name, arg_value in fields.items():
    if isinstance(
        arg_value, blackboard_value.BlackboardValue | cel.CelExpression
    ):
      continue
    field_desc = field_descriptor_map[field_name]
    field_type = field_desc.type
    field_message_type = field_desc.message_type
    if (
        field_descriptor_map[field_name].label
        == descriptor.FieldDescriptor.LABEL_REPEATED
    ):
      if (
          field_type == descriptor.FieldDescriptor.TYPE_MESSAGE
          and field_message_type.GetOptions().map_entry
      ):
        msg.ClearField(field_name)
        map_field = getattr(msg, field_name)
        if isinstance(arg_value, set):
          raise TypeError(
              "Got set where expected dict, initialized like {'foo', 1}'"
              " instead of {'foo': 1}?"
          )

        value_type = field_desc.message_type.fields_by_name["value"]

        for k, v in arg_value.items():
          if isinstance(
              v, blackboard_value.BlackboardValue | cel.CelExpression
          ):
            raise TypeError(
                f"Cannot set field {field_name}['{k}'] from blackboard"
                " value, not supported for maps"
            )

          if value_type.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
            if isinstance(v, MessageWrapper):
              map_field[k].CopyFrom(v.wrapped_message)
            elif isinstance(v, message.Message):
              # The messages are from different pools, therefore go through
              # serialization and parsing again
              map_field[k].ParseFromString(v.SerializeToString())
            else:
              raise TypeError(
                  f"Cannot set field {field_name}['{k}'] from non-message value"
              )
          else:
            map_field[k] = v

      else:
        repeated_field = getattr(msg, field_name)
        del repeated_field[:]  # clear field default since value was provided
        for value in arg_value:
          if isinstance(
              value, blackboard_value.BlackboardValue | cel.CelExpression
          ):
            if field_message_type is not None:
              repeated_field.add()
            else:
              repeated_field.append(_PYTHONIC_SCALAR_DEFAULT_VALUE[field_type])

          elif field_message_type is not None:
            repeated_field.add().ParseFromString(
                pythonic_to_proto_message(
                    value, field_message_type
                ).SerializeToString()
            )

          elif field_type in _PYTHONIC_SCALAR_FIELD_TYPE and isinstance(
              value, _PYTHONIC_SCALAR_FIELD_TYPE[field_type]
          ):
            repeated_field.append(value)

          else:
            raise TypeError(
                f"arg: {field_name}, with value {fields[field_name]} is of type"
                f" {type(arg_value)}. Must be of type"
                f" {type(getattr(msg, field_name))}"
            )
    elif field_type == descriptor.FieldDescriptor.TYPE_MESSAGE:
      submessage = getattr(msg, field_name)
      submessage.ParseFromString(
          pythonic_to_proto_message(
              arg_value, field_message_type
          ).SerializeToString()
      )
    elif field_type in _PYTHONIC_SCALAR_FIELD_TYPE and isinstance(
        arg_value, _PYTHONIC_SCALAR_FIELD_TYPE[field_type]
    ):
      setattr(msg, field_name, arg_value)
    else:
      raise TypeError(
          "arg: {}, with value {} is of type {}. Must be of type {}".format(
              field_name,
              arg_value,
              type(arg_value),
              type(getattr(msg, field_name)),
          )
      )
    params_set.append(field_name)
  return params_set


def _unset_non_oneofs(
    msg: message.Message,
) -> Dict[str, descriptor.FieldDescriptor]:
  """Returns a dictionary of non-oneof fields in the message.

  Args:
    msg: A Protobuf message.

  Returns:
    The unset fields, keyed by field name.
  """
  unset_non_oneofs = {}
  for field in msg.DESCRIPTOR.fields:
    if field.containing_oneof is not None:
      continue

    # NB: cannot be optional, they're always present, so HasField is useless for
    # them; it seems to always return false.
    if field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
      continue

    # Check for optional and message fields that they are, indeed, set
    if field.type == descriptor.FieldDescriptor.TYPE_MESSAGE and msg.HasField(
        field.name
    ):
      continue

    unset_non_oneofs[field.name] = field
  return unset_non_oneofs


def _unset_oneofs(msg: message.Message) -> List[descriptor.OneofDescriptor]:
  """Returns a list of unset oneofs in the message.

  Args:
    msg: A Protobuf message.

  Returns:
    The unset oneofs.
  """
  unset_oneofs = []
  for oneof in msg.DESCRIPTOR.oneofs:
    if msg.WhichOneof(oneof.name) is None:
      unset_oneofs.append(oneof)

  return unset_oneofs


def check_missing_fields_in_msg(
    skill_params: skill_parameters.SkillParameters,
    msg: message.Message,
    fields: AbstractSet[str],
) -> None:
  """Verifies that all required fields in the input message are set.

  Args:
    skill_params: The helper class to inspect skill parameters.
    msg: The message to check.
    fields: A set of field names.

  Raises:
    KeyError: if any singular field is unset, unless another field in the same
      containing oneof is set.
  """
  for required_field_name in skill_params.get_required_field_names():
    if (
        required_field_name not in fields
        and not skill_params.message_has_optional_field(
            required_field_name, msg
        )
    ):
      raise KeyError(
          f"Skill parameter argument '{required_field_name}' is missing"
      )


# Workaround for compatibility with different protobuf versions to prevent
# GetMessages() from printing a warning if GetMessageClassesForFiles() is
# available.
def _get_message_classes_for_files(
    files: List[str], desc_pool: descriptor_pool.DescriptorPool
) -> Dict[str, Type[message.Message]]:
  if hasattr(message_factory, "GetMessageClassesForFiles"):
    return message_factory.GetMessageClassesForFiles(files, desc_pool)
  else:
    msg_factory = message_factory.MessageFactory(pool=desc_pool)
    return msg_factory.GetMessages(files)


# Workaround for compatibility with different protobuf versions to prevent
# GetPrototype() from printing a warning if GetMessageClass() is available.
def _get_message_class(msg: descriptor.Descriptor) -> Type[message.Message]:
  if hasattr(message_factory, "GetMessageClass"):
    return message_factory.GetMessageClass(msg)
  else:
    return message_factory.MessageFactory().GetPrototype(msg)


def determine_failed_generate_proto_infra_from_filedescriptorset(
    filedescriptor_set: descriptor_pb2.FileDescriptorSet,
) -> str:
  """Determines, which class failed to generate the infrastructure pieces for.

  Proceeds like generate_proto_infra_from_filedescriptorset, but generate
  classes for protos individually, so that an external function can determine,
  what message is not importing correctly.

  Args:
    filedescriptor_set: The file descriptor set (a set of file descriptors,
      which each contain a set of proto descriptors) that would also be passed
      to generate_proto_infra_from_filedescriptorset.

  Returns:
    The last proto name that was tried to generate a class for and failed. Empty
    string, if none failed.
  """
  desc_pool = descriptors.create_descriptor_pool(filedescriptor_set)

  last_tried = ""
  try:
    for file_proto in filedescriptor_set.file:
      last_tried = file_proto.name
      _get_message_classes_for_files([file_proto.name], desc_pool)
  except NotImplementedError:
    return last_tried
  return ""


def generate_proto_infra_from_filedescriptorset(
    filedescriptor_set: descriptor_pb2.FileDescriptorSet,
) -> Tuple[
    descriptor_pool.DescriptorPool,
    Dict[str, Type[message.Message]],
]:
  """Generates the infrastructure pieces to deal with protos from a given set.

  This function creates a hermetic descriptor pool from that, a message factory
  based on that pool, and a mapping from type names to proto classes. This is
  the typical infrastructure required to deal with such messages in a hermetic
  fashion, i.e., without importing apriori known proto message packages.

  Args:
    filedescriptor_set: To publicly document a proto-based interface a
      transitive closure of proto descriptors is required. This is given as a
      file descriptor set (a set of file descriptors, which each contain a set
      of proto descriptors). It is provided by a discovery API.

  Returns:
    Tuple consisting of a proto descriptor pool populated with the proto types
    from the input file descriptor set, a message factory that can create
    messages from that pool, and a mapping from type names (of protos in the
    pool) to message classes.
  """
  desc_pool = descriptors.create_descriptor_pool(filedescriptor_set)
  message_classes = _get_message_classes_for_files(
      [file_proto.name for file_proto in filedescriptor_set.file], desc_pool
  )
  additional_msg_classes = {}
  for name, msg in message_classes.items():
    _get_nested_classes(msg.DESCRIPTOR, name, additional_msg_classes)

  for key, msg in additional_msg_classes.items():
    message_classes[key] = _get_message_class(msg)
  return desc_pool, message_classes


def _get_nested_classes(
    desc: descriptor.Descriptor,
    name: str,
    additional_msg_classes: Dict[str, descriptor.Descriptor],
):
  """Generates a mapping from type names to proto classes for nested types.

  Args:
    desc: Descriptor to inspect for nested_types.
    name: prefix for the type name.
    additional_msg_classes: map in which the nested types are collected.
  """
  for nested_type in desc.nested_types:
    type_name = name + "." + nested_type.name
    if type_name not in additional_msg_classes:
      additional_msg_classes[type_name] = nested_type
      _get_nested_classes(nested_type, type_name, additional_msg_classes)


def get_field_classes_to_alias(
    param_descriptor: descriptor.Descriptor,
    message_classes: Dict[str, Type[message.Message]],
    collected_classes: List[
        Tuple[str, Type[message.Message], descriptor.FieldDescriptor]
    ],
):
  """Gets classes which should be aliased as top-level members.

  This checks param_descriptor for fields which specify sub-messages.
  These are to be aliased at the enclosing class scope for easy access.

  Args:
    param_descriptor: parameter proto descriptor
    message_classes: mapping from type name to message class for all messages in
      the class's hermetic descriptor pool.
    collected_classes: List containing all collected classes up to this point.

  Returns:
    For each message class type of sub-message fields a tuple with the nested
    class attribute name (proto message short name), message class, and field
    descriptor.
  """

  for field in param_descriptor.fields:
    if (
        field.message_type is not None
        and field.message_type.full_name in message_classes
        and (
            # Do not alias auto-generated map *Entry classes
            field.type != descriptor.FieldDescriptor.TYPE_MESSAGE
            or not field.message_type.GetOptions().map_entry
        )
    ):
      nested_class_attr_name = message_classes[
          field.message_type.full_name
      ].__name__
      found = [
          elem
          for elem in collected_classes
          if (
              elem[0] == nested_class_attr_name
              and elem[2].full_name == field.full_name
          )
      ]
      if not any(found):
        collected_classes.append((
            nested_class_attr_name,
            message_classes[field.message_type.full_name],
            field,
        ))
        get_field_classes_to_alias(
            field.message_type, message_classes, collected_classes
        )


class MessageWrapper:
  """Message wrapper base.

  We wrap all messages which are used as parameter or return values.
  This enables us to introspect the types and generate
  documentation and augment the constructors with meta-information for
  auto-completion. Additionally, this allows us to handle BlackboardValues for
  parameterization of the message, as they need to be handled specially and
  cannot be added to the message directly.
  """

  # Class attributes
  _wrapped_type: Type[message.Message]

  # Instance attributes
  _wrapped_message: Optional[message.Message]
  _blackboard_params: dict[str, Any]

  def __init__(self):
    """This constructor normally will not be called from outside."""
    self._wrapped_message = None
    self._blackboard_params = {}

  def _set_params(self, **kwargs) -> List[str]:
    """Set parameters of message.

    Args:
      **kwargs: Map from field name to value as specified by the message.
        Unknown arguments are silently ignored.

    Returns:
      List of keys in arguments consumed as fields.
    Raises:
      TypeError: If passing a value that does not match a field's type.
      KeyError: If failing to provide a value for any skill argument.
    """
    consumed = []
    for param_name, value in kwargs.items():
      self._set_parameter(param_name, value, consumed)
    return consumed

  def _set_parameter(
      self, key: str, value: Any, consumed: Optional[List[str]] = None
  ):
    """Sets a single parameter of the message.

    Args:
      key: The parameter name.
      value: The value for the parameter.
      consumed: List of consumed parameters to append the key to in case it was
        consumed.

    Raises:
      KeyError: If a set of fields in fields would apply to the same oneof in
      msg.
      TypeError: If passing a value that does not match a field's type.
    """
    if self.wrapped_message is None:
      raise ValueError(
          f"Cannot set field {key} as the wrapped message is None."
      )

    msg = self.wrapped_message
    if msg is not None and key not in msg.DESCRIPTOR.fields_by_name:
      raise KeyError(
          f'Field "{key}" does not exist in message'
          f' "{msg.DESCRIPTOR.full_name}".'
      )

    if self._process_blackboard_params(key, value, consumed):
      return
    if isinstance(value, list):
      for index, entry in enumerate(value):
        self._process_blackboard_params(f"{key}[{index}]", entry, consumed)

    fields = set_fields_in_msg(self.wrapped_message, {key: value})
    if consumed is not None:
      consumed.extend(fields)

  def _process_blackboard_params(
      self, key: str, value: Any, consumed: Optional[List[str]] = None
  ) -> bool:
    """Adds a parameter mapping in case the value is a blackboard parameter.

    Parameters which will be provided during runtime by the blackboard are not
    part of the parameter proto directly but need to be specified separately.

    Args:
      key: The parameter name.
      value: The value for the parameter.
      consumed: List of already consumed parameters, to ensure no missing
        parameters.

    Returns:
      True if the value requires no further processing, False otherwise.
    """

    if isinstance(value, blackboard_value.BlackboardValue):
      self._blackboard_params[key] = value.value_access_path()
      if consumed is not None:
        consumed.append(key)
      return True

    elif isinstance(value, cel.CelExpression):
      self._blackboard_params[key] = str(value)
      if consumed is not None:
        consumed.append(key)
      return True

    elif isinstance(value, MessageWrapper):
      for k, v in value.blackboard_params.items():
        self._blackboard_params[key + "." + k] = v
    return False

  @property
  def wrapped_message(self) -> Optional[message.Message]:
    if hasattr(self, "_wrapped_message"):
      return self._wrapped_message
    return None

  @utils.classproperty
  def wrapped_type(cls) -> Type[message.Message]:  # pylint:disable=no-self-argument
    return cls._wrapped_type

  @property
  def blackboard_params(self) -> Dict[str, str]:
    return self._blackboard_params

  def __setattr__(self, name: str, value: Any):
    """Sets a parameter in the underlying message, if part of the message.

    This is necessary to support the current syntax when initializing messages
    which usually creates the message object first and then adds the arguments.

    Args:
      name: The parameter name.
      value: The value for the parameter.

    Raises:
      KeyError: If a set of fields in fields would apply to the same oneof in
      msg.
      TypeError: If passing a value that does not match a field's type.
    """
    msg = self.wrapped_message

    if msg is not None and name in msg.DESCRIPTOR.fields_by_name:
      self._set_parameter(name, value)
    else:
      super().__setattr__(name, value)


def _gen_wrapper_class(
    wrapped_type: Type[message.Message],
    skill_name: str,
    skill_package: str,
    field_doc_strings: Dict[str, str],
) -> Type[Any]:
  """Generates a new message wrapper class type.

  We need to do this because we already need the constructor to pass instance
  information and therefore need to overload __init__. In order to be able to
  augment it with meta info for auto-completion, we need to dynamically generate
  it. Since __init__ is a class and not an instance method, we cannot simply
  assign the function, but need to generate an entire type for it.

  Args:
    wrapped_type: Message to wrap.
    skill_name: Name of the skill.
    skill_package: Package name of the skill.
    field_doc_strings: Dict mapping from field name to doc string comment.

  Returns:
    A new type for a MessageWrapper sub-class.
  """
  type_class = type(
      # E.g.: 'Pose'
      wrapped_type.DESCRIPTOR.name,
      (MessageWrapper,),
      {
          "__doc__": _gen_init_docstring(wrapped_type, field_doc_strings),
          # E.g.: 'move_robot.intrinsic_proto.Pose'.
          "__qualname__": skill_name + "." + wrapped_type.DESCRIPTOR.full_name,
          # E.g.: 'intrinsic.solutions.skills.ai.intrinsic'.
          "__module__": module_for_generated_skill(skill_package),
          "_wrapped_type": wrapped_type,
      },
  )

  msg = wrapped_type()
  for enum_type in msg.DESCRIPTOR.enum_types:
    for value in enum_type.values:
      setattr(type_class, value.name, value.number)

  return type_class


def _gen_init_fun(
    wrapped_type: Type[message.Message],
    type_name: str,
    wrapper_classes: dict[str, Type[MessageWrapper]],
    field_doc_strings: Dict[str, str],
) -> Callable[[Any, Any], None]:
  """Generates custom __init__ class method with proper auto-completion info.

  Args:
    wrapped_type: Message to wrap.
    type_name: Type name of the object to wrap.
    wrapper_classes: Map from proto message names to corresponding message
      wrapper classes.
    field_doc_strings: dict mapping from field name to doc string comment.

  Returns:
    A function suitable to be used as __init__ function for a MessageWrapper
    derivative.
  """

  def new_init_fun(self, **kwargs) -> None:
    MessageWrapper.__init__(self)  # pytype: disable=wrong-arg-count
    self._wrapped_message = wrapped_type()  # pylint: disable=protected-access
    params_set = self._set_params(**kwargs)  # pylint: disable=protected-access
    # Arguments which are not expected parameters.
    extra_args_set = set(kwargs.keys()) - set(params_set)
    if extra_args_set:
      raise NameError(f"Unknown argument(s): {', '.join(extra_args_set)}")

  params = [
      inspect.Parameter(
          "self",
          inspect.Parameter.POSITIONAL_OR_KEYWORD,
          annotation="MessageWrapper_" + type_name,
      )
  ] + _gen_init_params(wrapped_type, wrapper_classes)
  new_init_fun.__signature__ = inspect.Signature(params)
  new_init_fun.__annotations__ = collections.OrderedDict(
      [(p.name, p.annotation) for p in params]
  )
  new_init_fun.__doc__ = _gen_init_docstring(wrapped_type, field_doc_strings)
  return new_init_fun


def _gen_init_docstring(
    wrapped_type: Type[message.Message],
    field_doc_strings: Dict[str, str],
) -> str:
  """Generates documentation string for init function.

  Args:
    wrapped_type: Message to wrap.
    field_doc_strings: Dict mapping from field name to doc string comment.

  Returns:
    Python documentation string.
  """
  param_defaults = wrapped_type()

  docstring: List[str] = [
      f"Wrapper class for {wrapped_type.DESCRIPTOR.full_name}.\n"
  ]
  message_doc_string = ""
  if param_defaults.DESCRIPTOR.full_name in field_doc_strings:
    message_doc_string = field_doc_strings[param_defaults.DESCRIPTOR.full_name]
  # Expect 80 chars width.
  is_first_line = True
  for doc_string_line in textwrap.dedent(message_doc_string).splitlines():
    wrapped_lines = textwrap.wrap(doc_string_line, 80)
    # Make sure that an empty line is wrapped to an empty line
    # and not removed. We assume that the skill author intended
    # the extra line break there unless it is the first line.
    if not wrapped_lines and is_first_line:
      is_first_line = False
      continue
    docstring += wrapped_lines

  message_fields = extract_docstring_from_message(
      param_defaults, field_doc_strings
  )
  if message_fields:
    docstring.append("\nFields:")
    message_fields.sort(
        key=lambda p: (p.has_default, p.name, p.default, p.doc_string)
    )
    for m in message_fields:
      field_name = f"{m.name}:"
      docstring.append(field_name.rjust(len(field_name) + 4))
      # Expect 80 chars width, subtract 8 for leading spaces in args string.
      for param_doc_string in m.doc_string:
        for line in textwrap.wrap(param_doc_string, 72):
          docstring.append(line.rjust(len(line) + 8))
      if m.has_default:
        default = f"Default value: {m.default}"
        docstring.append(default.rjust(len(default) + 8))
  return "\n".join(docstring)


def _gen_init_params(
    wrapped_type: Type[message.Message],
    wrapper_classes: dict[str, Type[MessageWrapper]],
) -> List[inspect.Parameter]:
  """Create argument typing information for a given message.

  Args:
    wrapped_type: Message to be wrapped.
    wrapper_classes: Map from proto message names to corresponding message
      wrapper classes.

  Returns:
    List of extracted parameters with typing information.
  """
  defaults = wrapped_type()
  param_info = extract_parameter_information_from_message(
      defaults, None, wrapper_classes
  )
  params = [p for p, _ in param_info]

  # Sort items without default arguments before the ones with defaults.
  # This is required to generate valid function signatures.
  params.sort(key=lambda f: f.default == inspect.Parameter.empty, reverse=True)
  return params


def _gen_wrapper_namespace_class(
    name: str, proto_path: str, skill_name: str, skill_package: str
) -> Type[Any]:
  """Generates a class to be used as a namespace for nested wrapper classes.

  Args:
    name: Name of the class to generate.
    proto_path: Prefix of a full proto type name corresponding to the namespace
      class to generate. E.g. 'intrinsic_proto', 'intrinsic_proto.foo' or
      'intrinsic_proto.foo.Bar' (if 'Bar' is just required as a namespace and we
      don't have a message wrapper for it).
    skill_name: Name of the parent skill.
    skill_package: Package name of the parent skill.

  Returns:
    The generated namespace class.
  """

  def init_fun(self, *args, **kwargs) -> None:
    del self, args, kwargs
    raise RuntimeError(
        f"This class ({proto_path}) serves only as a namespace and should not"
        " be instantiated."
    )

  return type(
      name,
      (),  # no base classes
      {
          "__init__": init_fun,
          "__name__": name,
          "__qualname__": skill_name + _PYTHON_PACKAGE_SEPARATOR + proto_path,
          "__module__": module_for_generated_skill(skill_package),
      },
  )


def _attach_wrapper_class(
    parent_name: str,
    relative_name: str,
    parent_class: Type[Any],
    wrapper_class: Type[MessageWrapper],
    skill_name: str,
    skill_package: str,
) -> None:
  """Attaches the given wrapper class as a nested class under a skill class.

  E.g. the wrapper class corresponding to the message 'intrinsic_proto.foo.Bar'
  will be attached as:
    skill class
      -> namespace class 'intrinsic_proto'
      -> namespace class 'foo'
      -> wrapper class 'Bar'

  Args:
    parent_name: Full name of the parent class.
    relative_name: Current path relative to parent_name under which to attach.
    parent_class: Current parent under which to attach.
    wrapper_class: Wrapper class to attach.
    skill_name: Name of the parent skill.
    skill_package: Package name of the parent skill.
  """

  if _PROTO_PACKAGE_SEPARATOR not in relative_name:
    if hasattr(parent_class, relative_name):
      raise AssertionError(
          f"Internal error: Parent class {parent_name} already has a nested"
          f" class {relative_name}. Wrong attachment order?"
      )
    setattr(parent_class, relative_name, wrapper_class)
    return

  prefix = relative_name.split(_PROTO_PACKAGE_SEPARATOR)[0]
  child_name = (
      f"{parent_name}{_PROTO_PACKAGE_SEPARATOR}{prefix}"
      if parent_name
      else prefix
  )

  if not hasattr(parent_class, prefix):
    child_class = _gen_wrapper_namespace_class(
        prefix, child_name, skill_name, skill_package
    )
    setattr(parent_class, prefix, child_class)
  else:
    # In this case, 'child_class' is a namespace class or a message wrapper
    # class that serves as a namespace for a nested proto message.
    child_class = getattr(parent_class, prefix)

  _attach_wrapper_class(
      child_name,
      relative_name.removeprefix(prefix).lstrip("."),
      child_class,
      wrapper_class,
      skill_name,
      skill_package,
  )


def update_message_class_modules(
    cls: Type[Any],
    skill_name: str,
    skill_package: str,
    enum_types: List[descriptor.EnumDescriptor],
    nested_classes: List[
        Tuple[str, Type[message.Message], descriptor.FieldDescriptor]
    ],
    field_doc_strings: Dict[str, str],
) -> dict[str, Type[MessageWrapper]]:
  """Updates given class with type aliases.

  Creates aliases (members) in the given cls for the given nested classes.

  Args:
    cls: class to modify
    skill_name: Name of the skill to correspoding to 'cls'.
    skill_package: Package name of the skill to correspoding to 'cls'.
    enum_types: Top-level enum classes whose values should be aliased to
      attributes of the message class.
    nested_classes: classes to be aliased
    field_doc_strings: dict mapping from field name to doc string comment.

  Returns:
    Map from proto message names to corresponding message wrapper classes.
  """
  for enum_type in enum_types:
    for enum_value in enum_type.values:
      value_name = enum_value.name
      if (
          hasattr(cls, value_name)
          and getattr(cls, value_name) != enum_value.number
      ):
        print(
            f"Duplicate definition of enum value {value_name}. "
            f"Enum {enum_type.full_name} is not the only one with a value "
            f"called {value_name}"
        )
      else:
        setattr(cls, value_name, enum_value.number)

  wrapper_classes: dict[str, Type[MessageWrapper]] = {}
  for _, message_type, field in nested_classes:
    if field.message_type.full_name in _MESSAGE_NAME_TO_PYTHONIC_TYPE:
      continue

    if field.message_type.full_name not in wrapper_classes:
      wrapper_class = _gen_wrapper_class(
          message_type,
          skill_name,
          skill_package,
          field_doc_strings,
      )
      wrapper_classes[field.message_type.full_name] = wrapper_class

  # The init function of a wrapper class may reference any other wrapper class
  # (proto definitions can be recursive!). So we can only generate the init
  # functions after all classes have been generated.
  for message_full_name, wrapper_class in wrapper_classes.items():
    wrapper_class.__init__ = _gen_init_fun(
        wrapper_class.wrapped_type,
        message_full_name,
        wrapper_classes,
        field_doc_strings,
    )

  # Attach message classes to skill class in sorted order to ensure that nested
  # proto message are handled correctly. E.g., 'foo.Bar' needs to be attached
  # before 'foo.Bar.Nested' so that we don't create a namespace class for
  # 'foo.Bar' when inserting 'foo.Bar.Nested'. Note that we might still create
  # 'foo.Bar' as a namespace class if the skill uses 'foo.Bar.Nested' but not
  # 'foo.Bar'.
  for message_full_name in sorted(wrapper_classes):
    wrapper_class = wrapper_classes[message_full_name]
    _attach_wrapper_class(
        "", message_full_name, cls, wrapper_class, skill_name, skill_package
    )

  # Create my_skill.<message name> shortcuts. Iterate in 'nested_classes' order
  # for backwards compatibility and also to ensure that the shortcuts are
  # deterministic in case of name collisions.
  for _, _, field in nested_classes:
    if field.message_type.full_name not in wrapper_classes:
      continue
    wrapper_class = wrapper_classes[field.message_type.full_name]
    message_name = wrapper_class.wrapped_type.DESCRIPTOR.name
    if not hasattr(cls, message_name):
      setattr(cls, message_name, wrapper_class)

  return wrapper_classes


def deconflict_param_and_resources(
    resource_slot: str,
    param_names: Container[str],
    try_suffix: str = RESOURCE_SLOT_DECONFLICT_SUFFIX,
) -> str:
  """Deconflicts resource slot name from existing parameters.

  Resource slots and parameter names are two separate namespaces in the skill
  specification. But for our API purposes, they both become parameters to the
  same function, and thus cannot be the same.

  Args:
    resource_slot: resource slot name
    param_names: container with all regular parameter names
    try_suffix: suffix to append on conflict to try deconfliction

  Returns:
    This function checks whether the resource_slot is in param_names. If it is
    not, the resource_slot is returned unmodified. If it is contained, the
    try_suffix is added. If it still is contained, an exception is raised.
    Otherwise the extended name is returned.

  Raises:
    NameError: if resource_slot as well as resource_slot+try_suffix is already
      contained in param_names
  """
  if resource_slot not in param_names:
    return resource_slot

  # We have a conflict, a skill has a resource slot and a parameter with
  # the same name (we are mixing two namespaces here). Add suffix to
  # slot name to disambiguate
  try_slot = resource_slot + try_suffix
  if try_slot in param_names:
    # Still a conflict!? Ok, out of luck, we cannot recover that one
    raise NameError(
        f"'{resource_slot}' and '{try_slot}' are both parameter "
        "names and resource slots."
    )
  return try_slot


def extract_parameter_information_from_message(
    param_defaults: message.Message,
    skill_params: Optional[skill_parameters.SkillParameters],
    wrapper_classes: dict[str, Type[MessageWrapper]],
) -> List[Tuple[inspect.Parameter, str]]:
  """Extracts signature information from message and SkillParameters.

  Args:
    param_defaults: The message filled with default parameters.
    skill_params: Utility class to inspect the skill's parameters.
    wrapper_classes: Map from proto message names to corresponding message
      wrapper classes.

  Returns:
    List of extracted parameters together with the corresponding field name.
  """
  params: List[Tuple[inspect.Parameter, str]] = []

  for field in param_defaults.DESCRIPTOR.fields:
    default_value = inspect.Parameter.empty
    if field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
      if (
          field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
          and field.message_type.GetOptions().map_entry
      ):
        field_type = dict[Union[str, int, bool], Any]
        map_field_default = getattr(param_defaults, field.name)
        value_type = field.message_type.fields_by_name["value"]
        if value_type.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
          default_value = {
              k: pythonic_field_default_value(v, value_type)
              for (k, v) in map_field_default.items()
          }
        else:
          default_value = map_field_default
      else:
        field_type = repeated_pythonic_field_type(field, wrapper_classes)
        repeated_field_default = getattr(param_defaults, field.name)
        default_value = [
            pythonic_field_default_value(value, field)
            for value in repeated_field_default
        ]
    else:
      field_type = pythonic_field_type(field, wrapper_classes)
      if skill_params and skill_params.has_default_value(field.name):
        default_value = pythonic_field_default_value(
            getattr(param_defaults, field.name), field
        )

    params.append((
        inspect.Parameter(
            field.name,
            inspect.Parameter.KEYWORD_ONLY,
            annotation=field_type,
            default=default_value,
        ),
        field.name,
    ))

  return params


def extract_docstring_from_message(
    defaults: message.Message,
    comments: Dict[str, str],
    skill_params: Optional[skill_parameters.SkillParameters] = None,
) -> List[ParameterInformation]:
  """Extracts docstring information from message and SkillParameters.

  Args:
    defaults: The message filled with default parameters.
    comments: Dict mapping from field name to doc string comment.
    skill_params: Utility class to inspect the skill's parameters.

  Returns:
    List containing a ParameterInformation object describing for each field
    whether the field has a default parameter, the field name, the default
    value and the doc string.
  """
  params: List[ParameterInformation] = []

  for field in defaults.DESCRIPTOR.fields:
    default_value = None
    have_default = False
    if field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
      if (
          field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
          and field.message_type.GetOptions().map_entry
      ):
        map_field_default = getattr(defaults, field.name)
        value_type = field.message_type.fields_by_name["value"]
        if value_type.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
          default_value = {
              k: pythonic_field_default_value(v, value_type)
              for (k, v) in sorted(map_field_default.items())
          }
        else:
          default_value = map_field_default
        if map_field_default:
          have_default = True

      else:
        repeated_field_default = getattr(defaults, field.name)
        default_value = [
            pythonic_field_default_value(value, field)
            for value in repeated_field_default
        ]
        if repeated_field_default:
          have_default = True
    elif skill_params and skill_params.has_default_value(field.name):
      have_default = True
      default_value = pythonic_field_default_value(
          getattr(defaults, field.name), field
      )

    doc_string = ""
    if field.full_name in comments:
      doc_string = comments[field.full_name]
    params.append(
        ParameterInformation(
            has_default=have_default,
            name=field.name,
            default=default_value,
            doc_string=[doc_string],
        )
    )

  return params


def wait_for_skill(
    skill_registry: skill_registry_client.SkillRegistryClient,
    skill_id: str,
    version: str = "",
    wait_duration: float = 60.0,
) -> None:
  """Polls the Skill registry until matching skill is found.

  Args:
    skill_registry: The skill registry to query.
    skill_id: Fully-qualified name of the skill to wait for.
    version: If non-empty, wait for this specific version of the skill.
    wait_duration: Time in seconds to wait before timing out.

  Raises:
    TimeoutError: If the wait_duration is exceeded and the skill still not
    available.
  """
  start_time = datetime.datetime.now()
  skill_id_version = f"{skill_id}.{version}"
  while True:
    if datetime.datetime.now() > start_time + datetime.timedelta(
        seconds=wait_duration
    ):
      raise TimeoutError(
          f"Timeout after {wait_duration}s while waiting for skill"
          f" {skill_id} to become available."
      )

    try:
      skill = skill_registry.get_skill(skill_id)
      if not version or skill_id_version == skill.id_version:
        break

    except grpc.RpcError:
      time.sleep(1)
