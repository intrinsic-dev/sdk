// Copyright 2023 Intrinsic Innovation LLC

// Main implements the main CLI for generating a SkillServiceConfig file
package main

import (
	"fmt"

	"flag"
	log "github.com/golang/glog"
	intrinsic "intrinsic/production/intrinsic"
	sscg "intrinsic/skills/build_defs/skillserviceconfiggen"
)

var (
	flagManifestPbbinFilename   = flag.String("manifest_pbbin_filename", "", "Filename for the binary skill manifest proto.")
	flagProtoDescriptorFilename = flag.String("proto_descriptor_filename", "", "Filename for FileDescriptorSet for skill parameter, return value and published topic protos.")
	flagOutputConfigFilename    = flag.String("output_config_filename", "", "Output filename.")
)

func checkArguments() error {
	if len(*flagManifestPbbinFilename) == 0 {
		return fmt.Errorf("--manifest_pbbin_filename is required")
	}
	if len(*flagProtoDescriptorFilename) == 0 {
		return fmt.Errorf("--proto_descriptor_filename is required")
	}
	if len(*flagProtoDescriptorFilename) == 0 {
		return fmt.Errorf("--output_config_filename is required")
	}
	return nil
}

func main() {
	intrinsic.Init()
	// Fail fast if CLI arguments are invalid.
	if err := checkArguments(); err != nil {
		log.Exitf("Invalid arguments: %v", err)
	}
	if err := sscg.GenerateSkillServiceConfig(*flagManifestPbbinFilename, *flagProtoDescriptorFilename, *flagOutputConfigFilename); err != nil {
		log.Exitf("Unable to generate SkillServiceConfig: %v", err)
	}
}
