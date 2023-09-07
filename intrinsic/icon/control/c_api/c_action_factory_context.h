// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_ACTION_FACTORY_CONTEXT_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_ACTION_FACTORY_CONTEXT_H_

#include <stdint.h>

#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_types.h"

#ifdef __cplusplus
extern "C" {
#endif

static constexpr size_t kXfaIconMaxStreamingOutputSizeBytes = 102400;

////////////////////////////////
// Streaming Input functions. //
////////////////////////////////

// Used for opaque pointers to streaming input values (i.e. the output type
// of the parser function).
struct XfaIconStreamingInputType;

// Used for opaque pointers to streaming input parser callbacks. This is not a
// function pointer typedef because these parsers frequently are std::functions
// or lambdas with captures, i.e. can not be converted to a single function
// pointer.
struct XfaIconStreamingInputParserFn;

// Bundles a parser callback pointer with its invoke and destroy function
// pointers.
struct XfaIconStreamingInputParserFnInstance {
  XfaIconStreamingInputParserFn* self;
  // Invokes an InputReceiver parser. `proto_input` is a serialized
  // google::protobuf::Any proto.
  //
  // The caller owns `self` and `proto_input`.
  //
  // Writes a pointer to an XfaIconStreamingInputType to `parsed_input_out` on
  // success. The caller assumes ownership of that pointer and must call
  // `destroy_input` on it.
  //
  // Writes an XfaIconRealtimeStatus to `status_out` in case of an error (i.e.
  // when the return value is nullptr);
  XfaIconStreamingInputType* (*invoke)(XfaIconStreamingInputParserFn* self,
                                       XfaIconStringView proto_input,
                                       XfaIconRealtimeStatus* status_out);

  // Destroys the InputReceiver callback function `self`. Safe to call on
  // nullptr.
  void (*destroy)(XfaIconStreamingInputParserFn* self);
  // Destroys the parsed streaming input `self`. Safe to call on nullptr.
  void (*destroy_input)(XfaIconStreamingInputType* self);
};

////////////////////////////////
// Streaming Output functions. //
////////////////////////////////

// Used for opaque pointers to streaming output values (i.e. the input type
// of the converter function).
struct XfaIconStreamingOutputType;

// Used for opaque pointers to streaming output parser callbacks. This is not a
// function pointer typedef because these parsers frequently are std::functions
// or lambdas with captures, i.e. can not be converted to a single function
// pointer.
struct XfaIconStreamingOutputConverterFn;

// Bundles a parser callback pointer with its invoke and destroy function
// pointers.
struct XfaIconStreamingOutputConverterFnInstance {
  XfaIconStreamingOutputConverterFn* self;
  XfaIconStringDestroy destroy_string;
  // Invokes a streaming output converter. `realtime_output` is an opaque
  // pointer to the realtime output data. `realtime_output_size` indicates how
  // far beyond `realtime_output` the converter is allowed to read.
  //
  // Writes to `result_status_out` to indicate success or failure.
  //
  // Returns a pointer to a serialized ::google::protobuf::Any proto to
  // `output_proto_buffer_out`. The caller assumes ownership of that buffer
  // *regardless of the value of `result_status_out`* and is responsible for
  // deleting it via a call to XfaIconStringDestroy (see c_types.h).
  // Specifically, to ensure memory safety, the caller must use `destroy_string`
  // above.
  XfaIconString* (*invoke)(
      XfaIconStreamingOutputConverterFn* self,
      const XfaIconStreamingOutputType* realtime_output_buffer,
      const size_t realtime_output_size,
      XfaIconRealtimeStatus* result_status_out);

  // Destroys the IutputReceiver callback function `self`.
  void (*destroy)(XfaIconStreamingOutputConverterFn* self);
};

struct XfaIconSlotInfo {
  uint64_t realtime_slot_id;
  // Contains a serialized intrinsic_proto.icon.PartConfig proto message. Make
  // sure to delete this using the corresponding
  // XfaconActionFactoryContextVtable's `destroy_string` function.
  XfaIconString* part_config_buffer;
};

struct XfaIconActionFactoryContext;

struct XfaIconActionFactoryContextVtable {
  XfaIconStringDestroy destroy_string;
  // Returns a pointer to a string-serialized
  // ::intrinsic_proto::icon::ServerConfig proto, and sets `proto_size_out` to
  // indicate its size. Caller takes ownership of the returned pointer, but must
  // only destroy it using `destroy_string`.
  XfaIconString* (*server_config)(const XfaIconActionFactoryContext* self);
  // Tries to find SlotInfo for `slot_name`, and writes it into `slot_info_out`
  // on success.
  // Caller assumes ownership of the proto char buffer inside of
  // XfaIconSlotInfo, and must take care to destroy it using `destroy_string`.
  // Returns an IconRealtimeStatus to indicate success or failure
  // (`slot_info_out` is invalid on anything but an OK return value).
  XfaIconRealtimeStatus (*get_slot_info)(XfaIconActionFactoryContext* self,
                                         XfaIconStringView slot_name,
                                         XfaIconSlotInfo* slot_info_out);

  // Registers `parser` to convert data for the streaming input `input_name`
  // from a ::google::protobuf::Any proto to the Action's realtime input type.
  // Takes ownership of `parser`, i.e. will call its `destroy` method when
  // appropriate.
  //
  // On success, this function writes the StreamingInputId for the input to
  // `streaming_input_id_out`,
  //
  // Actions can use `streaming_output_id_out` to access streaming input values
  // in realtime functions.
  //
  // Returns an error if there's already a streaming input parser registered for
  // `input_name`.
  //
  // Returns an error if `input_proto_message_type_name` does not match the name
  // of the proto message type for `input_name` in this Action's signature.
  //
  // NOTE: It is an error for the factory to not register parsers for *all*
  // streaming inputs in its Action's signature!
  XfaIconRealtimeStatus (*add_streaming_input_parser)(
      XfaIconActionFactoryContext* self, XfaIconStringView input_name,
      XfaIconStringView input_proto_message_type_name,
      XfaIconStreamingInputParserFnInstance parser,
      uint64_t* streaming_input_id_out);

  // Registers `converter` to convert data for the Action's streaming output
  // from its realtime data type to a ::google::protobuf::Any message. The
  // realtime data type must have a known size (`realtime_type_size`) that
  // cannot be larger than kXfaIconMaxStreamingOutputSizeBytes.
  //
  // `output_proto_message_type_name` is the full name (obtained via
  // `MyProtoMessage::GetDescriptor()->full_name()`) of the message type
  // *inside* the Any proto.
  //
  // Returns an error if `output_proto_message_type_name` does not match the
  // output message type in the Action type's signature.
  //
  // Returns an error if called more than once.
  //
  // NOTE: It is an error for the factory to not register a converter if there
  // is a streaming output in its Action's signature!
  XfaIconRealtimeStatus (*add_streaming_output_converter)(
      XfaIconActionFactoryContext* self,
      XfaIconStringView output_proto_message_type_name,
      size_t realtime_type_size,
      XfaIconStreamingOutputConverterFnInstance converter);
};

#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_ACTION_FACTORY_CONTEXT_H_
