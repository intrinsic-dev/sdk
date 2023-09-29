// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/internal/skill_service_impl.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/log.h"
#include "absl/memory/memory.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "absl/strings/substitute.h"
#include "absl/synchronization/mutex.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/empty.pb.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/grpcpp.h"
#include "grpcpp/support/status.h"
#include "intrinsic/assets/id_utils.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.grpc.pb.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/equipment_utilities.h"
#include "intrinsic/skills/internal/error_utils.h"
#include "intrinsic/skills/internal/execute_context_impl.h"
#include "intrinsic/skills/internal/get_footprint_context_impl.h"
#include "intrinsic/skills/internal/runtime_data.h"
#include "intrinsic/skills/internal/skill_registry_client_interface.h"
#include "intrinsic/skills/internal/skill_repository.h"
#include "intrinsic/skills/proto/error.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/proto/merge.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic {
namespace skills {

using ::intrinsic::assets::NameFrom;
using ::intrinsic::assets::RemoveVersionFrom;

namespace {

template <class Request>
absl::Status ValidateRequest(const Request& request) {
  if (request.world_id().empty()) {
    return absl::InvalidArgumentError(
        "Cannot load a world with an empty world_id");
  }
  return absl::OkStatus();
}

template <class ProjectOrExecuteRequest>
absl::Status SetDefaultsInRequest(
    const google::protobuf::Message& prototype,
    const internal::SkillRuntimeData& runtime_data,
    ProjectOrExecuteRequest& request) {
  auto param_defaults = absl::WrapUnique(prototype.New());
  if (std::optional<google::protobuf::Any> defaults =
          runtime_data.GetParameterData().GetDefault();
      defaults.has_value()) {
    if (!defaults->UnpackTo(param_defaults.get())) {
      return absl::InternalError(absl::StrFormat(
          "failed to unpack default parameters for: %s", runtime_data.GetId()));
    }
  }
  auto params = absl::WrapUnique(prototype.New());
  request.parameters().UnpackTo(params.get());
  INTRINSIC_RETURN_IF_ERROR(MergeUnset(*param_defaults, *params));
  request.mutable_parameters()->PackFrom(*params);
  return absl::OkStatus();
}

}  // namespace

namespace internal {

absl::StatusOr<std::unique_ptr<SkillExecutionOperation>>
SkillExecutionOperation::Create(
    const intrinsic_proto::skills::ExecuteRequest* request,
    const std::optional<::google::protobuf::Any>& param_defaults,
    std::shared_ptr<SkillCancellationManager> canceller) {
  if (request == nullptr) {
    return absl::InvalidArgumentError("`request` is null.");
  }
  return absl::WrapUnique(new SkillExecutionOperation(
      /*instance_name=*/request->instance().instance_name(),
      /*id_version=*/request->instance().id_version(),
      /*params=*/request->parameters(), param_defaults, canceller, *request));
}

absl::Status SkillExecutionOperation::StartExecute(
    std::unique_ptr<SkillExecuteInterface> skill,
    std::unique_ptr<ExecuteContextImpl> context) {
  if (skill == nullptr) {
    return absl::InvalidArgumentError("`skill` is null.");
  }
  if (context == nullptr) {
    return absl::InvalidArgumentError("`context` is null.");
  }

  {
    absl::MutexLock lock(&thread_mutex_);
    if (thread_ != nullptr) {
      return absl::FailedPreconditionError(
          "An execution thread already exists.");
    }
    thread_ = std::make_unique<Thread>([this, skill = std::move(skill),
                                        context = std::move(
                                            context)]() -> absl::Status {
      absl::StatusOr<intrinsic_proto::skills::ExecuteResult> skill_result;
      {
        skill_result =
            skill->Execute(ExecuteRequest(params_, param_defaults_), *context);
      }

      if (!skill_result.ok()) {
        intrinsic_proto::skills::SkillErrorInfo error_info;
        error_info.set_error_type(
            intrinsic_proto::skills::SkillErrorInfo::ERROR_TYPE_SKILL);
        auto rpc_status = ToGoogleRpcStatus(skill_result.status(), error_info);
        LOG(ERROR) << "Skill: " << GetSkillIdVersion()
                   << " returned an error during execution. code: "
                   << rpc_status.code()
                   << ", message: " << rpc_status.message();

        INTRINSIC_RETURN_IF_ERROR(Finish(&rpc_status, nullptr));
      } else {
        INTRINSIC_RETURN_IF_ERROR(Finish(nullptr, &(*skill_result)));
      }

      return absl::OkStatus();
    });
  }

  return absl::OkStatus();
}

absl::Status SkillExecutionOperation::RequestCancellation() {
  if (canceller_ == nullptr) {
    return absl::UnimplementedError(
        absl::StrFormat("Skill does not support cancellation: %s.", GetName()));
  }

  return canceller_->Cancel();
}

absl::StatusOr<google::longrunning::Operation>
SkillExecutionOperation::WaitExecution(absl::Time deadline) {
  finished_notification_.WaitForNotificationWithDeadline(deadline);

  return GetOperation();
}

void SkillExecutionOperation::WaitOperation(absl::string_view caller_name) {
  // Wait for skill execution to finish.
  LOG(INFO) << caller_name << " waiting for operation to finish: \""
            << GetName() << "\".";
  finished_notification_.WaitForNotification();

  // Wait until the thread that executed the skill is finished. This wait
  // shouldn't take long, since `finished_notification_` is notified as the
  // last step of execution.
  {
    absl::MutexLock lock(&thread_mutex_);
    if (thread_ != nullptr && thread_->Joinable()) {
      LOG(INFO) << caller_name << " joining operation thread: \"" << GetName()
                << "\".";
      thread_->Join();
      thread_.reset();
    }
  }

  LOG(INFO) << caller_name << " finished waiting for operation: \"" << GetName()
            << "\".";
}

absl::Status SkillExecutionOperation::Finish(
    const ::google::rpc::Status* error,
    const intrinsic_proto::skills::ExecuteResult* result) {
  absl::MutexLock lock(&operation_mutex_);
  if (GetFinished()) {
    return absl::FailedPreconditionError(
        absl::StrFormat("The operation has already finished: %s.", GetName()));
  }

  if (error != nullptr) {
    operation_.mutable_error()->MergeFrom(*error);
  }
  if (result != nullptr) {
    operation_.mutable_response()->PackFrom(*result);
  }
  operation_.set_done(true);

  finished_notification_.Notify();

  return absl::OkStatus();
}

absl::Status SkillExecutionOperationCleaner::Watch(
    std::shared_ptr<SkillExecutionOperation> operation) {
  bool start_processing_queue = false;
  {
    absl::MutexLock lock(&queue_mutex_);

    queue_.push_back(operation);

    if (queue_processed_->HasBeenNotified()) {
      start_processing_queue = true;
      queue_processed_ = std::make_shared<absl::Notification>();
    }
  }

  if (start_processing_queue) {
    {
      absl::MutexLock lock(&thread_mutex_);

      WaitThread();
      thread_ = std::make_unique<Thread>([this]() { ProcessQueue(); });
    }
  }

  return absl::OkStatus();
}

void SkillExecutionOperationCleaner::WaitOperations(
    const std::string& caller_name) {
  std::shared_ptr<absl::Notification> queue_processed;
  {
    absl::MutexLock lock(&queue_mutex_);
    LOG(INFO) << caller_name << " waiting for cleaner to process "
              << queue_.size() << " operation(s)).";

    queue_processed = queue_processed_;
  }
  queue_processed->WaitForNotification();

  {
    absl::MutexLock lock(&thread_mutex_);
    WaitThread(caller_name);
  }

  LOG(INFO) << caller_name << " finished waiting.";
}

void SkillExecutionOperationCleaner::ProcessQueue() {
  while (true) {
    std::shared_ptr<SkillExecutionOperation> operation;
    {
      absl::MutexLock lock(&queue_mutex_);
      if (queue_.empty()) {
        queue_processed_->Notify();
        return;
      }

      LOG(INFO) << "Cleaner queue has " << queue_.size() << " operation(s).";

      operation = queue_.front();
      queue_.pop_front();
    }

    operation->WaitOperation("Cleaner");
  }
}

void SkillExecutionOperationCleaner::WaitThread(
    const std::string& caller_name) {
  if (thread_ != nullptr) {
    if (!caller_name.empty()) {
      LOG(INFO) << caller_name << " joining cleaner thread.";
    }
    thread_->Join();
    thread_.reset();
  }
}

absl::StatusOr<std::shared_ptr<SkillExecutionOperation>>
SkillExecutionOperations::StartExecute(
    std::unique_ptr<SkillExecuteInterface> skill,
    const intrinsic_proto::skills::ExecuteRequest* request,
    const std::optional<::google::protobuf::Any>& param_defaults,
    std::unique_ptr<ExecuteContextImpl> context,
    std::shared_ptr<SkillCancellationManager> canceller,
    google::longrunning::Operation& initial_operation) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<internal::SkillExecutionOperation> operation,
      internal::SkillExecutionOperation::Create(request, param_defaults,
                                                canceller));
  initial_operation = operation->GetOperation();

