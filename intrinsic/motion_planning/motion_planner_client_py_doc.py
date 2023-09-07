# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""A dummy file that is only used by the Python API documentation generator.

The `motion_planner_client_py_doc` target is required because building a
library is a no-op if not used by any binary in Bazel. This file serves as the
main file of this dummy target and doesn't need any content.

See intrinsic/external_docs/tools/generate_python_api_docs.py
"""
from intrinsic.motion_planning import motion_planner_client  # pylint: disable=unused-import
