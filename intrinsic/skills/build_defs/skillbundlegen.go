// Copyright 2023 Intrinsic Innovation LLC

// Package skillbundlegen creates a skill bundle.
package main

import (
	"fmt"

	"flag"
	log "github.com/golang/glog"
	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"intrinsic/assets/bundleio"
	"intrinsic/assets/idutils"
	intrinsic "intrinsic/production/intrinsic"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
)

var (
	flagFileDescriptorSet = flag.String("file_descriptor_set", "", "File descriptor set.")
	flagImageTar          = flag.String("image_tar", "", "Skill image file.")
	flagPBT               = flag.String("pbt", "", "Parameterized behavior tree file.")
	flagManifest          = flag.String("manifest", "", "Skill manifest.")

	flagOutputBundle = flag.String("output_bundle", "", "Output path.")
)

func validateManifest(m *smpb.SkillManifest) error {
	if err := idutils.ValidateIDProto(m.GetId()); err != nil {
		return fmt.Errorf("invalid name or package: %v", err)
	}
	if m.GetVendor().GetDisplayName() == "" {
		return fmt.Errorf("vendor.display_name must be specified")
	}
	return nil
}

func main() {
	intrinsic.Init()

	m := new(smpb.SkillManifest)
	if err := protoio.ReadBinaryProto(*flagManifest, m); err != nil {
		log.Exitf("failed to read manifest: %v", err)
	}

	if err := validateManifest(m); err != nil {
		log.Exitf("invalid manifest: %v", err)
	}

	fds := &descriptorpb.FileDescriptorSet{}
	if err := protoio.ReadBinaryProto(*flagFileDescriptorSet, fds); err != nil {
		log.Exitf("failed to read file descriptor set: %v", err)
	}

	if err := bundleio.WriteSkill(*flagOutputBundle, bundleio.WriteSkillOpts{
		Manifest:    m,
		Descriptors: fds,
		ImageTar:    *flagImageTar,
		PBT:         *flagPBT,
	}); err != nil {
		log.Exitf("unable to write skill bundle: %v", err)
	}
}
