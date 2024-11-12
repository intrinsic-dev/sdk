// Copyright 2023 Intrinsic Innovation LLC

// Package main implements a CLI to generate labels for a skill's OCI image.
package main

import (
	"fmt"

	"flag"
	log "github.com/golang/glog"
	intrinsic "intrinsic/production/intrinsic"
	slg "intrinsic/skills/build_defs/skilllabelsgen"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
)

var (
	flagManifest = flag.String("manifest", "", "Filename for the binary skill manifest proto.")
	flagOutput   = flag.String("output", "", "Output filename.")
)

func checkArguments() error {
	if len(*flagManifest) == 0 {
		return fmt.Errorf("--manifest is required")
	}
	if len(*flagOutput) == 0 {
		return fmt.Errorf("--output is required")
	}
	return nil
}

func main() {
	intrinsic.Init()
	// Fail fast if CLI arguments are invalid.
	if err := checkArguments(); err != nil {
		log.Exitf("Invalid arguments: %v", err)
	}

	var err error
	var labels []string

	m := new(smpb.SkillManifest)
	if err := protoio.ReadBinaryProto(*flagManifest, m); err != nil {
		log.Exitf("failed to read manifest: %v", err)
	}

	if labels, err = slg.GenerateLabelsFromManifest(m); err != nil {
		log.Exitf("Unable to generate labes from manifest: %v", err)
	}

	if err = slg.WriteLabelsToFile(labels, *flagOutput); err != nil {
		log.Exitf("Unable to write %v to file %v: %v", labels, *flagOutput, err)
	}
}