  INTRINSIC_RETURN_IF_ERROR(Add(operation));

  INTRINSIC_RETURN_IF_ERROR(
      operation->StartExecute(std::move(skill), std::move(context)));

  INTRINSIC_RETURN_IF_ERROR(cleaner_.Watch(operation));

  return operation;
}

absl::Status SkillExecutionOperations::Add(
    std::shared_ptr<SkillExecutionOperation> operation) {
  absl::MutexLock lock(&update_mutex_);

  // First remove the oldest finished operation if we've reached our limit of
  // tracked operations.
  while (operation_names_.size() >= kMaxNumOperations) {
    bool finished_operation_found = false;
    for (auto name_it = operation_names_.begin(), end = operation_names_.end();
         name_it != end; ++name_it) {
      auto op_it = operations_.find(*name_it);
      if (op_it == operations_.end()) {
        return absl::InternalError(absl::StrFormat(
            "%s found in operation_names_ but not in operations_.", *name_it));
      }
      if (op_it->second->GetFinished()) {
        finished_operation_found = true;
        operation_names_.erase(name_it);
        operations_.erase(op_it);
        break;
      }
    }
    if (!finished_operation_found) {
      return absl::FailedPreconditionError(
          absl::StrFormat("Cannot add operation %s, since there are already %d "
                          "unfinished operations.",
                          operation->GetName(), operations_.size()));
    }
  }

  std::string operation_name = operation->GetName();

  if (auto [_, inserted] = operations_.emplace(operation_name, operation);
      !inserted) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "An operation already exists with name '%s'.", operation_name));
  }

  operation_names_.push_back(operation_name);

  return absl::OkStatus();
}

