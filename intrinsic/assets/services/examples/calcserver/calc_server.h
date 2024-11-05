// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ASSETS_SERVICES_EXAMPLES_CALCSERVER_CALC_SERVER_H_
#define INTRINSIC_ASSETS_SERVICES_EXAMPLES_CALCSERVER_CALC_SERVER_H_

#include "grpcpp/server_context.h"
#include "grpcpp/support/status.h"
#include "intrinsic/assets/services/examples/calcserver/calc_server.grpc.pb.h"
#include "intrinsic/assets/services/examples/calcserver/calc_server.pb.h"
#include "intrinsic/resources/proto/runtime_context.pb.h"

namespace intrinsic::services {

// Performs basic calculator operations.
class CalculatorServiceImpl
    : public intrinsic_proto::services::Calculator::Service {
 public:
  explicit CalculatorServiceImpl(
      const intrinsic_proto::services::CalculatorConfig& config)
      : config_(config) {}

  grpc::Status Calculate(
      grpc::ServerContext* context,
      const intrinsic_proto::services::CalculatorRequest* request,
      intrinsic_proto::services::CalculatorResponse* response) override;

 private:
  intrinsic_proto::services::CalculatorConfig config_;
};

}  // namespace intrinsic::services

#endif  // INTRINSIC_ASSETS_SERVICES_EXAMPLES_CALCSERVER_CALC_SERVER_H_
