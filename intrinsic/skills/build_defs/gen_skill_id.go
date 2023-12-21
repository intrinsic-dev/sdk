// Copyright 2023 Intrinsic Innovation LLC

package main

import (
	"fmt"

	"flag"
	log "github.com/golang/glog"
	intrinsic "intrinsic/production/intrinsic"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
)

var (
	flagManifest = flag.String("manifest_pbbin_filename", "", "Path to the manifest binary proto file.")
	flagOutput   = flag.String("output_pbbin_filename", "", "Path to file to write prototext id out to.")
)

func genSkillIDFile() error {
	m := new(smpb.Manifest)
	if err := protoio.ReadBinaryProto(*flagManifest, m); err != nil {
		return fmt.Errorf("failed to read manifest: %v", err)
	}
	log.Infof("writing: %v to: %s", m.GetId(), *flagOutput)
	if err := protoio.WriteBinaryProto(*flagOutput, m.GetId(), protoio.WithDeterministic(true)); err != nil {
		return fmt.Errorf("could not write skill ID proto: %v", err)
	}
	return nil
}

func main() {
	intrinsic.Init()
	if err := genSkillIDFile(); err != nil {
		log.Exitf("Failed generate skill ID filet: %v", err)
	}
}
