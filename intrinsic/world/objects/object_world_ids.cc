// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/world/objects/object_world_ids.h"

namespace intrinsic {

const ObjectWorldResourceId& RootObjectId() {
  static const ObjectWorldResourceId* kRootObjectId =
      new ObjectWorldResourceId("root");
  return *kRootObjectId;
}

const ObjectWorldResourceId& RootEntityId() {
  static const ObjectWorldResourceId* kRootEntityId =
      new ObjectWorldResourceId("eid_root");
  return *kRootEntityId;
}

const WorldObjectName& RootObjectName() {
  static const WorldObjectName* kRootObjectName = new WorldObjectName("root");
  return *kRootObjectName;
}

const FrameName& FlangeFrameName() {
  static const FrameName* kFlangeFrameName = new FrameName("flange");
  return *kFlangeFrameName;
}

const FrameName& SensorFrameName() {
  static const FrameName* kSensorFrameName = new FrameName("sensor");
  return *kSensorFrameName;
}

}  // namespace intrinsic
