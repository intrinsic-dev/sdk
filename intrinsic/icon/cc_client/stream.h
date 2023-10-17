// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CC_CLIENT_STREAM_H_
#define INTRINSIC_ICON_CC_CLIENT_STREAM_H_

#include <memory>
#include <optional>
#include <utility>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "grpcpp/client_context.h"
#include "grpcpp/support/sync_stream.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/service.grpc.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon {

// A StreamWriter is a typed communication endpoint for writing to a streaming
// input of an Action.
// Not thread-safe.
template <class T>
class StreamWriterInterface {
 public:
  virtual ~StreamWriterInterface() = default;

  // Writes `value` to the Action input stream associated with this
  // StreamWriter.
  virtual absl::Status Write(const T& value) = 0;
};

namespace internal {

class GenericStreamWriter {
 public:
  GenericStreamWriter(std::unique_ptr<::grpc::ClientContext> channel_context,
                      std::unique_ptr<::grpc::ClientReaderWriterInterface<
                          intrinsic_proto::icon::OpenWriteStreamRequest,
                          intrinsic_proto::icon::OpenWriteStreamResponse>>
                          grpc_stream)
      : channel_context_(std::move(channel_context)),
        grpc_stream_(std::move(grpc_stream)) {}
  ~GenericStreamWriter();
  GenericStreamWriter(GenericStreamWriter&&) = default;
  GenericStreamWriter& operator=(GenericStreamWriter&&) = default;

  absl::Status OpenStreamWriter(SessionId session_id,
                                ActionInstanceId action_instance_id,
                                absl::string_view input_name);
  absl::Status WriteToStream(const google::protobuf::Message& value);
  absl::Status FinishIfNeeded();

 private:
  std::unique_ptr<::grpc::ClientContext> channel_context_;
  std::unique_ptr<::grpc::ClientReaderWriterInterface<
      intrinsic_proto::icon::OpenWriteStreamRequest,
      intrinsic_proto::icon::OpenWriteStreamResponse>>
      grpc_stream_;
  // If set, gprc_stream_ must not be used.
  std::optional<absl::Status> finish_status_;
};

template <class T>
class StreamWriter : public StreamWriterInterface<T> {
 public:
  explicit StreamWriter(std::unique_ptr<GenericStreamWriter> stream_writer)
      : stream_writer_(std::move(stream_writer)) {}

  static absl::StatusOr<std::unique_ptr<StreamWriter<T>>> Open(
      SessionId session_id, ActionInstanceId action_instance_id,
      absl::string_view input_name,
      intrinsic_proto::icon::IconApi::StubInterface* stub,
      const ClientContextFactory& client_context_factory = nullptr) {
    std::unique_ptr<::grpc::ClientContext> context;
    if (client_context_factory) {
      context = client_context_factory();
    } else {
      context = std::make_unique<::grpc::ClientContext>();
    }
    auto grpc_stream = stub->OpenWriteStream(context.get());
    auto generic_stream_writer = std::make_unique<GenericStreamWriter>(
        std::move(context), std::move(grpc_stream));
    auto stream_writer =
        std::make_unique<::intrinsic::icon::internal::StreamWriter<T>>(
            std::move(generic_stream_writer));
    INTRINSIC_RETURN_IF_ERROR(stream_writer->stream_writer_->OpenStreamWriter(
        session_id, action_instance_id, input_name));
    return stream_writer;
  }

  absl::Status Write(const T& value) override {
    return stream_writer_->WriteToStream(value);
  }

 private:
  std::unique_ptr<GenericStreamWriter> stream_writer_;
};

}  // namespace internal
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CC_CLIENT_STREAM_H_
