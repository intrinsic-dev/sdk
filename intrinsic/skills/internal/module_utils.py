# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Utility functions for dynamically loading a Python module."""

import importlib
import inspect
import typing


def build_class(module: typing.Text, class_name: typing.Text) -> typing.Any:
  """Given the name of the module returns an object corresponding to the name.

  Args:
    module: The package name which includes a number of desired classes.
    class_name: The name of the class to be instantiated.

  Returns:
    An object corresponding to the class.
  """
  module = importlib.import_module(module)
  return getattr(module, class_name)


def get_subclasses_in_modules(
    module_names: typing.List[typing.Text], module_baseclass: typing.Any
) -> typing.List[typing.Any]:
  """Finds all of the module subclass objects in a list of modules.

  The library that uses this function must have the desired modules in its
  build dependencies. The module_name is specified the same way as static
  modules are specified. e.g.
  intrinsic.skills.test_data.sample_skills

  Args:
    module_names: The name of the module, string.
    module_baseclass: The baseclass that the subclass is derived from.

  Returns:
    A list of Subclass objects.
  """
  module_subclasses = []

  for module_name in module_names:
    my_module = importlib.import_module(module_name)
    for _, obj in inspect.getmembers(my_module):
      if inspect.isclass(obj) and issubclass(obj, module_baseclass):
        module_subclasses.append(obj)
  return module_subclasses


def get_subclass_instances_in_modules(
    module_names: typing.List[typing.Text], module_baseclass: typing.Any
) -> typing.List[typing.Any]:
  """Returns instances of all modules in a list of modules.

  The library that uses this function must have the desired modules in its
  build dependencies. The module_name is specified the same way as static
  modules are specified. e.g.
  intrinsic.skills.test_data.sample_skills

  Args:
    module_names: The names of the modules, string.
    module_baseclass: The baseclass that the subclass is derived from.

  Returns:
    A list of Module objects.
  """
  module_subclasses = get_subclasses_in_modules(
      module_names=module_names, module_baseclass=module_baseclass
  )
  return list(map(lambda x: x(), module_subclasses))
