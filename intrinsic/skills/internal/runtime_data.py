# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Classes used by the skill service at run time.

This file contains data types that are used by the skill service at runtime
to provide our internal framework access to metadata about skills. Classes
defined here should not be used in user-facing contexts.
"""

import dataclasses
import datetime
from typing import List, Mapping, Optional, Sequence

from google.protobuf import any_pb2
from google.protobuf import descriptor as proto_descriptor
from intrinsic.assets import id_utils
from intrinsic.skills.proto import equipment_pb2
from intrinsic.skills.proto import skill_service_config_pb2
from intrinsic.skills.proto import skills_pb2
from intrinsic.skills.python import skill_interface as skl


@dataclasses.dataclass(frozen=True)
class ParameterData:
  """Parameter data that are required by the skill service at runtime.

  Attributes:
   descriptor: The parameter descriptor.
   default_value: The default value of the parameter (optional).
  """

  descriptor: proto_descriptor.Descriptor
  default_value: any_pb2.Any | None = None


@dataclasses.dataclass(frozen=True)
class ReturnTypeData:
  """Return type data that are required by the skill service at runtime.

  Attributes:
    descriptor: The return type data descriptor (optional).
  """

  descriptor: proto_descriptor.Descriptor | None = None


@dataclasses.dataclass(frozen=True)
class ExecutionOptions:
  """Execution options for a skill that are relevant to the skill services.

  Attributes:
    supports_cancellation: True, if the skill supports cancellation.
    cancellation_ready_timeout: The amount of time the skill has to prepare for
      cancellation.
  """

  supports_cancellation: bool = False
  cancellation_ready_timeout: datetime.timedelta = datetime.timedelta(
      seconds=30
  )


@dataclasses.dataclass(frozen=True)
class ResourceData:
  """Data about resources for a skill relevant to the skill service.

  Attributes:
    required_resources: Mapping of resources to run the skill.
  """

  required_resources: Mapping[str, equipment_pb2.EquipmentSelector]


@dataclasses.dataclass(frozen=True)
class SkillRuntimeData:
  """Data about skills that are relevant to the skills services.

  Attributes:
    parameter_data: The parameter data.
    return_type_data: The return data.
    execution_options: The execution options.
    resource_data: The resource data.
    skill_id: The skill id.
  """

  parameter_data: ParameterData
  return_type_data: ReturnTypeData
  execution_options: ExecutionOptions
  resource_data: ResourceData
  skill_id: str


def get_runtime_data_from(
    skill_service_config: skill_service_config_pb2.SkillServiceConfig,
    parameter_descriptor: proto_descriptor.Descriptor,
    return_type_descriptor: Optional[proto_descriptor.Descriptor],
) -> SkillRuntimeData:
  # pyformat: disable
  """Constructs RuntimeData from the given skill service config & descriptors.

  This applies a default `cancellation_ready_timeout` of 30 seconds to the
  execution options if no timeout is specified, in order to match the behavior
  of the skill signature.

  Args:
    skill_service_config: The skill service config.
    parameter_descriptor: The parameter descriptor.
    return_type_descriptor: The return type descriptor (optional).

  Returns:
    Constructed SkillRuntimeData from given args.
  """
  # pyformat: enable

  if skill_service_config.execution_service_options.HasField(
      'cancellation_ready_timeout'
  ):
    duration_proto = (
        skill_service_config.execution_service_options.cancellation_ready_timeout
    )
    timeout = datetime.timedelta(
        seconds=duration_proto.seconds,
        milliseconds=(duration_proto.nanos / 1e-6),
    )
    execute_opts = ExecutionOptions(
        skill_service_config.skill_description.execution_options.supports_cancellation,
        timeout,
    )
  else:
    execute_opts = ExecutionOptions(
        skill_service_config.skill_description.execution_options.supports_cancellation
    )

  resource_data = dict(
      skill_service_config.skill_description.equipment_selectors
  )

  if skill_service_config.skill_description.parameter_description.HasField(
      'default_value'
  ):
    default_value = (
        skill_service_config.skill_description.parameter_description.default_value
    )
  else:
    default_value = None

  return SkillRuntimeData(
      parameter_data=ParameterData(
          descriptor=parameter_descriptor,
          default_value=default_value,
      ),
      return_type_data=ReturnTypeData(return_type_descriptor),
      execution_options=execute_opts,
      resource_data=ResourceData(resource_data),
      skill_id=skill_service_config.skill_description.id,
  )


def get_runtime_data_from_signature(
    skill_signature: skl.Skill,
) -> SkillRuntimeData:
  """Constructs SkillRuntimeData from the given skill.

  Args:
    skill_signature: The skill.

  Returns:
    The constructed SkillRuntimeData from the given skill.
  """
  sig_id = id_utils.id_from(skill_signature.package(), skill_signature.name())

  if skill_signature.default_parameters() is None:
    param_data = ParameterData(
        descriptor=skill_signature.get_parameter_descriptor(),
    )
  else:
    default_value = any_pb2.Any()
    default_value.Pack(skill_signature.default_parameters())
    param_data = ParameterData(
        descriptor=skill_signature.get_parameter_descriptor(),
        default_value=default_value,
    )

  return_type_data = ReturnTypeData(
      skill_signature.get_return_value_descriptor()
  )
  execution_opts = ExecutionOptions(
      supports_cancellation=skill_signature.supports_cancellation(),
      cancellation_ready_timeout=datetime.timedelta(
          seconds=skill_signature.get_ready_for_cancellation_timeout()
      ),
  )

  return SkillRuntimeData(
      parameter_data=param_data,
      return_type_data=return_type_data,
      execution_options=execution_opts,
      resource_data=ResourceData(skill_signature.required_equipment()),
      skill_id=sig_id,
  )
