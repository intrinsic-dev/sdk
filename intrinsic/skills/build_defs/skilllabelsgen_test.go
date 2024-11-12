// Copyright 2023 Intrinsic Innovation LLC

// Package skilllabelsgen_test tests the skilllabelsgen library.
package skilllabelsgen_test

import (
	"os"
	"path/filepath"
	"reflect"
	"testing"

	slg "intrinsic/skills/build_defs/skilllabelsgen"
	smpb "intrinsic/skills/proto/skill_manifest_go_proto"
	"intrinsic/util/proto/protoio"
	runfiles2 "intrinsic/util/runfiles"
)

const (
	ccManifestFilename = "intrinsic/skills/build_defs/tests/no_op_skill_cc_manifest.pbbin"
	pyManifestFilename = "intrinsic/skills/build_defs/tests/no_op_skill_py_manifest.pbbin"
)

func mustHaveRunfile(t *testing.T, p string) string {
	t.Helper()
	rp, err := runfiles2.Rlocation(p)
	if err != nil {
		t.Fatalf("Unable to access runfile %v: %v", p, err)
	}
	return rp
}

func TestGenerateLabels(t *testing.T) {
	tests := []struct {
		desc             string
		manifestFilename string
		outputFilename   string
		wantLabels       []string
	}{
		{
			desc:             "CC no op manifest",
			manifestFilename: mustHaveRunfile(t, ccManifestFilename),
			outputFilename:   "output_cc_labels.txt",
			wantLabels:       []string{"ai.intrinsic.asset-id=ai.intrinsic.no_op"},
		},
		{
			desc:             "Py no op manifest",
			manifestFilename: mustHaveRunfile(t, pyManifestFilename),
			outputFilename:   "output_py_labels.txt",
			wantLabels:       []string{"ai.intrinsic.asset-id=ai.intrinsic.no_op"},
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			m := new(smpb.SkillManifest)
			if err := protoio.ReadBinaryProto(tc.manifestFilename, m); err != nil {
				t.Fatalf("failed to read manifest: %v", err)
			}

			var labels []string
			var err error
			if labels, err = slg.GenerateLabelsFromManifest(m); err != nil {
				t.Fatalf("Unable to generate labes from manifest: %v", err)
			}

			if got, want := labels, tc.wantLabels; !reflect.DeepEqual(got, want) {
				t.Errorf("got: %v want %v", got, want)
			}
		})
	}
}

func TestWriteLabelsToFile(t *testing.T) {
	outputFilename := filepath.Join(t.TempDir(), "output_labels.txt")
	givenLabels := []string{"a=b", "foo=bar"}
	if err := slg.WriteLabelsToFile(givenLabels, outputFilename); err != nil {
		t.Fatalf("WriteLabelsToFile(%v, %v) failed: %v", givenLabels, outputFilename, err)
	}

	content, err := os.ReadFile(outputFilename)
	if err != nil {
		t.Fatalf("Unable to read output file %v: %v", outputFilename, err)
	}

	if got, want := string(content), "a=b\nfoo=bar"; got != want {
		t.Errorf("got %v want %v", got, want)
	}
}
