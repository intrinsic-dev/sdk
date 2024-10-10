// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_SERVER_ICON_API_SERVICE_H_
#define INTRINSIC_ICON_SERVER_ICON_API_SERVICE_H_

#include "intrinsic/icon/proto/service.grpc.pb.h"

namespace intrinsic::icon {

class IconApiService : public intrinsic_proto::icon::IconApi::Service {
 public:
  // Tries to cancel all grpc streams.
  // Does not block. It is not guaranteed that all streams and sessions
  // shut down.
  virtual void TryCancel() {};
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_SERVER_ICON_API_SERVICE_H_
