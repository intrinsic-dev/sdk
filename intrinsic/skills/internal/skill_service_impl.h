// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_IMPL_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_IMPL_H_

#include <cstdint>
#include <deque>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/base/thread_annotations.h"
#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"
#include "google/longrunning/operations.pb.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/empty.pb.h"
#include "grpcpp/server_context.h"
#include "grpcpp/support/status.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.grpc.pb.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/execute_context_impl.h"
#include "intrinsic/skills/internal/skill_registry_client_interface.h"
#include "intrinsic/skills/internal/skill_repository.h"
#include "intrinsic/skills/proto/skill_service.grpc.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic {
namespace skills {

namespace internal {

// Maximum number of operations to keep in a SkillExecutionOperations instance.
// This value places a hard upper limit on the number of one type of skill that
// can execute simultaneously.
constexpr int32_t kMaxNumOperations = 100;

// Encapsulates a single skill execution operation.
class SkillExecutionOperation {
 public:
  // Creates a new operation from an ExecuteRequest.
  static absl::StatusOr<std::unique_ptr<SkillExecutionOperation>> Create(
      const intrinsic_proto::skills::ExecuteRequest* request,
      const std::optional<::google::protobuf::Any>& param_defaults,
      std::shared_ptr<SkillCancellationManager> canceller);

  // Starts executing the specified skill.
  absl::Status StartExecute(std::unique_ptr<SkillExecuteInterface> skill,
                            std::unique_ptr<ExecuteContextImpl> context)
      ABSL_LOCKS_EXCLUDED(thread_mutex_);

  // True if the skill execution has finished.
  bool GetFinished() { return finished_notification_.HasBeenNotified(); }

  // A unique name for the skill execution operation.
  std::string GetName() {
    absl::ReaderMutexLock lock(&operation_mutex_);
    return operation_.name();
  }

  // Gets the id_version of the skill executed by this operation.
  // id_version is defined by: intrinsic_proto.catalog.SkillMeta.id_version
  std::string GetSkillIdVersion() const { return id_version_; }

  // Gets the ExecuteRequest associated with this operation, if any.
  const std::optional<intrinsic_proto::skills::ExecuteRequest>&
  GetExecuteRequest() const {
    return execute_request_;
  }

  // A copy of the underlying Operation proto.
  google::longrunning::Operation GetOperation() {
    absl::ReaderMutexLock lock(&operation_mutex_);
    return operation_;
  }

  // Requests cancellation of the operation.
  absl::Status RequestCancellation();

  // Waits for execution of the skill to finish.
  //
  // Returns the state of the operation when either skill execution finishes or
  // the wait timed out.
  absl::StatusOr<google::longrunning::Operation> WaitExecution(
      absl::Time deadline);

  // Waits for the entire operation to finish.
  //
  // This wait is similar to `WaitExecution`, except that it also waits for
  // post-execution cleanup, like joining and deleting the thread that executed
  // the skill.
  //
  // `caller_name` is specified for logging.
  void WaitOperation(absl::string_view caller_name)
      ABSL_LOCKS_EXCLUDED(thread_mutex_);

 private:
  SkillExecutionOperation(
      absl::string_view instance_name, absl::string_view id_version,
      const ::google::protobuf::Any& params,
      const std::optional<::google::protobuf::Any>& param_defaults,
      std::shared_ptr<SkillCancellationManager> canceller,
      const std::optional<intrinsic_proto::skills::ExecuteRequest>&
          execute_request)
      : execute_request_(execute_request),
        id_version_(id_version),
        params_(params),
        param_defaults_(param_defaults),
        canceller_(canceller) {
    absl::MutexLock lock(&operation_mutex_);
    operation_.set_name(instance_name);
  }

  // Marks the operation as finished, with an error and/or result.
  absl::Status Finish(const ::google::rpc::Status* error,
                      const intrinsic_proto::skills::ExecuteResult* result)
      ABSL_LOCKS_EXCLUDED(operation_mutex_);

  std::optional<intrinsic_proto::skills::ExecuteRequest> execute_request_;

  std::string id_version_;
  ::google::protobuf::Any params_;
  std::optional<::google::protobuf::Any> param_defaults_;

  std::shared_ptr<SkillCancellationManager> canceller_;

  // Notified when the operation is finished.
  absl::Notification finished_notification_;

  absl::Mutex operation_mutex_;
  google::longrunning::Operation operation_ ABSL_GUARDED_BY(operation_mutex_);