absl::StatusOr<std::shared_ptr<SkillExecutionOperation>>
SkillExecutionOperations::Get(absl::string_view name) {
  absl::MutexLock lock(&update_mutex_);
  auto itr = operations_.find(name);
  if (itr == operations_.end()) {
    return absl::NotFoundError(
        absl::StrFormat("No operation found with name '%s'.", name));
  }
  return itr->second;
}

absl::Status SkillExecutionOperations::Clear(bool wait_for_operations) {
  absl::MutexLock lock(&update_mutex_);

  std::vector<std::string> unfinished_operation_names;
  for (auto& [_, operation] : operations_) {
    if (operation->GetFinished() || wait_for_operations) {
      // Wait until the operation thread is finished.
      operation->WaitOperation("Clear operations");
    } else {
      unfinished_operation_names.push_back(operation->GetName());
    }
  }
  if (!unfinished_operation_names.empty()) {
    return absl::FailedPreconditionError(
        absl::StrFormat("The following operations are not yet finished: '%s'.",
                        absl::StrJoin(unfinished_operation_names, ", ")));
  }

  operations_ = {};
  operation_names_ = {};

  // Wait until the cleaner thread is finished.
  cleaner_.WaitOperations("Clear operations");

  return absl::OkStatus();
}

std::vector<std::string> SkillExecutionOperations::GetOperationSkillIdVersions()
    const {
  absl::MutexLock lock(&update_mutex_);
  std::vector<std::string> skill_id_versions;
  skill_id_versions.reserve(operation_names_.size());
  for (const std::string& operation_name : operation_names_) {
    if (operations_.find(operation_name) == operations_.end()) {
      LOG(ERROR) << "operations_ and operation_names_ have inconsistent "
                    "view. operation_name_ == "
                 << operation_name
                 << " exists in operation_names_ but not operations_.";
      continue;
    }
    skill_id_versions.push_back(
        operations_.find(operation_name)->second->GetSkillIdVersion());
  }
  return skill_id_versions;
}

std::vector<intrinsic_proto::skills::ExecuteRequest>
SkillExecutionOperations::GetExecuteRequests() const {
  absl::MutexLock lock(&update_mutex_);
  std::vector<intrinsic_proto::skills::ExecuteRequest> execute_requests;
  execute_requests.reserve(operation_names_.size());
  for (const std::string& operation_name : operation_names_) {
    auto itr = operations_.find(operation_name);
    if (itr == operations_.end()) {
      LOG(ERROR) << "operations_ and operation_names_ have inconsistent "
                    "view. operation_name_ == "
                 << operation_name
                 << " exists in operation_names_ but not operations_.";
      continue;
    }
    std::optional<intrinsic_proto::skills::ExecuteRequest> request =
        itr->second->GetExecuteRequest();
    if (request.has_value()) {
      execute_requests.push_back(*request);
    }
  }
  return execute_requests;
}

}  // namespace internal

