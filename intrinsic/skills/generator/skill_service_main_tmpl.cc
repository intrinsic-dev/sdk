// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Server with single-skill based services.

#include <cstdint>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/time/time.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/skills/internal/runtime_data.h"
#include "intrinsic/skills/internal/single_skill_factory.h"
#include "intrinsic/skills/internal/skill_init.h"
#include "intrinsic/util/grpc/grpc.h"
// clang-format off
{{- range .CCHeaderPaths }}
#include "{{ . }}"
{{- end }}
// clang-format on

ABSL_FLAG(int32_t, port, 8001, "Port to serve gRPC on.");
ABSL_FLAG(std::string, skill_service_config_filename, "",
          "Filename for the SkillServiceConfig binary proto. When present, an "
          "additional server (skill information) is started. The skill "
          "registry queries this server to get information about this skill.");
ABSL_FLAG(std::string, data_logger_grpc_service_address, "",
          "(optional) Address of the Intrinsic DataLogger gRPC service.");
ABSL_FLAG(std::string, world_service_address, "world:8080",
          "gRpc target for the World service");
ABSL_FLAG(std::string, geometry_service_address, "geomservice:8080",
          "gRpc target for the geometry service");
ABSL_FLAG(std::string, motion_planner_service_address,
          "motion-planner-service:8080",
          "gRpc target for the motion planner service");
ABSL_FLAG(std::string, skill_registry_service_address, "skill-registry:8080",
          "gRpc target for the skill registry service");
ABSL_FLAG(int32_t, grpc_connect_timeout_secs,
          absl::ToInt64Seconds(intrinsic::kGrpcClientConnectDefaultTimeout),
          "Time to wait for other grpc services to become available.");

ABSL_FLAG(bool, logtostderr, true, "Dummy flag, do not use");
ABSL_FLAG(int32_t, opencensus_metrics_port, 9999, "Dummy flag, do not use");
ABSL_FLAG(bool, opencensus_tracing, true, "Dummy flag, do not use");

namespace {

using ::intrinsic::skills::GetSkillServiceConfig;
using ::intrinsic::skills::SkillInit;
using ::intrinsic::skills::internal::GetRuntimeDataFrom;
using ::intrinsic::skills::internal::SingleSkillFactory;
using ::intrinsic::skills::internal::SkillRuntimeData;
using ::intrinsic_proto::skills::SkillServiceConfig;

}  // namespace

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);

  absl::StatusOr<SkillServiceConfig> service_config =
      GetSkillServiceConfig(absl::GetFlag(FLAGS_skill_service_config_filename));
  QCHECK_OK(service_config.status())
      << "Failed to read skill service config at: "
      << absl::GetFlag(FLAGS_skill_service_config_filename);

  // clang-format off
  absl::StatusOr<SkillRuntimeData> runtime_data = GetRuntimeDataFrom(
      *service_config,
      {{.ParameterDescriptorPtr}},
      {{.ReturnDescriptorPtr}});
  // clang-format on
  QCHECK_OK(runtime_data.status()) << "Failed to create SkillRuntimeData";

  // clang-format off
  SingleSkillFactory skill_factory(
      *runtime_data,
      {{.CreateSkillMethod}});
  // clang-format on
  QCHECK_OK(SkillInit(
      *service_config, absl::GetFlag(FLAGS_data_logger_grpc_service_address),
      absl::GetFlag(FLAGS_world_service_address),
      absl::GetFlag(FLAGS_geometry_service_address),
      absl::GetFlag(FLAGS_motion_planner_service_address),
      absl::GetFlag(FLAGS_skill_registry_service_address),
      absl::GetFlag(FLAGS_port),
      absl::Seconds(absl::GetFlag(FLAGS_grpc_connect_timeout_secs)),
      skill_factory))
      << "Initializing skill service failed.";
  return 0;
}
