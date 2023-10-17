# Copyright 2023 Intrinsic Innovation LLC

# Configure Gazelle to get importpath-to-repository mappings from
# bazel/go_deps.bzl. This file needs to be referenced in our call to
# gazelle_dependencies() (see //bazel/deps_1.bzl).
#
# Note that, currently, this file must reside at the workspace root folder due
# to a path resolution bug in the 'gazelle:repository_macro' directive.
# Otherwise we could move it to //bazel or even inline it into a .bzl file in
# //bazel.

# gazelle:repository_macro bazel/go_deps.bzl%go_dependencies
