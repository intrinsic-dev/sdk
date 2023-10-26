# Copyright 2023 Intrinsic Innovation LLC

"""Helper decorators for Python files."""

def overrides(interface):
  """Overrides decorator to annotate method overrides parent's."""

  def overrider(method):
    assert hasattr(
        interface, method.__name__
    ), 'method %s declared to be @overrides is not defined in %s' % (
        method.__name__,
        interface.__name__,
    )
    return method

  return overrider
