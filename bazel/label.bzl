# Copyright 2023 Intrinsic Innovation LLC

"""Parse and create labels."""

def parse_label(label):
    """Parse a label into (repository, package, name).

    Args:
      label: string in relative or absolute form.

    Returns:
      Tuple of strings: repository, package, relative_name

    Raises:
      ValueError for malformed label (does not do an exhaustive validation)
    """
    label = absolute_label(label)
    repository = label.split("//", 1)[0][1:]
    label = label.split("//", 1)[1]
    pkg, target = label.split(":")
    return repository, pkg, target

def absolute_label(
        label,
        package_name = None,
        repository_name = None):
    """Expand a label to be of the full form @repo//package:foo.

    absolute_label("@foo//bar:baz") = "@foo//bar:baz"
    absolute_label("//bar:baz")     = "@<current_repo>//bar:baz"
    absolute_label("//bar:bar")     = "@<current_repo>//bar:bar"
    absolute_label("@foo//bar")     = "@foo//bar:bar"
    absolute_label("//bar")         = "@<current_repo>//bar:bar"
    absolute_label(":baz")          = "@<current_repo>//current_package:baz"
    absolute_label("baz")           = "@<current_repo>//current_package:baz"

    The form is "canonical" - that is, every label with the same meaning will
    generate a single absolute label form.

    Args:
      label: string in absolute or relative form.
      package_name: Optional. The name of the package that should be used if the |label| is
          relative. If left empty, defaults to `native.package_name()` which is only
          resolvable during the analysis phase.
      repository_name: Optional. The name of the repository that should be used if the |repository| is
          not declared. If left empty, defaults to `native.repository_name()` which is only
          resolvable during the analysis phase.

    Returns:
      Absolute form of the label as a string.

    Raises:
      ValueError for malformed label (does not do an exhaustive validation)
    """
    if label.startswith("@"):
        if ":" in label:
            return label
        return "%s:%s" % (label, label.rsplit("/", 1)[-1])
    repository_name = native.repository_name() if not repository_name else repository_name
    if label.startswith("//"):
        label = "%s%s" % (repository_name, label)
        if ":" in label:
            return label
        return "%s:%s" % (label, label.rsplit("/", 1)[-1])
    package_name = native.package_name() if not package_name else package_name
    if label.startswith(":"):
        return "%s//%s%s" % (repository_name, package_name, label)
    return "%s//%s:%s" % (repository_name, package_name, label)
