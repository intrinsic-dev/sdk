// Copyright 2023 Intrinsic Innovation LLC

package main

import (
	"fmt"
	"io"
	"os"

	"flag"
	log "github.com/golang/glog"
	"intrinsic/assets/idutils"
	intrinsic "intrinsic/production/intrinsic"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
)

var (
	flagManifest = flag.String("manifest_pbbin_filename", "", "Path to the manifest binary proto file.")
	flagOutID    = flag.String("out_id_filename", "", "Path to file to which to write the skills' ID.")
)

func writeToFile(path string, content string) error {
	log.Infof("writing to %s", path)
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("could not create %s: %v", path, err)
	}
	if _, err := io.WriteString(f, content); err != nil {
		return fmt.Errorf("could not write to %s: %v", path, err)
	}
	err = f.Close()
	if err != nil {
		return fmt.Errorf("could not close %s: %v", path, err)
	}
	return nil
}

func genSkillIDFile() error {
	m := new(smpb.Manifest)
	if err := protoio.ReadBinaryProto(*flagManifest, m); err != nil {
		return fmt.Errorf("failed to read manifest: %v", err)
	}

	id, err := idutils.IDFromProto(m.GetId())
	if err != nil {
		return fmt.Errorf("invalid skill ID: %v", err)
	}
	if err := writeToFile(*flagOutID, id); err != nil {
		return err
	}

	return nil
}

func main() {
	intrinsic.Init()
	if err := genSkillIDFile(); err != nil {
		log.Exitf("Failed generate skill ID file: %v", err)
	}
}
