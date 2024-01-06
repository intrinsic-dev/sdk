# Copyright 2023 Intrinsic Innovation LLC

"""Library to run skill services from the skill image builder."""

from absl import app
from absl import flags
from intrinsic.skills.internal import module_utils
from intrinsic.skills.internal import runtime_data as rd
from intrinsic.skills.internal import single_skill_factory
from intrinsic.skills.internal import skill_init
from intrinsic.skills.python import skill_interface as skl

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
    "geomservice.app-intrinsic-base:8080",
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

  if not _SKILL_SERVICE_CONFIG_FILENAME.value:
    raise SystemExit("--skill_service_config_filename not set")

  service_config = skill_init.get_skill_service_config(
      _SKILL_SERVICE_CONFIG_FILENAME.value
  )

  skill_class_list = module_utils.get_subclasses_in_modules(
      module_names=service_config.python_config.module_names[:],
      module_baseclass=skl.Skill,
  )

  num_skills = len(skill_class_list)
  if num_skills != 1:
    raise SystemExit(f"Expected to find only 1 class, found {num_skills}")

  skill = skill_class_list[0]
  runtime_data = rd.get_runtime_data_from(
      skill_service_config=service_config,
      # This is assigned by skill_image_builder when building the skill.
      parameter_descriptor=skill._parameter_descriptor,  # pylint: disable=protected-access
  )
  skill_repository = single_skill_factory.SingleSkillFactory(
      skill_runtime_data=runtime_data, create_skill=skill
  )

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
  app.run(main)
