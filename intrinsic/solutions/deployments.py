# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Entry point of the Intrinsic solution building libraries.

## Usage example

```
from intrinsic.solutions import deployments

solution = deployments.connect(...)
skills = solution.skills
executive = solution.executive

throw_ball = skills.throw_ball(...)
executive.run(throw_ball)
```
"""

import enum
import inspect
import os
from typing import Any, Dict, Optional, Union
import warnings

from google.protobuf import empty_pb2
import grpc
from intrinsic.frontend.cloud.api import solutiondiscovery_api_pb2
from intrinsic.frontend.cloud.api import solutiondiscovery_api_pb2_grpc
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2
from intrinsic.kubernetes.workcell_spec.proto import installer_pb2_grpc
from intrinsic.skills.client import skill_registry_client
from intrinsic.solutions import dialerutil
from intrinsic.solutions import equipment as equipment_mod
from intrinsic.solutions import equipment_registry as equipment_registry_mod
from intrinsic.solutions import error_processing
from intrinsic.solutions import errors as solution_errors
from intrinsic.solutions import execution
from intrinsic.solutions import ipython
from intrinsic.solutions import pose_estimation
from intrinsic.solutions import providers
from intrinsic.solutions import simulation
from intrinsic.solutions import skills as skills_mod
from intrinsic.solutions import structured_logging
from intrinsic.solutions import userconfig
from intrinsic.solutions import worlds
from intrinsic.util.grpc import error_handling


_DEFAULT_HOSTPORT = "localhost:17080"
_XFA_BOX_ADDRESS_ENVIRONMENT_VAR = "XFA_BOX_ADDRESS"
_GRPC_OPTIONS = [
    # Remove limit on message size for e.g. images.
    ("grpc.max_receive_message_length", -1),
    ("grpc.max_send_message_length", -1),
]

# If an app is missing any of those services, the connect() method will raise an
# error.
_REQUIRED_BACKENDS = [
    "executive",
    "resource-registry",
    "skill-registry",
    "logger",
]

_CSS_FAILURE_STYLE = (
    "color: #ab0000; font-family: monospace; font-weight: bold; "
    "padding-left: var(--jp-code-padding);"
)

_WORLD_ID = "world"


class Solution:
  """Wraps a connection to a deployed solution."""

  class HealthStatus(enum.Enum):
    """Health status of the solution's backend."""

    UNKNOWN = 0
    # Ready to receive requests.
    HEALTHY = 1
    # Not ready to receive requests, but should fix itself.
    PENDING = 2
    # Non-recoverable error.
    ERROR = 3

  def __init__(
      self,
      grpc_channel: grpc.Channel,
      is_simulated: bool,
      executive: execution.Executive,
      skill_registry: skill_registry_client.SkillRegistryClient,
      equipment_registry: equipment_registry_mod.EquipmentRegistry,
      object_world: worlds.ObjectWorld,
      simulator: Optional[simulation.Simulation],
      structured_logs: structured_logging.StructuredLogs,
      errors: error_processing.ErrorsLoader,
      pose_estimators: Optional[pose_estimation.PoseEstimators],
      installer: installer_pb2_grpc.InstallerServiceStub,
  ):
    self.grpc_channel: grpc.Channel = grpc_channel
    self.is_simulated: bool = is_simulated

    self.executive: execution.Executive = executive
    self._skill_registry: skill_registry_client.SkillRegistryClient = (
        skill_registry
    )
    self._equipment_registry: equipment_registry_mod.EquipmentRegistry = (
        equipment_registry
    )
    self.equipment: equipment_mod.Equipment = equipment_mod.Equipment(
        self._equipment_registry
    )

    self.world: worlds.ObjectWorld = object_world
    self.simulator: Optional[simulation.Simulation] = simulator
    self._installer_service_stub = installer

    self.skills: providers.SkillProvider = skills_mod.Skills(
        self._skill_registry,
        self._equipment_registry,
    )
    self.structured_logs: structured_logging.StructuredLogs = structured_logs
    self.pose_estimators: Optional[pose_estimation.PoseEstimators] = (
        pose_estimators
    )
    self.errors: error_processing.ErrorsLoader = errors
  @classmethod
  def for_channel(
      cls,
      grpc_channel: grpc.Channel,
      *,
      options: Optional[Dict[str, Any]] = None,
  ) -> "Solution":
    """Creates a Solution for the given channel and options.

    Args:
      grpc_channel: gRPC channel to the cluster which hosts the deployed
        solution.
      options: An optional Dict[str, Any] containing additional options. See
        'deployments.connect()' for available values.

    Returns:
      A fully initialized Workcell instance.
    """

    print("Connecting to deployed solution...")

    if options is None:
      options = {}

    installer_stub = installer_pb2_grpc.InstallerServiceStub(grpc_channel)
    try:
      solution_status = _get_solution_status_with_retry(installer_stub)
    except solution_errors.BackendNoWorkcellError as e:
      ipython.display_html_or_print_msg(
          f'<span style="{_CSS_FAILURE_STYLE}">{str(e)}</span>', str(e)
      )
      raise

    # Note that the ports of the services in the 'solution_status' are
    # irrelevant, as we use the Ingress by default.
    backend_names = [s.name for s in solution_status.services]

    missing = list(filter(lambda x: x not in backend_names, _REQUIRED_BACKENDS))

    if missing:
      raise solution_errors.NotFoundError(
          "n\nMissing backend.\nRequired backends: {}\nExisting backends: {}"
          "\nMissing: {}".format(
              ", ".join(_REQUIRED_BACKENDS),
              ", ".join(backend_names),
              missing,
          )
      )

    # Optional backends.
    simulator = None
    if solution_status.simulated:
      simulator = simulation.Simulation.connect(grpc_channel)

    # Required backends. (see _REQUIRED_BACKENDS)
    structured_logs = structured_logging.StructuredLogs.connect(grpc_channel)
    error_loader = error_processing.ErrorsLoader(
        structured_logs, installer_stub
    )
    executive = execution.Executive.connect(
        grpc_channel, error_loader, simulator
    )
    skill_registry = skill_registry_client.SkillRegistryClient.connect(
        grpc_channel
    )
    equipment_registry = equipment_registry_mod.EquipmentRegistry.connect(
        grpc_channel
    )

    object_world = worlds.ObjectWorld.connect(_WORLD_ID, grpc_channel)

    pose_estimators = None
    if "perception" in backend_names:
      pose_estimators = pose_estimation.PoseEstimators(
          grpc_channel, structured_logs
      )

    print(
        f'Connected successfully to "{solution_status.display_name}'
        f'({solution_status.version})" at "{solution_status.workcell_name}".'
    )
    return cls(
        grpc_channel,
        solution_status.simulated,
        executive,
        skill_registry,
        equipment_registry,
        object_world,
        simulator,
        structured_logs,
        error_loader,
        pose_estimators,
        installer_stub,
    )

  def get_health_status(self) -> "HealthStatus":
    """Returns the health status of the solution backend.

    Can be called before or after connecting to the deployed solution.

    Returns:
      Health status of solution backend
    """
    status = self._installer_service_stub.GetInstalledSpec(
        empty_pb2.Empty()
    ).status
    if status == installer_pb2.GetInstalledSpecResponse.HEALTHY:
      return self.HealthStatus.HEALTHY
    if status == installer_pb2.GetInstalledSpecResponse.PENDING:
      return self.HealthStatus.PENDING
    if status == installer_pb2.GetInstalledSpecResponse.ERROR:
      return self.HealthStatus.ERROR
    return self.HealthStatus.UNKNOWN

  def skills_overview(
      self,
      with_signatures: bool = False,
      with_type_annotations: bool = False,
      shorten_type_annotations: bool = False,
      with_doc: bool = False,
  ) -> None:
    """Prints an overview of the registered skills.

    Args:
      with_signatures: Include signatures for skill construction.
      with_type_annotations: Include type annotations and not just the parameter
        name.
      shorten_type_annotations: Removes path prefixes from the signature to
        shorten lengthy types.
      with_doc: Also print out docstring for each skill.
    """

    def build_signature(
        skill, with_type_annotations: bool, shorten_type_annotations: bool
    ) -> str:
      """Build a signature for skill, optionally including type annotations.

      Args:
        skill: The skill to build the signature for.
        with_type_annotations: Include type annotations and not just the
          parameter name.
        shorten_type_annotations: Removes 'google3.googlex.intrinsic.' from the
          signature to shoren lengthy types.

      Returns:
        The skill signature.
      """
      signature = inspect.signature(skill)
      parameters = []
      for k, v in signature.parameters.items():
        if not with_type_annotations:
          parameters.append(k)
          continue
        param = str(v)
        if shorten_type_annotations:
          param = param.replace("google3.googlex.intrinsic.", "")
        parameters.append(param)
      return ", ".join(parameters)

    skill_names = dir(self.skills)
    for skill_name in skill_names:
      skill = getattr(self.skills, skill_name)
      if with_signatures:
        signature_str = build_signature(
            skill, with_type_annotations, shorten_type_annotations
        )
        print(f"{skill_name}({signature_str})")
      else:
        print(skill_name)
      if with_doc:
        print(f"\n{inspect.getdoc(skill)}\n")

  def update_skills(self) -> None:
    self.skills.update()


