# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provide error handling utils for skill services/clients.

Skill service rpcs use a particular formatting of grpc.Status errors to pass
additional metadata. The calls below help translate to and from absl::Status.

See error_utils.h for more information.
"""

from google.rpc import status_pb2
import grpc
from intrinsic.skills.proto import error_pb2
from pybind11_abseil import status

# This key is taken from the grpc implementation and generates special behavior
# when sending it as trailing metadata.
_GRPC_DETAILS_METADATA_KEY = 'grpc-status-details-bin'


def make_grpc_status_with_error_info(
    code: status.StatusCode,
    message: str,
    skill_error_info: error_pb2.SkillErrorInfo,
) -> grpc.Status:
  """Generates a grpc status from the given data.

  This function does some special packing of the information in a way that grpc
  recognizes, ensuring that all the data shows up on the other side of the call.

  Args:
    code: status code as integer or equivalent
    message: human readable error message
    skill_error_info: information from the skill framework side

  Returns:
    a grpc.Status
  """
  my_status = status_pb2.Status(code=code.value, message=message)
  my_status.details.add().Pack(skill_error_info)

  grpc_code = grpc.StatusCode.UNKNOWN
  for some_code in grpc.StatusCode:
    if some_code.value[0] == code.value:
      grpc_code = some_code
  grpc_status = grpc.Status()
  grpc_status.code = grpc_code
  grpc_status.details = message
  grpc_status.trailing_metadata = (
      (_GRPC_DETAILS_METADATA_KEY, my_status.SerializeToString()),
  )
  return grpc_status
