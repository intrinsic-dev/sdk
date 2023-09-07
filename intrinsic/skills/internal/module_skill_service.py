# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Library to run Project and Execute skill services.

Initializes a server with SkillProjectorServicer and SkillExecutorServicer
servicers. Skills provided by these servicers are from a given module.
"""

from absl import app
from absl import flags
from intrinsic.skills.internal import module_utils
from intrinsic.skills.internal import skill_init
from intrinsic.skills.proto import skill_service_config_pb2
from intrinsic.skills.python import skill_interface as skl
from intrinsic.skills.testing import map_skill_repository

_THREADS = flags.DEFINE_integer(
    "threads", 8, "Number of server threads to run."
)
_PORT = flags.DEFINE_integer("port", 8002, "Port to serve gRPC on.")
_SKILL_SERVICE_CONFIG_FILENAME = flags.DEFINE_string(
    "skill_service_config_filename",
    "",
    (
        "Filename for the SkillServiceConfig binary proto. When present, an "
        "additional server (skill information) is started. The skill registry "
        "queries this server to get information about this skill."
    ),
)
_SKILLS_MODULES = flags.DEFINE_list(
    "skills_modules", "", "Modules with skills to run on the service."
)
_WORLD_SERVICE_ADDRESS = flags.DEFINE_string(
    "world_service_address", "world:8080", "gRPC target for the World service"
)
_MOTION_PLANNER_SERVICE_ADDRESS = flags.DEFINE_string(
    "motion_planner_service_address",
    "motion-planner-service:8080",
    "gRPC target for the MotionPlanner service",
)
_GEOMETRY_SERVICE_ADDRESS = flags.DEFINE_string(
    "geometry_service_address",
    "geomservice:8080",
    "gRPC target for the Geometry service",
)
_SKILL_REGISTRY_SERVICE_ADDRESS = flags.DEFINE_string(
    "skill_registry_service_address",
    "skill-registry:8080",
    "gRPC target for the skill registry service. (deprecated, present to match"
    " cpp skill service)",
)
_GRPC_CONNECT_TIMEOUT = flags.DEFINE_integer(
    "grpc_connect_timeout_secs",
    60,
    "Time to wait for other grpc services to become available in seconds.",
)

_ = flags.DEFINE_string(
    "data_logger_grpc_service_address", "", "Dummy flag, do not use"
)
_ = flags.DEFINE_integer(
    "opencensus_metrics_port", 9999, "Dummy flag, do not use"
)
_ = flags.DEFINE_bool("opencensus_tracing", True, "Dummy flag, do not use")


def main(argv):
  del argv  # unused

  if _SKILL_SERVICE_CONFIG_FILENAME.value:
    service_config = skill_init.get_skill_service_config(
        _SKILL_SERVICE_CONFIG_FILENAME.value
    )
  else:
    service_config = skill_service_config_pb2.SkillServiceConfig(
        python_config=skill_service_config_pb2.PythonSkillServiceConfig(
            module_names=_SKILLS_MODULES.value
        )
    )

  skill_class_list = module_utils.get_subclasses_in_modules(
      module_names=service_config.python_config.module_names[:],
      module_baseclass=skl.Skill,
  )
  skill_repository = map_skill_repository.MapSkillRepository()
  for skill in skill_class_list:
    skill_repository.insert_or_assign_skill(skill.name(), skill)

  skill_init.skill_init(
      skill_repository=skill_repository,
      skill_service_config=service_config,
      num_threads=_THREADS.value,
      skill_service_port=_PORT.value,
      world_service_address=_WORLD_SERVICE_ADDRESS.value,
      motion_planner_service_address=_MOTION_PLANNER_SERVICE_ADDRESS.value,
      geometry_service_address=_GEOMETRY_SERVICE_ADDRESS.value,
      connection_timeout=_GRPC_CONNECT_TIMEOUT.value,
  )


if __name__ == "__main__":
  app.run(main, change_root_and_user=False)
