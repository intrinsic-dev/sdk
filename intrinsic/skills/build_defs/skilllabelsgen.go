// Copyright 2023 Intrinsic Innovation LLC

// Package skilllabelsgen implements a function for generating labels for a skill's OCI image
package skilllabelsgen

import (
	"fmt"
	"io"
	"os"
	"strings"

	log "github.com/golang/glog"
	"intrinsic/assets/idutils"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
)

// WriteLabelsToFile writes the given labels to the given file path.
func WriteLabelsToFile(labels []string, path string) error {
	content := strings.Join(labels, "\n")

	log.Infof("writing to %s", path)
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("could not create %s: %v", path, err)
	}
	if _, err := io.WriteString(f, content); err != nil {
		return fmt.Errorf("could not write to %s: %v", path, err)
	}
	if err = f.Close(); err != nil {
		return fmt.Errorf("could not close %s: %v", path, err)
	}
	return nil
}

// GenerateLabelsFromManifest generates OCI image labels given a skill manifest.
func GenerateLabelsFromManifest(m *smpb.SkillManifest) ([]string, error) {
	var err error
	var id string

	if id, err = idutils.IDFromProto(m.GetId()); err != nil {
		log.Exitf("Invalid manifest: %v", err)
	}

	return []string{fmt.Sprintf("ai.intrinsic.asset-id=%s", id)}, nil
}
