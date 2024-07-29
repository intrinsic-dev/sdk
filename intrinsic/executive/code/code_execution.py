# Copyright 2023 Intrinsic Innovation LLC

"""Utilities for executing code from the code execution service."""

import importlib
import sys
import types

from google.protobuf import any_pb2
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import message
from google.protobuf.internal import builder


# Converts "foo/bar/baz.proto" -> "foo.bar.baz_pb2"
def _to_proto_module(proto_filename: str) -> str:
  proto_module = proto_filename.replace(".proto", "_pb2").replace("/", ".")
  return proto_module


# Converts "foo.bar.baz_pb2" -> "foo/bar/baz.proto"
def _to_proto_filename(proto_module: str) -> str:
  proto_filename = proto_module
  return proto_filename.replace(".", "/").replace("_pb2", ".proto")


def import_from_file_descriptor_set(
    module_name: str,
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
) -> types.ModuleType:
  """Imports a proto module from the given file descriptor set.

  First tries a regular import of the proto module with the given name and if no
  corresponding module file exists, imports it "from the corresponding file in
  the given file descriptor set". Dependencies of the imported module
  are handled recursively. The message classes and other types which are
  provided by the returned module are associated with the default descriptor
  pool, just like for a regularly imported proto module.

  Conceptually, the following two are equivalent:
   - my_proto_pb2 = import_from_file_descriptor_set(
         "foo.bar_pb2",
         file_descriptor_set, # containing "foo/bar.proto"
     )
   - "protoc --python_out . foo/bar.proto" followed by:
     from foo import bar_pb2

  This function blindly assumes that the file descriptor set is compatible with
  the current Python environment. E.g., assume that the file descriptor set
  contains "a.proto" and "b.proto" where "a.proto" depends on "b.proto", and
  "b_pb2.py" is also available in the current Python environment. Then "b.proto"
  from the file descriptor set and "b_pb2.py" from the current Python
  environment must be equivalent or else things can break when importing "a_pb2"
  from the file descriptor set.

  Args:
    module_name: The name of the proto module to import. Must end with "_pb2".
    file_descriptor_set: The file descriptor set to import missing modules from.

  Returns:
    The imported module.
  """
  if not module_name.endswith("_pb2"):
    raise ValueError(f"Module name must end with _pb2, but got {module_name}")

  # First try a regular import (from the sys.modules cache or "from file"). Note
  # that if this function is called a second time with the same arguments, we
  # will get a cache hit here.
  try:
    module = importlib.import_module(module_name)
    print("Imported", module_name, "from file or cache")
    return module
  except ModuleNotFoundError:
    # Regular import failed, import from the file descriptor set.
    pass

  file_name = _to_proto_filename(module_name)

  try:
    file_descriptor_proto = next(
        file for file in file_descriptor_set.file if file.name == file_name
    )
  except StopIteration as e:
    raise ValueError(
        f"Could not find file {file_name} in file descriptor set"
    ) from e

  # Import all proto module dependencies (just like in a generated "*_pb2.py"
  # file).
  for dependency_file_name in file_descriptor_proto.dependency:
    import_from_file_descriptor_set(
        _to_proto_module(dependency_file_name),
        file_descriptor_set,
    )

  # Add file descriptor to the default descriptor pool (just like in a generated
  # "*_pb2.py" file).
  descriptor_pool.Default().Add(file_descriptor_proto)
  file_descriptor = descriptor_pool.Default().FindFileByName(
      file_descriptor_proto.name
  )

  # Generate message classes etc. (just like in a generated "*_pb2.py" file).
  module = types.ModuleType(name=module_name)
  setattr(module, "DESCRIPTOR", file_descriptor)
  builder.BuildMessageAndEnumDescriptors(file_descriptor, module.__dict__)
  builder.BuildTopDescriptorsAndMessages(
      file_descriptor, module.__name__, module.__dict__
  )

  # Add the module to the sys.modules cache. Technically, we would also need to
  # load and add all parent modules here (e.g., "import foo.bar" loads "foo" and
  # then "foo.bar"). But we avoid this additional complexity as long as we don't
  # strictly need it.
  sys.modules[module.__name__] = module

  return module


def _find_module_containing_message(
    message_full_name: str,
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
) -> str:
  """Finds the proto module containing the given message.

  Finds the proto module containing the given message in the given file
  descriptor set. Assumes that the message is a *top-level* message in some file
  in the file descriptor set.

  Args:
    message_full_name: The full name of the message to find.
    file_descriptor_set: The file descriptor set in which to search for the
      message.

  Returns:
    The name of the proto module containing the given message.
  """
  for file in file_descriptor_set.file:
    for message_type in file.message_type:
      full_message_name = (
          file.package + "." if file.package else ""
      ) + message_type.name
      if full_message_name == message_full_name:
        return _to_proto_module(file.name)

  raise ValueError(
      f"Could not find params message {message_full_name} in file"
      " descriptor set"
  )


def unpack_params_message(
    params_any: any_pb2.Any,
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
) -> message.Message:
  """Unpacks the given params Any proto.

  Unpacks the given params Any proto into a message of the proper type (as
  indicated by the Any proto's type_url).

  Args:
    params_any: The Any proto to unpack.
    file_descriptor_set: The file descriptor set containing the file defining
      the params message and all its dependencies.

  Returns:
    The unpacked params message.
  """
  params_full_message_name = params_any.type_url.split("/")[-1]
  params_module_name = _find_module_containing_message(
      params_full_message_name, file_descriptor_set
  )
  params_message_module = import_from_file_descriptor_set(
      params_module_name, file_descriptor_set
  )
  message_name = params_any.type_url.split(".")[-1]
  message_class = getattr(params_message_module, message_name)

  params = message_class()
  params_any.Unpack(params)
  return params


def serialize_return_value_message(
    return_value: message.Message | None,
    return_value_message_full_name: str,
) -> bytes | None:
  """Serializes the given return value message as an Any proto.

  Also performs some basic sanity checks on the return value and its message
  type. For convenience, this function will return None if the given return
  value is None.

  Args:
    return_value: The return value message to pack. Must be a proto message of
      the type indicated by return_value_message_full_name.
    return_value_message_full_name: The expected full name of the proto message
      type of the return value.

  Returns:
    The return value message packed into an Any proto and then serialized.
  """
  if return_value is None:
    return None

  if not isinstance(return_value, message.Message):
    raise ValueError("returned value is not a proto message")
  if return_value.DESCRIPTOR.full_name != return_value_message_full_name:
    raise ValueError(
        "returned value is a proto message with the wrong type (got"
        f" {return_value.DESCRIPTOR.full_name}, expected"
        f" {return_value_message_full_name})"
    )

  return_value_any = any_pb2.Any()
  return_value_any.Pack(return_value)
  return return_value_any.SerializeToString()
