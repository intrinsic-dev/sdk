// Copyright 2023 Intrinsic Innovation LLC

#include <cstddef>
#include <iostream>
#include <ostream>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/descriptor.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/icon/proto/io_block.pb.h"
#include "intrinsic/icon/proto/part_status.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080",
          "Address of the ICON Application Layer Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_FLAG(std::string, header, "x-icon-instance-name",
          "Optional header name to be used to select a specific ICON instance. "
          " Has no effect if --instance is not set");

ABSL_FLAG(bool, print_part_config, false,
          "Also prints the GenericPartConfig for every part.");

const char kUsage[] =
    "Lists the available Parts, then the available Actions (including the "
    "compatible Parts for each), and finally the current PartStatus for each "
    "Part.";

namespace {

// Custom printing methods, because the messages contain FileDescriptorSets,
// which result in very long DebugString() representations without giving much
// information to a human reader.
std::string PrettyPrintParameterInfo(
    const intrinsic_proto::icon::ActionSignature::ParameterInfo&
        parameter_info) {
  std::stringstream sstream;
  sstream << "Parameter name: " << parameter_info.parameter_name() << "\n";
  sstream << "Description: " << parameter_info.text_description() << "\n";
  sstream << "Type: " << parameter_info.value_message_type() << "\n";
  return sstream.str();
}

std::string PrettyPrintStateVariableInfo(
    const intrinsic_proto::icon::ActionSignature::StateVariableInfo&
        state_variable_info) {
  std::stringstream sstream;
  sstream
      << state_variable_info.state_variable_name() << " ("
      << intrinsic_proto::icon::ActionSignature::StateVariableInfo::Type_Name(
             state_variable_info.type())
      << ")\n";
  sstream << "  " << state_variable_info.text_description() << "\n";
  return sstream.str();
}

std::string PrettyPrintActionSignature(
    const intrinsic_proto::icon::ActionSignature& action_signature) {
  std::stringstream sstream;
  sstream << "Action type name: " << action_signature.action_type_name()
          << "\n";
  sstream << "Description: " << action_signature.text_description() << "\n";
  sstream << "\n";
  if (action_signature.fixed_parameters_message_type().empty()) {
    sstream << "Does not take parameters.\n";
  } else {
    sstream << "Parameter type: "
            << action_signature.fixed_parameters_message_type() << "\n";
  }
  sstream << "\n";
  if (action_signature.streaming_input_infos().empty()) {
    sstream << "Does not take streaming inputs.\n";
  } else {
    sstream << "Streaming Inputs:\n";
    for (const auto& streaming_input_info :
         action_signature.streaming_input_infos()) {
      sstream << PrettyPrintParameterInfo(streaming_input_info);
    }
  }
  sstream << "\n";
  if (!action_signature.has_streaming_output_info()) {
    sstream << "Does not provide a streaming output.\n";
  } else {
    sstream << "Streaming Output:\n";
    sstream << PrettyPrintParameterInfo(
        action_signature.streaming_output_info());
  }
  sstream << "\n";
  sstream << "State Variables:\n";
  for (const auto& state_variable_info :
       action_signature.state_variable_infos()) {
    sstream << PrettyPrintStateVariableInfo(state_variable_info);
  }
  sstream << "\n";
  sstream << "Slots:\n";
  for (const auto& [slot_name, slot_info] :
       action_signature.part_slot_infos()) {
    sstream << "  " << slot_name << "\n";
    sstream << "    Description: " << slot_info.description() << "\n";
    sstream << "    Required feature interfaces:" << "\n";
    if (slot_info.required_feature_interfaces().empty()) {
      sstream << "      (none)\n";
    } else {
      for (int fi : slot_info.required_feature_interfaces()) {
        sstream << "      "
                << intrinsic_proto::icon::FeatureInterfaceTypes_Name(fi)
                << "\n";
      }
    }
    if (!slot_info.optional_feature_interfaces().empty()) {
      sstream << "    Optional feature interfaces:" << "\n";
      for (int fi : slot_info.optional_feature_interfaces()) {
        sstream << "      "
                << intrinsic_proto::icon::FeatureInterfaceTypes_Name(fi)
                << "\n";
      }
    }
  }
  return sstream.str();
}

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params) {
  if (connection_params.address.empty()) {
    return absl::FailedPreconditionError("`--server` must not be empty.");
  }

  INTR_ASSIGN_OR_RETURN(auto icon_channel,
                        intrinsic::icon::Channel::Make(connection_params));
  intrinsic::icon::Client client(icon_channel);

  INTR_ASSIGN_OR_RETURN(std::vector<std::string> parts, client.ListParts());
  INTR_ASSIGN_OR_RETURN(const auto config, client.GetConfig());

  {
    std::stringstream sstream;
    sstream << "Available Parts:\n";
    for (const auto& part : parts) {
      sstream << "  " << part << "\n";
      sstream << "    Supported feature interfaces:\n";
      INTR_ASSIGN_OR_RETURN(
          std::vector<intrinsic_proto::icon::FeatureInterfaceTypes>
              feature_interfaces,
          config.GetPartFeatureInterfaces(part));
      if (feature_interfaces.empty()) {
        sstream << "      (none)\n";
      } else {
        for (const intrinsic_proto::icon::FeatureInterfaceTypes fi :
             feature_interfaces) {
          const google::protobuf::EnumDescriptor* descriptor =
              intrinsic_proto::icon::FeatureInterfaceTypes_descriptor();
          sstream << "      " << descriptor->FindValueByNumber(fi)->name()
                  << "\n";
        }
      }
    }
    std::cout << "\n" << sstream.str() << std::endl;
  }

  if (absl::GetFlag(FLAGS_print_part_config)) {
    std::stringstream sstream;
    for (const auto& part : parts) {
      sstream << "GenericPartConfig for part '" << part << "':\n"
              << absl::StrCat(*config.GetGenericPartConfig(part)) << "\n";
    }
    std::cout << "\n" << sstream.str() << std::endl;
  }

  INTR_ASSIGN_OR_RETURN(
      std::vector<intrinsic_proto::icon::ActionSignature> action_signatures,
      client.ListActionSignatures());
  std::cout << "Available Actions:";
  for (const auto& signature : action_signatures) {
    INTR_ASSIGN_OR_RETURN(
        std::vector<std::string> compatible_parts,
        client.ListCompatibleParts({signature.action_type_name()}));
    std::stringstream sstream;
    if (compatible_parts.empty()) {
      sstream << "No compatible Parts\n";
    } else {
      sstream << "Compatible Parts:\n";
      for (const auto& part : compatible_parts) {
        sstream << "  " << part;
      }
    }
    std::cout << std::endl
              << PrettyPrintActionSignature(signature) << std::endl
              << sstream.str() << std::endl
              << std::endl;
  }

  INTR_ASSIGN_OR_RETURN(intrinsic_proto::icon::GetStatusResponse status,
                        client.GetStatus());

  for (const auto& part : parts) {
    auto part_status_it = status.part_status().find(part);
    if (part_status_it == status.part_status().end()) {
      return absl::NotFoundError(
          absl::StrCat("No PartStatus for Part '", part, "'"));
    }
    std::cout << "Status for Part '" << part << "'";
    if (!part_status_it->second.joint_states().empty()) {
      std::cout << "  Joint positions:" << std::endl;
      for (size_t i = 0; i < part_status_it->second.joint_states_size(); ++i) {
        const intrinsic_proto::icon::PartJointState& joint_state =
            part_status_it->second.joint_states(i);
        std::cout << "    J" << i << ": "
                  << absl::StrFormat("%6.3f", joint_state.position_sensed())
                  << std::endl;
      }

      // If there are joint states, there is also a cartesian base_t_tip pose
      const intrinsic_proto::icon::Transform& base_t_tip =
          part_status_it->second.base_t_tip_sensed();
      std::cout << "  base_T_tip:" << std::endl
                << "    x: " << absl::StrFormat("%6.3f", base_t_tip.pos().x())
                << std::endl
                << "    y: " << absl::StrFormat("%6.3f", base_t_tip.pos().y())
                << std::endl
                << "    z: " << absl::StrFormat("%6.3f", base_t_tip.pos().z())
                << std::endl
                << "   qw: " << absl::StrFormat("%6.3f", base_t_tip.rot().qw())
                << std::endl
                << "   qx: " << absl::StrFormat("%6.3f", base_t_tip.rot().qx())
                << std::endl
                << "   qy: " << absl::StrFormat("%6.3f", base_t_tip.rot().qy())
                << std::endl
                << "   qz: " << absl::StrFormat("%6.3f", base_t_tip.rot().qz())
                << std::endl;
    }
    // PartStatus can also hold a gripper state.
    if (part_status_it->second.has_gripper_state()) {
      std::cout << "  gripper state: " << std::endl
                << "    "
                << intrinsic_proto::icon::GripperState::SensedState_Name(
                       part_status_it->second.gripper_state().sensed_state())
                << std::endl;
    }
    // PartStatus can also hold the state of analog-/digial IOs.
    if (part_status_it->second.has_adio_state()) {
      std::cout << "  ADIO state: " << std::endl
                << absl::StrCat(part_status_it->second.adio_state())
                << std::endl;
    }

    // PartStatus can also hold the currently active control mode.
    if (part_status_it->second.has_current_control_mode()) {
      std::cout << "  Control Mode: "
                << PartControlMode_Name(
                       part_status_it->second.current_control_mode())
                << std::endl;
    }
  }

  if (status.has_safety_status()) {
    std::cout << "SafetyStatus:" << std::endl
              << absl::StrCat(status.safety_status()) << std::endl;
  }

  std::cout << "Sessions:" << std::endl;
  for (const auto& session : status.sessions()) {
    std::cout << "Session ID " << session.first << ":"
              << absl::StrCat(session.second) << std::endl;
  }

  return absl::OkStatus();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(kUsage, argc, argv);
  QCHECK_OK(Run(intrinsic::icon::ConnectionParams{
      .address = absl::GetFlag(FLAGS_server),
      .instance_name = absl::GetFlag(FLAGS_instance),
      .header = absl::GetFlag(FLAGS_header),
  }));
  return 0;
}
