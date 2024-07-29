# Copyright 2023 Intrinsic Innovation LLC

"""Utilities for executing code from the code execution service."""

import importlib
import sys
import types

from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
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
