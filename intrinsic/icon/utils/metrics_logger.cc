// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/metrics_logger.h"

#include <cstddef>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "google/protobuf/struct.pb.h"
#include "intrinsic/logging/data_logger_client.h"
#include "intrinsic/logging/proto/log_item.pb.h"
#include "intrinsic/performance/analysis/proto/performance_metrics.pb.h"
#include "intrinsic/platform/common/buffers/realtime_write_queue.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

using intrinsic_proto::data_logger::LogItem;
using intrinsic_proto::performance::analysis::proto::PerformanceMetrics;

namespace intrinsic::icon {

static constexpr std::size_t kRtQueueSize = 1000;

MetricsLogger::~MetricsLogger() {
  if (metrics_publisher_thread_.Joinable()) {
    shutdown_requested_.store(true);
    metrics_publisher_thread_.Join();
  }
}

absl::Status MetricsLogger::Start() {
  if (metrics_publisher_thread_.Joinable()) {
    return absl::FailedPreconditionError(
        "Metrics publisher thread is already running");
  }

  intrinsic::ThreadOptions options;
  options.SetNormalPriorityAndScheduler();
  options.SetName("metrics_publisher_thread_");
  shutdown_requested_.store(false);
  INTR_RETURN_IF_ERROR(
      metrics_publisher_thread_.Start(options, [this]() { LoggerFunction(); }));

  return absl::OkStatus();
}
void MetricsLogger::LoggerFunction() {
  // Read the queue until empty
  while (!shutdown_requested_.load()) {
    // Build performance metrics log
    LogItem log_item = BuildMetricsLog();
  }
}

// Helper functions to build performance metrics proto
void InsertNumericField(PerformanceMetrics& perf_metrics,
                        std::string field_name, double field_value) {
  google::protobuf::Value field_value_proto;
  field_value_proto.set_number_value(field_value);
  perf_metrics.mutable_metrics()->mutable_metrics()->mutable_fields()->insert(
      std::make_pair(field_name, field_value_proto));
}

void InsertStringField(PerformanceMetrics& perf_metrics, std::string field_name,
                       std::string field_value) {
  google::protobuf::Value field_value_proto;
  field_value_proto.set_string_value(field_value);
  perf_metrics.mutable_metrics()->mutable_metrics()->mutable_fields()->insert(
      std::make_pair(field_name, field_value_proto));
}

LogItem MetricsLogger::BuildMetricsLog() {}

}  // namespace intrinsic::icon
