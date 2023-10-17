// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/internal/skill_init.h"

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/algorithm/container.h"
#include "absl/flags/flag.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "google/protobuf/descriptor.pb.h"
#include "grpc/grpc.h"
#include "grpcpp/channel.h"
#include "grpcpp/security/server_credentials.h"
#include "grpcpp/server.h"
#include "grpcpp/server_builder.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/logging/data_logger_client.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.grpc.pb.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/skill_proto_utils.h"
#include "intrinsic/skills/internal/skill_registry_client.h"
#include "intrinsic/skills/internal/skill_repository.h"
#include "intrinsic/skills/internal/skill_service_impl.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/grpc/grpc.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic::skills {
namespace {

using ObjectWorldService = ::intrinsic_proto::world::ObjectWorldService;
using MotionPlannerService =
    ::intrinsic_proto::motion_planning::MotionPlannerService;

absl::StatusOr<std::shared_ptr<
    intrinsic_proto::motion_planning::MotionPlannerService::Stub>>
CreateMotionPlannerServiceStub(absl::string_view motion_planner_service_address,
                               absl::Duration connection_timeout) {
  INTRINSIC_ASSIGN_OR_RETURN(
      const std::shared_ptr<grpc::Channel> channel,
      CreateClientChannel(motion_planner_service_address,
                          absl::Now() + connection_timeout));
  return intrinsic_proto::motion_planning::MotionPlannerService::NewStub(
      channel);
}

}  // namespace

absl::Status SkillInit(
    const intrinsic_proto::skills::SkillServiceConfig& service_config,
    absl::string_view data_logger_grpc_service_address,
    absl::string_view world_service_address,
    absl::string_view geometry_service_address,
    absl::string_view motion_planner_service_address,
    absl::string_view skill_registry_service_address,
    int32_t skill_service_port, absl::Duration connection_timeout,
    SkillRepository& skill_repository) {
  // Start DataLogger if the endpoint is configured by flags. Do not fail if
  // the logger is unavailable.
  if (!data_logger_grpc_service_address.empty()) {
    if (auto s = intrinsic::data_logger::StartUpIntrinsicLoggerViaGrpc(
            data_logger_grpc_service_address, connection_timeout);
        !s.ok()) {
      LOG(ERROR) << "Failed to connect to data logger: " << s;
    }
  }

  // Set up world service.
  INTRINSIC_ASSIGN_OR_RETURN(
      const std::shared_ptr<grpc::Channel> world_service_channel,
      CreateClientChannel(world_service_address,
                          absl::Now() + connection_timeout));

  std::shared_ptr<ObjectWorldService::StubInterface> object_world_service =
      ObjectWorldService::NewStub(world_service_channel);

  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<MotionPlannerService::StubInterface>
          motion_planner_service,
      CreateMotionPlannerServiceStub(motion_planner_service_address,
                                     connection_timeout));

  // Set up the skill registry client.
  INTRINSIC_ASSIGN_OR_RETURN(
      std::unique_ptr<SkillRegistryClient> skill_registry_client,
      CreateSkillRegistryClient(skill_registry_service_address));

  SkillProjectorServiceImpl project_service(
      skill_repository, object_world_service, motion_planner_service);
  SkillExecutorServiceImpl execute_service(
      skill_repository, object_world_service, motion_planner_service);

  std::string server_address = absl::StrCat("0.0.0.0:", skill_service_port);

  grpc::ServerBuilder builder;
  std::shared_ptr<grpc::ServerCredentials> creds =
      grpc::InsecureServerCredentials();  // NOLINT (insecure)
  builder.AddListeningPort(server_address, creds);
  builder.AddChannelArgument(GRPC_ARG_ALLOW_REUSEPORT, 0);
  builder.RegisterService(&project_service);
  builder.RegisterService(&execute_service);

  // Initialize the skill information service if service_config has a
  // skill_description or skill_name (which means we're running a modular skill
  // server).
  std::unique_ptr<SkillInformationServiceImpl> skill_information_service;
  if (service_config.has_skill_description() ||
      !service_config.skill_name().empty()) {
    google::protobuf::FileDescriptorSet parameter_file_descriptor_set;
    if (!service_config.parameter_descriptor_filename().empty()) {
      INTRINSIC_ASSIGN_OR_RETURN(
          parameter_file_descriptor_set,
          GetBinaryProto<google::protobuf::FileDescriptorSet>(
              service_config.parameter_descriptor_filename()));
    }
    google::protobuf::FileDescriptorSet return_value_file_descriptor_set;
    if (!service_config.return_value_descriptor_filename().empty()) {
      INTRINSIC_ASSIGN_OR_RETURN(
          return_value_file_descriptor_set,
          GetBinaryProto<google::protobuf::FileDescriptorSet>(
              service_config.return_value_descriptor_filename()));
    }

    intrinsic_proto::skills::Skill skill_description;
    if (!service_config.has_skill_description()) {
      absl::StatusOr<std::unique_ptr<SkillInterface>> status_or_skill_object =
          skill_repository.GetSkill(service_config.skill_name());
      if (!status_or_skill_object.ok()) {
        return intrinsic::AnnotateError(
            status_or_skill_object.status(),
            absl::StrCat(
                "available skills are: ",
                absl::StrJoin(skill_repository.GetSkillAliases(), ", ")));
      }

      auto skill_object = std::move(*status_or_skill_object);
      INTRINSIC_ASSIGN_OR_RETURN(skill_description,
                                 BuildSkillProto(*skill_object));
      LOG(INFO) << "Adding skill information server with modular skill "
                << skill_description.skill_name();

      INTRINSIC_RETURN_IF_ERROR(AddFileDescriptorSetWithoutSourceCodeInfo(
          *skill_object, parameter_file_descriptor_set,
          return_value_file_descriptor_set, skill_description));
    } else {
      skill_description = service_config.skill_description();
    }

    skill_information_service =
        std::make_unique<SkillInformationServiceImpl>(skill_description);
    builder.RegisterService(skill_information_service.get());
  }
  std::unique_ptr<::grpc::Server> server(builder.BuildAndStart());
  if (server == nullptr) {
    LOG(FATAL) << "Cannot create skill service " << server_address;
  }

  std::vector<std::string> skill_names = skill_repository.GetSkillAliases();
  absl::c_sort(skill_names);

  LOG(INFO) << "Available skills: ";
  for (const auto& name : skill_names) {
    LOG(INFO) << "\t" << name;
  }

  LOG(INFO) << "--------------------------------";
  LOG(INFO) << "-- Skill service listening on " << server_address;
  LOG(INFO) << "--------------------------------";

  server->Wait();
  return absl::OkStatus();
}

absl::StatusOr<intrinsic_proto::skills::SkillServiceConfig>
GetSkillServiceConfig(absl::string_view skill_service_config_filename) {
  intrinsic_proto::skills::SkillServiceConfig service_config;
  if (!skill_service_config_filename.empty()) {
    LOG(INFO) << "Reading skill configuration proto from "
              << skill_service_config_filename;
    INTRINSIC_ASSIGN_OR_RETURN(
        service_config,
        GetBinaryProto<intrinsic_proto::skills::SkillServiceConfig>(
            skill_service_config_filename));
    LOG(INFO) << "\nUsing skill configuration proto:\n" << service_config;
  }
  return service_config;
}

}  // namespace intrinsic::skills
