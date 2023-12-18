// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/cc/skill_interface_utils.h"

#include <algorithm>
#include <memory>
#include <optional>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/time/time.h"
#include "google/protobuf/message.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/execute_context_view.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/world/proto/object_world_updates.pb.h"

namespace intrinsic {
namespace skills {

absl::StatusOr<std::unique_ptr<::google::protobuf::Message>> PreviewViaExecute(
    SkillExecuteInterface& skill, const PreviewRequest& request,
    PreviewContext& context) {
  EquipmentPack equipment;

  INTR_ASSIGN_OR_RETURN(ExecuteRequest execute_request,
                        PreviewToExecuteRequest(request));
  INTR_ASSIGN_OR_RETURN(ExecuteContextView execute_context,
                        PreviewToExecuteContext(context, equipment));

  return skill.Execute(execute_request, execute_context);
}

absl::StatusOr<ExecuteRequest> PreviewToExecuteRequest(
    const PreviewRequest& request) {
  return ExecuteRequest(
      /*params=*/request.params_any(),
      /*param_defaults=*/std::nullopt);
}

absl::StatusOr<ExecuteContextView> PreviewToExecuteContext(
    PreviewContext& context, const EquipmentPack& equipment) {
  return ExecuteContextView(context.canceller(), equipment,
                            context.logging_context(), context.motion_planner(),
                            context.object_world());
}

}  // namespace skills
}  // namespace intrinsic
