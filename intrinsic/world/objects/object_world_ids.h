// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_IDS_H_
#define INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_IDS_H_

#include <ostream>

#include "absl/strings/string_view.h"
#include "intrinsic/util/string_type.h"

namespace intrinsic {

// A unique id for a resource in the object-based world view (see ObjectWorld).
// All resources (objects and frames) share the same id-namespace.
// Treat this as an opaque value. There are no guarantees on character set,
// formatting or length.
INTRINSIC_DEFINE_STRING_TYPE_AS(ObjectWorldResourceId,
                                intrinsic::SharedPtrStringRepresentation);

// The id of the root object which is present in every object world.
const ObjectWorldResourceId& RootObjectId();

// The id of the root entity which is present in every object world.
const ObjectWorldResourceId& RootEntityId();

// A human-readable name for an object in the object-based world view
// (see ObjectWorld).
INTRINSIC_DEFINE_STRING_TYPE_AS(WorldObjectName,
                                intrinsic::SharedPtrStringRepresentation);

// The name of the root object which is present in every object world.
const WorldObjectName& RootObjectName();

enum class WorldObjectNameType {
  kNameIsNotGlobalAlias = 0,
  kNameIsGlobalAlias = 1
};

// A human-readable name for a frame in the object-based world view (see
// ObjectWorld). The name is unique amongst all frames under one object.
INTRINSIC_DEFINE_STRING_TYPE_AS(FrameName,
                                intrinsic::SharedPtrStringRepresentation);

// Frame name marking the flange of a robot arm according to the ISO 9787
// standard. This should be used by convention for flange frames on kinematic
// objects that represent a single robot arm.
// If you want to access the flange frame(s) of a kinematic object, do not use
// this constant directly. Instead, query the available flange frames via
// KinematicObject::GetIsoFlangeFrames().
const FrameName& FlangeFrameName();

// Identifies a frame marking the sensor position of objects such as cameras,
// force-torque sensors or lidars (for cameras, this is the "projection
// origin"). This frame is guaranteed to be present if the object has any type
// of sensor defined. An object cannot have more than one sensor.
const FrameName& SensorFrameName();

// Uniquely identifies a frame in the world by means of its own name and the
// name of its parent object.
struct FrameReferenceByName {
  WorldObjectName object_name;
  FrameName frame_name;

  FrameReferenceByName(const WorldObjectName& _object_name,
                       const FrameName& _frame_name)
      : object_name(_object_name), frame_name(_frame_name) {}

  friend bool operator==(const FrameReferenceByName& a,
                         const FrameReferenceByName& b) {
    return a.object_name == b.object_name && a.frame_name == b.frame_name;
  }

  friend bool operator!=(const FrameReferenceByName& a,
                         const FrameReferenceByName& b) {
    return !(a == b);
  }

  friend std::ostream& operator<<(std::ostream& strm,
                                  const FrameReferenceByName& ref) {
    return strm << "{object_name = " << ref.object_name
                << ", frame_name = " << ref.frame_name << "}";
  }
};

}  // namespace intrinsic

#endif  // INTRINSIC_WORLD_OBJECTS_OBJECT_WORLD_IDS_H_