SkillProjectorServiceImpl::SkillProjectorServiceImpl(
    SkillRepository& skill_repository,
    std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
    std::shared_ptr<MotionPlannerService::StubInterface> motion_planner_service,
    SkillRegistryClientInterface& skill_registry_client)
    : object_world_service_(std::move(object_world_service)),
      motion_planner_service_(std::move(motion_planner_service)),
      skill_repository_(skill_repository),
      skill_registry_client_(skill_registry_client),
      message_factory_(google::protobuf::MessageFactory::generated_factory()) {}

absl::StatusOr<GetFootprintRequest>
SkillProjectorServiceImpl::ProtoToGetFootprintRequest(
    const intrinsic_proto::skills::GetFootprintRequest& request) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::string id, RemoveVersionFrom(request.instance().id_version()));
  INTRINSIC_ASSIGN_OR_RETURN(std::string skill_name, NameFrom(id));
  INTRINSIC_ASSIGN_OR_RETURN(internal::SkillRuntimeData runtime_data,
                             skill_repository_.GetSkillRuntimeData(skill_name));

  return GetFootprintRequest(request.parameters(),
                             runtime_data.GetParameterData().GetDefault());
}

grpc::Status SkillProjectorServiceImpl::GetFootprint(
    grpc::ServerContext* context,
    const intrinsic_proto::skills::GetFootprintRequest* request,
    intrinsic_proto::skills::GetFootprintResult* result) {
  LOG(INFO) << "Attempting to get footprint '"
            << request->instance().id_version() << "' skill with world id '"
            << request->world_id() << "'";

  INTRINSIC_RETURN_IF_ERROR(ValidateRequest(*request));

  INTRINSIC_ASSIGN_OR_RETURN(const std::string skill_name,
                             NameFrom(request->instance().id_version()));
  LOG(INFO) << "Calling GetFootprint for skill name: " << skill_name;
  INTRINSIC_ASSIGN_OR_RETURN(std::unique_ptr<SkillProjectInterface> skill,
                             skill_repository_.GetSkillProject(skill_name));

  INTRINSIC_ASSIGN_OR_RETURN(GetFootprintRequest get_footprint_request,
                             ProtoToGetFootprintRequest(*request));

  INTRINSIC_ASSIGN_OR_RETURN(EquipmentPack equipment,
                             EquipmentPack::GetEquipmentPack(*request));

  GetFootprintContextImpl footprint_context(
      request->world_id(), request->context(), object_world_service_,
      motion_planner_service_, std::move(equipment), skill_registry_client_);
  auto skill_result =
      skill->GetFootprint(get_footprint_request, footprint_context);

  if (!skill_result.ok()) {
    intrinsic_proto::skills::SkillErrorInfo error_info;
    error_info.set_error_type(
        intrinsic_proto::skills::SkillErrorInfo::ERROR_TYPE_SKILL);
    return ToGrpcStatus(skill_result.status(), error_info);
  }

  INTRINSIC_ASSIGN_OR_RETURN(internal::SkillRuntimeData runtime_data,
                             skill_repository_.GetSkillRuntimeData(skill_name));

  // Populate the footprint in the result with equipment reservations.
  *result->mutable_footprint() = std::move(skill_result).value();
  INTRINSIC_ASSIGN_OR_RETURN(
      auto equipment_resources,
      ReserveEquipmentRequired(
          runtime_data.GetResourceData().GetRequiredResources(),
          request->instance().equipment_handles()));
  for (const auto& equipment_resource : equipment_resources) {
    *result->mutable_footprint()->add_equipment_resource() = equipment_resource;
  }

  return ::grpc::Status::OK;
}

grpc::Status SkillProjectorServiceImpl::Predict(
    grpc::ServerContext* context,
    const intrinsic_proto::skills::PredictRequest* request,
    intrinsic_proto::skills::PredictResult* result) {
  result->set_internal_data(request->internal_data());
  result->add_outcomes()->set_probability(1.0);
  return ::grpc::Status::OK;
}

SkillExecutorServiceImpl::SkillExecutorServiceImpl(
    SkillRepository& skill_repository,
    std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
    std::shared_ptr<MotionPlannerService::StubInterface> motion_planner_service,
    SkillRegistryClientInterface& skill_registry_client)
    : skill_repository_(skill_repository),
      object_world_service_(std::move(object_world_service)),
      motion_planner_service_(std::move(motion_planner_service)),
      skill_registry_client_(skill_registry_client),
      message_factory_(google::protobuf::MessageFactory::generated_factory()) {}

