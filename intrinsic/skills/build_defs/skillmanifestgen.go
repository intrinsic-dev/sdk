// Copyright 2023 Intrinsic Innovation LLC

// main validates a skill manifest text proto and builds the binary.
package main

import (
	"fmt"
	"strings"

	"flag"
	log "github.com/golang/glog"
	"intrinsic/assets/idutils"
	"intrinsic/assets/metadatafieldlimits"
	intrinsic "intrinsic/production/intrinsic"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
	"intrinsic/util/proto/registryutil"
)

var (
	flagManifest           = flag.String("manifest", "", "Path to a SkillManifest pbtxt file.")
	flagOutput             = flag.String("output", "", "Output path.")
	flagFileDescriptorSets = flag.String("file_descriptor_sets", "", "Comma separated paths to binary file descriptor set protos.")
)

func validateManifest(m *smpb.Manifest) error {
	if err := idutils.ValidateIDProto(m.GetId()); err != nil {
		return fmt.Errorf("invalid name or package: %v", err)
	}
	if err := metadatafieldlimits.ValidateNameLength(m.GetId().GetName()); err != nil {
		return fmt.Errorf("invalid name for skill: %v", err)
	}
	if err := metadatafieldlimits.ValidateDescriptionLength(m.GetDocumentation().GetDescription()); err != nil {
		return fmt.Errorf("invalid description for skill: %v", err)
	}
	if m.GetVendor().GetDisplayName() == "" {
		return fmt.Errorf("missing vendor display name")
	}
	return nil
}

func createSkillManifest() error {
	var fds []string
	if *flagFileDescriptorSets != "" {
		fds = strings.Split(*flagFileDescriptorSets, ",")
	}
	set, err := registryutil.LoadFileDescriptorSets(fds)
	if err != nil {
		return fmt.Errorf("unable to build FileDescriptorSet: %v", err)
	}

	types, err := registryutil.NewTypesFromFileDescriptorSet(set)
	if err != nil {
		return fmt.Errorf("failed to populate the registry: %v", err)
	}

	m := new(smpb.Manifest)
	if err := protoio.ReadTextProto(*flagManifest, m, protoio.WithResolver(types)); err != nil {
		return fmt.Errorf("failed to read manifest: %v", err)
	}
	if err := validateManifest(m); err != nil {
		return err
	}
	if err := protoio.WriteBinaryProto(*flagOutput, m, protoio.WithDeterministic(true)); err != nil {
		return fmt.Errorf("could not write skill manifest proto: %v", err)
	}
	return nil
}

func main() {
	intrinsic.Init()
	if err := createSkillManifest(); err != nil {
		log.Exitf("Failed to create skill manifest: %v", err)
	}
}