  absl::Mutex thread_mutex_;
  std::unique_ptr<Thread> thread_ ABSL_GUARDED_BY(thread_mutex_);
};

// Cleans up skill execution operations once they are finished.
class SkillExecutionOperationCleaner {
 public:
  SkillExecutionOperationCleaner() {
    absl::MutexLock lock(&queue_mutex_);
    queue_processed_ = std::make_shared<absl::Notification>();
    queue_processed_->Notify();
  }

  // Start watching an operation, and clean it up when it finishes.
  absl::Status Watch(std::shared_ptr<SkillExecutionOperation> operation)
      ABSL_LOCKS_EXCLUDED(queue_mutex_, thread_mutex_);

  // Waits for all operations to be cleaned up and for the queue processing
  // thread to finish.
  //
  // `caller_name` is specified for logging.
  void WaitOperations(const std::string& caller_name)
      ABSL_LOCKS_EXCLUDED(queue_mutex_, thread_mutex_);

 private:
  // Process the queue of operations.
  void ProcessQueue() ABSL_LOCKS_EXCLUDED(queue_mutex_);

  // Wait for the queue processing thread to finish.
  //
  // `caller_name` is specified for logging.
  void WaitThread(const std::string& caller_name = "")
      ABSL_SHARED_LOCKS_REQUIRED(thread_mutex_);

  absl::Mutex queue_mutex_;
  std::deque<std::shared_ptr<SkillExecutionOperation>> queue_
      ABSL_GUARDED_BY(queue_mutex_);
  std::shared_ptr<absl::Notification> queue_processed_
      ABSL_GUARDED_BY(queue_mutex_);

  absl::Mutex thread_mutex_;
  std::unique_ptr<Thread> thread_ ABSL_GUARDED_BY(thread_mutex_);
};

// A collection of skill execution operations.
class SkillExecutionOperations {
 public:
  // Creates a new SkillExecutionOperation and starts executing the skill.
  absl::StatusOr<std::shared_ptr<SkillExecutionOperation>> StartExecute(
      std::unique_ptr<SkillExecuteInterface> skill,
      const intrinsic_proto::skills::ExecuteRequest* request,
      const std::optional<::google::protobuf::Any>& param_defaults,
      std::unique_ptr<ExecuteContextImpl> context,
      std::shared_ptr<SkillCancellationManager> canceller,
      google::longrunning::Operation& initial_operation);

  // Gets an operation by name.
  absl::StatusOr<std::shared_ptr<SkillExecutionOperation>> Get(
      absl::string_view name) ABSL_LOCKS_EXCLUDED(update_mutex_);

  // Clears all operations in the collection.
  //
  // NOTE: If wait_for_operations is false, the operations must all be
  // finished before clearing them. If any operation is not yet finished, no
  // operations will be cleared, and an error status will be returned.
  absl::Status Clear(bool wait_for_operations)
      ABSL_LOCKS_EXCLUDED(update_mutex_);

  // Returns the SkillIdVersions of operations in order of operation addition.
  // id_version is defined by: intrinsic_proto.catalog.SkillMeta.id_version
  std::vector<std::string> GetOperationSkillIdVersions() const
      ABSL_LOCKS_EXCLUDED(update_mutex_);

  // Returns the ExecuteRequests of operations in order of operation addition.
  std::vector<intrinsic_proto::skills::ExecuteRequest> GetExecuteRequests()
      const ABSL_LOCKS_EXCLUDED(update_mutex_);

 private:
  // Adds an operation to the collection.
  absl::Status Add(std::shared_ptr<SkillExecutionOperation> operation)
      ABSL_LOCKS_EXCLUDED(update_mutex_);

  // Protects access while updates occur.
  mutable absl::Mutex update_mutex_;

  // Tracked operation names, in order of addition, so we can remove the oldest
  // finished operation whenever operations_ is full.
  std::vector<std::string> operation_names_ ABSL_GUARDED_BY(update_mutex_);
  // Map from operation name to operation. Limited in `Add` to have at most
  // kMaxNumOperations elements.
  absl::flat_hash_map<std::string, std::shared_ptr<SkillExecutionOperation>>
      operations_ ABSL_GUARDED_BY(update_mutex_);

