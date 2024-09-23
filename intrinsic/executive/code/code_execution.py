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
import grpc
from intrinsic.geometry.service import geometry_service_pb2_grpc
from intrinsic.skills.internal import basic_compute_context_impl
from intrinsic.skills.python import basic_compute_context
from intrinsic.world.proto import object_world_service_pb2_grpc
from intrinsic.world.python import object_world_client


# Converts "foo/bar/baz.proto" -> "foo.bar.baz_pb2"
def _to_proto_module(proto_filename: str) -> str:
  proto_module = proto_filename.replace(".proto", "_pb2").replace("/", ".")
  return proto_module


# Converts "foo.bar.baz_pb2" -> "foo/bar/baz.proto"
def _to_proto_filename(proto_module: str) -> str:
  proto_filename = proto_module
  return proto_filename.replace(".", "/").replace("_pb2", ".proto")


def _proto_full_name(pkg: str, symbol_name: str) -> str:
  """Creates a full name for a proto symbol in a package.

  Args:
    pkg: The proto package the symbol is in (e.g., my_proto_pkg)
    symbol_name: The name of the proto symbol (e.g., TestMessage)

  Returns:
    Full name of the proto symbol (e.g., my_proto_pkg.TestMessage)
  """
  if not pkg:
    return symbol_name
  return pkg + "." + symbol_name


def _create_symbol_to_file(
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
) -> dict[str, str]:
  """Computes a map from a proto symbol to its file name in the default pool.

  The input file descriptor set is only used to define the symbols to look at,
  but not to determine in which file they are defined. The function looks for
  file names in the default pool.

  Thus only proto symbols that are already in the default pool will be recorded.
  It is not an error if a symbol in file_descriptor_set is not in the default
  pool.

  Args:
    file_descriptor_set: A FileDescriptorSet, where every known symbol will be
      recorded in the map

  Returns:
    A map from the full name of a proto symbol to the file it is in the default
    pool
  """
  symbol_to_file: dict[str, str] = {}
  for file in file_descriptor_set.file:
    for get_symbol_field in [
        lambda file_descriptor: file_descriptor.message_type,
        lambda file_descriptor: file_descriptor.enum_type,
        lambda file_descriptor: file_descriptor.service,
        lambda file_descriptor: file_descriptor.extension,
    ]:
      for symbol in get_symbol_field(file):
        # for message_type in file.message_type:
        full_name = _proto_full_name(file.package, symbol.name)
        try:
          default_file_descriptor = (
              descriptor_pool.Default().FindFileContainingSymbol(full_name)
          )
          default_file_name = default_file_descriptor.name
          symbol_to_file[full_name] = default_file_name
        except KeyError:
          # Symbol not in default pool. This is OK as the purpose of the
          # function is to find matching files in the default pool and then
          # later make sure these are compatible. If there is no entry in the
          # default pool, there can be no incompatibility.
          continue
  return symbol_to_file


def _create_default_paths(
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    symbol_to_file: dict[str, str],
) -> dict[str, str]:
  """Maps file names in file_descriptor_set to file names in the default pool.

  Args:
    file_descriptor_set: The file_descriptor_set to compute the path map for.
    symbol_to_file: A mapping from proto symbols to default pool file names

  Returns:
    A mapping from file names in file_descriptor_set to file names in the
    default pool.
  """
  # Go through each message/proto symbol in each file of the new file descriptor
  # set and record in which file that symbol is defined in the default pool
  # given by symbol_to_file. If there is no entry the respective file descriptor
  # is new (e.g., the parameter message) and its default path is its own file
  # path.
  path_to_default_path: dict[str, str] = {}
  for file in file_descriptor_set.file:
    default_path_for_file = ""
    for get_symbol_field in [
        lambda file_descriptor: file_descriptor.message_type,
        lambda file_descriptor: file_descriptor.enum_type,
        lambda file_descriptor: file_descriptor.service,
        lambda file_descriptor: file_descriptor.extension,
    ]:
      for symbol in get_symbol_field(file):
        # for message_type in file.message_type:
        full_name = _proto_full_name(file.package, symbol.name)
        if full_name in symbol_to_file:
          # Assuming if there is a message with the same full name, it is
          # actually the same message.
          # Note that this will fail horribly if this assumption is violated and
          # a message with the same name has different content.
          path = symbol_to_file[full_name]
          if not default_path_for_file:
            default_path_for_file = path
          if default_path_for_file != path:
            raise TypeError(
                "Found inconsistent path in new file descriptor set in file"
                f" {file.name}. The message {full_name} is contained in"
                f" {path} in the default pool, but another message in"
                f" {file.name} in the default pool was in"
                f" {default_path_for_file}"
            )
    # fallback case if this is a new file descriptor
    if not default_path_for_file:
      default_path_for_file = file.name
    path_to_default_path[file.name] = default_path_for_file
    # Also register the default path as that obviously matches. This covers the
    # cases, where during recursive calls the file descriptor set already has
    # been adapted to default paths.
    path_to_default_path[default_path_for_file] = default_path_for_file
  return path_to_default_path


