// Copyright 2023 Intrinsic Innovation LLC

// Package runfiles provides functionality to access runfiles
package runfiles

import (
	"fmt"
	"io/fs"
	"path"

	"github.com/bazelbuild/rules_go/go/runfiles"
)

// Rlocation gets the runfiles location of a file.
//
// Use the typical runfiles path without the repository name.
//
// Correct:
//
//	Rlocation("intrinsic/skills/build_defs/tests/no_op_skill_py_manifest.pbbin")
//
// Incorrect:
//
//	Rlocation("intrinsic/skills/build_defs/tests/no_op_skill_py_manifest.pbbin")
func Rlocation(p string) (string, error) {
	r, err := runfiles.New()
	if err != nil {
		return "", err
	}
	return r.Rlocation(path.Join("ai_intrinsic_sdks", p))
}

// RootFs gets an fs.FS for runfiles relative to the repo root.
func RootFs() (fs.FS, error) {
	r, err := runfiles.New()
	if err != nil {
		return nil, fmt.Errorf("unable to create runfiles object: %v", err)
	}
	baseDirFs, err := fs.Sub(r, "ai_intrinsic_sdks")
	if err != nil {
		return nil, fmt.Errorf("unable to get runfiles sub: %v", err)
	}
	return baseDirFs, nil
}
