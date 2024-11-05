// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/assets/services/examples/calcserver/calc_server.h"

#include <cstdint>

#include "absl/log/log.h"
#include "grpcpp/server_context.h"
#include "grpcpp/support/status.h"
#include "intrinsic/assets/services/examples/calcserver/calc_server.pb.h"
#include "intrinsic/resources/proto/runtime_context.pb.h"

namespace intrinsic::services {

grpc::Status CalculatorServiceImpl::Calculate(
    grpc::ServerContext* context,
    const intrinsic_proto::services::CalculatorRequest* request,
    intrinsic_proto::services::CalculatorResponse* response) {
  int64_t result;

  int64_t a, b;
  if (config_.reverse_order()) {
    a = request->y();
    b = request->x();
  } else {
    a = request->x();
    b = request->y();
  }

  switch (request->operation()) {
    case intrinsic_proto::services::CALCULATOR_OPERATION_ADD:
      result = a + b;
      LOG(INFO) << a << " + " << b << " = " << result;
      break;
    case intrinsic_proto::services::CALCULATOR_OPERATION_MULTIPLY:
      result = a * b;
      LOG(INFO) << a << " * " << b << " = " << result;
      break;
    case intrinsic_proto::services::CALCULATOR_OPERATION_SUBTRACT:
      result = a - b;
      LOG(INFO) << a << " - " << b << " = " << result;
      break;
    case intrinsic_proto::services::CALCULATOR_OPERATION_DIVIDE:
      if (b == 0) {
        LOG(INFO) << "Cannot divide by 0 (" << a << " / " << b << ")";
        return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT,
                            "Cannot divide by 0");
      }
      result = a / b;
      LOG(INFO) << a << " / " << b << " = " << result;
      break;
    default:
      return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT,
                          "Invalid operation");
  }
  response->set_result(result);
  return grpc::Status::OK;
}

}  // namespace intrinsic::services