def _create_compatible_file_descriptor_set(
    new_file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    path_to_default_path: dict[str, str],
) -> descriptor_pb2.FileDescriptorSet:
  """Makes the passed FileDescriptorSet compatible with the default pool.

  Args:
    new_file_descriptor_set: A file descriptor set with paths reference in
      path_to_default_path
    path_to_default_path: Mapping from paths in new_file_descriptor_set to paths
      in file descriptors in the default pool

  Returns:
    A new file descriptor set with file names and dependencies adapted to have
    the same file names as in the default pool.
  """
  # Update the new file descriptor set to a compatible one.
  # Replace each file name and each dependency by the mapping in
  # path_to_default_path of what it would be in the default pool.
  # Note: This is the same logic as in
  # ProtobufManager::CreateCompatibleFileDescriptorSet.
  compatible_file_descriptor_set = descriptor_pb2.FileDescriptorSet()
  compatible_file_descriptor_set.CopyFrom(new_file_descriptor_set)
  for file in compatible_file_descriptor_set.file:
    if file.name != path_to_default_path[file.name]:
      print(
          f"Adapted default file path for {file.name} to"
          f" {path_to_default_path[file.name]}"
      )
    file.name = path_to_default_path[file.name]
    for i, dep in enumerate(file.dependency):
      if dep != path_to_default_path[dep]:
        print(
            f"Adapted default dependency file path for {dep} to"
            f" {path_to_default_path[dep]}"
        )
        file.dependency[i] = path_to_default_path[dep]

  return compatible_file_descriptor_set


def import_from_file_descriptor_set(
    module_name: str,
    file_descriptor_set: descriptor_pb2.FileDescriptorSet,
    symbol_to_file: dict[str, str] | None = None,
    path_to_default_path: dict[str, str] | None = None,
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

  It is OK to leave symbol_to_file and path_to_default_path empty for the
  initial call on the input file_descriptor_set. In that case these will be
  created.

  Args:
    module_name: The name of the proto module to import. Must end with "_pb2".
    file_descriptor_set: The file descriptor set to import missing modules from.
    symbol_to_file: A map from proto symbol full name to the file name it is in
    path_to_default_path: Mapping from a file name to the respective file in the
      default pool

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

  if symbol_to_file is None:
    symbol_to_file = _create_symbol_to_file(file_descriptor_set)
  if path_to_default_path is None:
    path_to_default_path = _create_default_paths(
        file_descriptor_set, symbol_to_file
    )

  # Before adding this descriptor set: Modify all paths (file names and
  # dependencies) if the same symbols are present in the default pool, but under
  # another file name. If it is, use the file name of the proto file in the
  # default pool. This assumes that the definitions are compatible.
  file_descriptor_set = _create_compatible_file_descriptor_set(
      file_descriptor_set, path_to_default_path
  )

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
        symbol_to_file,
        path_to_default_path,
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
      full_message_name = _proto_full_name(file.package, message_type.name)
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


def create_compute_context(
    world_id: str,
    world_service_address: str,
    geometry_service_address: str,
) -> basic_compute_context.BasicComputeContext:
  """Creates a BasicComputeContext.

  Args:
    world_id: The id of the world.
    world_service_address: The address of the world service.
    geometry_service_address: The address of the geometry service.

  Returns:
    The created BasicComputeContext.
  """
  world_stub = object_world_service_pb2_grpc.ObjectWorldServiceStub(
      grpc.insecure_channel(world_service_address)
  )
  geometry_stub = geometry_service_pb2_grpc.GeometryServiceStub(
      grpc.insecure_channel(geometry_service_address)
  )
  return basic_compute_context_impl.BasicComputeContextImpl(
      object_world_client.ObjectWorldClient(world_id, world_stub, geometry_stub)
  )