SkillExecutorServiceImpl::~SkillExecutorServiceImpl() {
  operations_.Clear(true).IgnoreError();
}

grpc::Status SkillExecutorServiceImpl::StartExecute(
    grpc::ServerContext* context,
    const intrinsic_proto::skills::ExecuteRequest* request,
    google::longrunning::Operation* result) {
  LOG(INFO) << "Attempting to start execution of '"
            << request->instance().id_version() << "' skill with world id '"
            << request->world_id() << "'";

  INTRINSIC_RETURN_IF_ERROR(ValidateRequest(*request));

  INTRINSIC_ASSIGN_OR_RETURN(
      std::string skill_id,
      RemoveVersionFrom(request->instance().id_version()));

  INTRINSIC_ASSIGN_OR_RETURN(std::string name, NameFrom(skill_id));
  INTRINSIC_ASSIGN_OR_RETURN(internal::SkillRuntimeData runtime_data,
                             skill_repository_.GetSkillRuntimeData(name));

  INTRINSIC_ASSIGN_OR_RETURN(EquipmentPack equipment,
                             EquipmentPack::GetEquipmentPack(*request));

  std::shared_ptr<SkillCancellationManager> skill_canceller;
  if (runtime_data.GetExecutionOptions().SupportsCancellation()) {
    skill_canceller = std::make_shared<SkillCancellationManager>(
        runtime_data.GetExecutionOptions().GetCancellationReadyTimeout(),
        /*operation_name=*/absl::Substitute("skill '$0'", skill_id));
  }

  auto execute_context = std::make_unique<ExecuteContextImpl>(
      *request, object_world_service_, motion_planner_service_,
      std::move(equipment), skill_registry_client_, skill_canceller);

  INTRINSIC_ASSIGN_OR_RETURN(std::unique_ptr<SkillExecuteInterface> skill,
                             skill_repository_.GetSkillExecute(name));

  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<internal::SkillExecutionOperation> operation,
      operations_.StartExecute(std::move(skill), request,
                               runtime_data.GetParameterData().GetDefault(),
                               std::move(execute_context), skill_canceller,
                               *result));

  return grpc::Status::OK;
}

grpc::Status SkillExecutorServiceImpl::GetOperation(
    grpc::ServerContext* context,
    const google::longrunning::GetOperationRequest* request,
    google::longrunning::Operation* result) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<internal::SkillExecutionOperation> operation,
      operations_.Get(request->name()));

  *result = operation->GetOperation();
  return grpc::Status::OK;
}

grpc::Status SkillExecutorServiceImpl::CancelOperation(
    grpc::ServerContext* context,
    const google::longrunning::CancelOperationRequest* request,
    google::protobuf::Empty* result) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<internal::SkillExecutionOperation> operation,
      operations_.Get(request->name()));

  INTRINSIC_RETURN_IF_ERROR(operation->RequestCancellation());

  return grpc::Status::OK;
}

grpc::Status SkillExecutorServiceImpl::WaitOperation(
    grpc::ServerContext* context,
    const google::longrunning::WaitOperationRequest* request,
    google::longrunning::Operation* result) {
  INTRINSIC_ASSIGN_OR_RETURN(
      std::shared_ptr<internal::SkillExecutionOperation> operation,
      operations_.Get(request->name()));
  INTRINSIC_ASSIGN_OR_RETURN(
      *result, operation->WaitExecution(absl::FromChrono(context->deadline())));

  return grpc::Status::OK;
}

grpc::Status SkillExecutorServiceImpl::ClearOperations(
    grpc::ServerContext* context, const google::protobuf::Empty* request,
    google::protobuf::Empty* result) {
  return operations_.Clear(false);
}

std::vector<intrinsic_proto::skills::ExecuteRequest>
SkillExecutorServiceImpl::GetExecuteRequests() const {
  return operations_.GetExecuteRequests();
}

std::vector<std::string> SkillExecutorServiceImpl::GetExecutedSkillIdVersions()
    const {
  return operations_.GetOperationSkillIdVersions();
}

::grpc::Status SkillInformationServiceImpl::GetSkillInfo(
    ::grpc::ServerContext* context, const google::protobuf::Empty* request,
    intrinsic_proto::skills::SkillInformationResult* result) {
  *result->mutable_skill() = skill_;
  return ::grpc::Status::OK;
}

}  // namespace skills
}  // namespace intrinsic