  SkillExecutionOperationCleaner cleaner_;
};

}  // namespace internal

class SkillProjectorServiceImpl
    : public intrinsic_proto::skills::Projector::Service {
  using ObjectWorldService = ::intrinsic_proto::world::ObjectWorldService;
  using MotionPlannerService =
      ::intrinsic_proto::motion_planning::MotionPlannerService;

 public:
  // All of the given references will be kept for the lifetime of the created
  // instance.
  explicit SkillProjectorServiceImpl(
      SkillRepository& skill_repository,
      std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
      std::shared_ptr<MotionPlannerService::StubInterface>
          motion_planner_service,
      SkillRegistryClientInterface& skill_registry_client);

  grpc::Status GetFootprint(
      grpc::ServerContext* context,
      const intrinsic_proto::skills::GetFootprintRequest* request,
      intrinsic_proto::skills::GetFootprintResult* result) override;

  grpc::Status Predict(grpc::ServerContext* context,
                       const intrinsic_proto::skills::PredictRequest* request,
                       intrinsic_proto::skills::PredictResult* result) override;

 private:
  absl::StatusOr<GetFootprintRequest> ProtoToGetFootprintRequest(
      const intrinsic_proto::skills::GetFootprintRequest& request);

  std::shared_ptr<ObjectWorldService::StubInterface> object_world_service_;
  std::shared_ptr<MotionPlannerService::StubInterface> motion_planner_service_;
  SkillRepository& skill_repository_;
  SkillRegistryClientInterface& skill_registry_client_;
  absl::Mutex message_mutex_;
  google::protobuf::MessageFactory* message_factory_
      ABSL_GUARDED_BY(message_mutex_);
  absl::flat_hash_map<std::string, const google::protobuf::Message* const>
      message_prototype_by_skill_name_ ABSL_GUARDED_BY(message_mutex_);
};

class SkillExecutorServiceImpl
    : public intrinsic_proto::skills::Executor::Service {
  using ObjectWorldService = ::intrinsic_proto::world::ObjectWorldService;
  using MotionPlannerService =
      ::intrinsic_proto::motion_planning::MotionPlannerService;

 public:
  // All of the given references will be kept for the lifetime of the created
  // instance.
  explicit SkillExecutorServiceImpl(
      SkillRepository& skill_repository,
      std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
      std::shared_ptr<MotionPlannerService::StubInterface>
          motion_planner_service,
      SkillRegistryClientInterface& skill_registry_client);

  ~SkillExecutorServiceImpl() override;

  grpc::Status StartExecute(
      grpc::ServerContext* context,
      const intrinsic_proto::skills::ExecuteRequest* request,
      google::longrunning::Operation* result) override;

  grpc::Status GetOperation(
      grpc::ServerContext* context,
      const google::longrunning::GetOperationRequest* request,
      google::longrunning::Operation* result) override;

  grpc::Status CancelOperation(
      grpc::ServerContext* context,
      const google::longrunning::CancelOperationRequest* request,
      google::protobuf::Empty* result) override;

  grpc::Status WaitOperation(
      grpc::ServerContext* context,
      const google::longrunning::WaitOperationRequest* request,
      google::longrunning::Operation* result) override;

  grpc::Status ClearOperations(grpc::ServerContext* context,
                               const google::protobuf::Empty* request,
                               google::protobuf::Empty* result) override;

  // Returns a list of the executed skill id_versions in order of execution.
  // id_version is defined by: intrinsic_proto.catalog.SkillMeta.id_version
  std::vector<std::string> GetExecutedSkillIdVersions() const;

  // Returns a list of the executed skill requests in order of execution.
  std::vector<intrinsic_proto::skills::ExecuteRequest> GetExecuteRequests()
      const;

 private:
  SkillRepository& skill_repository_;
  std::shared_ptr<ObjectWorldService::StubInterface> object_world_service_;
  std::shared_ptr<MotionPlannerService::StubInterface> motion_planner_service_;
  SkillRegistryClientInterface& skill_registry_client_;
  absl::Mutex message_mutex_;
  google::protobuf::MessageFactory* message_factory_
      ABSL_GUARDED_BY(message_mutex_);
  absl::flat_hash_map<std::string, const google::protobuf::Message* const>
      message_prototype_by_skill_name_ ABSL_GUARDED_BY(message_mutex_);
  internal::SkillExecutionOperations operations_;
};

// This class implements the SkillInformation service. The skill registry can\
// query it to get information about a single skill.
class SkillInformationServiceImpl
    : public intrinsic_proto::skills::SkillInformation::Service {
 public:
  explicit SkillInformationServiceImpl(intrinsic_proto::skills::Skill skill)
      : skill_(std::move(skill)) {}
  ::grpc::Status GetSkillInfo(
      ::grpc::ServerContext* context, const google::protobuf::Empty* request,
      intrinsic_proto::skills::SkillInformationResult* result) override;

 private:
  const intrinsic_proto::skills::Skill skill_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_IMPL_H_