def connect(
    grpc_channel_or_hostport: Optional[Union[grpc.Channel, str]] = None,
    *,
    grpc_channel: Optional[grpc.Channel] = None,
    address: Optional[str] = None,
    project: Optional[str] = None,
    solution: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> "Solution":
  # pyformat: disable
  """Connects to a deployed solution.

  Args:
    grpc_channel_or_hostport: gRPC channel or address. Deprecated: Use explicit `address` or `grpc_channel`
    grpc_channel: gRPC channel to use for connection.
    address: Connect directly to an address (e.g. localhost). Only one of [project, solution] and address is allowed.
    project: Google Cloud Project to connect to.
    solution: Id (not display name!) of the solution to connect to.
    options: An optional Dict[str, Any] containing additional options.
  Raises:
    ValueError: if parameter combination is incorrect.

  Returns:
    A fully initialized Solution object that represents the deployed solution.
  """
  if (
      sum([
          bool(grpc_channel_or_hostport),
          bool(grpc_channel),
          bool(
              project
              or solution
          ),
          bool(address),
      ])
      > 1
  ):
    solution_params = ["project", "solution"]
    solution_params = ", ".join(solution_params)
    raise ValueError(
        f"Only one of grpc_channel_or_host_port, [{solution_params}],"
        " grpc_channel or address is allowed!"
    )

  if grpc_channel:
    channel = grpc_channel
  else:
    channel = create_grpc_channel(
        grpc_channel_or_hostport,
        address=address,
        project=project,
        solution=solution,
    )

  return Solution.for_channel(channel, options=options)


def connect_to_selected_solution(
    *,
    options: Optional[Dict[str, Any]] = None,
) -> "Solution":
  """Connects to a deployed solution.

  Use project and solution that are set in the user config.

  Args:
    options: Same as for connect().

  Raises:
    ValueError: if config, project or solution could not be retrieved.

  Returns:
    A fully initialized Solution object that represents the deployed solution.
  """
  config = userconfig.read()

  selected_project = config.get(userconfig.SELECTED_PROJECT, None)
  if selected_project is None:
    raise ValueError("No project selected!")

  selected_solution = config.get(userconfig.SELECTED_SOLUTION, None)
  if selected_solution is None:
    raise ValueError("No solution selected!")

  return connect(
      project=selected_project, solution=selected_solution, options=options
  )


def create_grpc_channel(
    grpc_channel_or_hostport: Optional[Union[grpc.Channel, str]] = None,
    *,
    address: Optional[str] = None,
    project: Optional[str] = None,
    solution: Optional[str] = None,
) -> grpc.Channel:
  # pyformat: disable
  """Creates a gRPC channel to a deployed solution.

  Args:
    grpc_channel_or_hostport: gRPC channel to the intrinsic box or a string of
      the form "host:port" to connect to (creates a channel with default
      parameters).
    address: Connect directly to an address (e.g. localhost). Only one of
      [project, solution] and address is allowed.
    project: Google Cloud Project to connect to.
    solution: Id (not display name!) of the solution to connect to.
  Returns:
    A gRPC channel
  """
  # pyformat: enable

  params: dialerutil.CreateChannelParams = None
  if not any([
      grpc_channel_or_hostport,
      project,
      solution,
      address,
  ]):
    # Legacy behavior: Use default hostport if called without params.
    default_address = os.environ.get(
        _XFA_BOX_ADDRESS_ENVIRONMENT_VAR, _DEFAULT_HOSTPORT
    )
    params = dialerutil.CreateChannelParams(address=default_address)
  elif grpc_channel_or_hostport:
    warnings.warn(
        "grpc_channel_or_host_port is deprecated. Use `address` or"
        " `grpc_channel` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if isinstance(grpc_channel_or_hostport, str):
      params = dialerutil.CreateChannelParams(address=grpc_channel_or_hostport)
    elif isinstance(grpc_channel_or_hostport, grpc.Channel):
      return grpc_channel_or_hostport
    else:
      raise ValueError(
          "Unsupported grpc_channel_or_host_port type"
          f" ({type(grpc_channel_or_hostport)})!"
      )
  elif address is not None:
    params = dialerutil.CreateChannelParams(address=address)
  elif (
      (project is not None)
      or (solution is not None)
  ):
    # pyformat: disable
    if not (project and (
        solution
    )):
      raise ValueError(
          f"'project' ({project}) and 'solution' ({solution}) "
          "are required!"
      )
    # pyformat: enable

    resolved_cluster = None
    if solution:
      resolved_cluster = _get_cluster_from_solution(project, solution)

    params = dialerutil.CreateChannelParams(
        project_name=project, cluster=resolved_cluster
    )

  return dialerutil.create_channel(params, grpc_options=_GRPC_OPTIONS)


def _get_cluster_from_solution(project: str, solution_id: str) -> str:
  # Open a temporary gRPC channel to the cloud cluster to resolve the cluster
  # on which the solution is running.
  params = dialerutil.CreateChannelParams(project_name=project)
  channel = dialerutil.create_channel(params)
  stub = solutiondiscovery_api_pb2_grpc.SolutionDiscoveryServiceStub(channel)
  response = stub.GetSolutionDescription(
      solutiondiscovery_api_pb2.GetSolutionDescriptionRequest(name=solution_id)
  )
  channel.close()

  return response.solution.cluster_name


@solution_errors.retry_on_pending_backend
@error_handling.retry_on_grpc_unavailable
def _get_solution_status_with_retry(
    stub: installer_pb2_grpc.InstallerServiceStub,
) -> installer_pb2.GetInstalledSpecResponse:
  """Loads a solution's status.

  Args:
    stub: Installer service to query health.

  Returns:
    Workcell status

  Raises:
    solution_errors.BackendPendingError: Will lead to retry.
    solution_errors.BackendHealthError: Not recoverable.
  """
  try:
    response = stub.GetInstalledSpec(empty_pb2.Empty())

    if response.status != installer_pb2.GetInstalledSpecResponse.HEALTHY:
      if response.status == installer_pb2.GetInstalledSpecResponse.PENDING:
        print("Solution backends not healthy yet. Retrying...")
        print(f"Reason: {response.error_reason}")
        # Note this error leads to a retry given the retry_on_pending_backend
        # decorator.
        raise solution_errors.BackendPendingError(
            f"Workcell backends not healthy yet. {response.error_reason}"
        )
      if response.status == installer_pb2.GetInstalledSpecResponse.ERROR:
        raise solution_errors.BackendHealthError(
            "Workcell backend is unhealthy and not expected to recover "
            "without intervention. Try restarting your solution. "
            f"{response.error_reason}"
        )
      else:
        raise solution_errors.BackendHealthError(
            "Unexpected solution health status. Try restarting your "
            f"solution. {response.error_reason}"
        )
    return response
  except grpc.RpcError as e:
    if hasattr(e, "code"):
      if e.code() == grpc.StatusCode.NOT_FOUND:
        raise solution_errors.BackendNoWorkcellError(
            "No workcell spec has been installed. "
            "Start a solution before connecting."
        )
    raise
