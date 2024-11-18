// Copyright 2023 Intrinsic Innovation LLC

// Package pathresolver provides functionality to access runfiles
package pathresolver

import (
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"

	"github.com/bazelbuild/rules_go/go/runfiles"
)

// ResolveRunfilesFs gets an fs.FS for runfiles relative to the repo root.
func ResolveRunfilesFs() (fs.FS, error) {
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

// ResolveRunfilesPath gets the runfiles location of a file.
//
// Use the typical runfiles path without the repository name.
//
// Correct:
//
//	ResolveRunfilesPath("intrinsic/skills/build_defs/tests/no_op_skill_py_manifest.pbbin")
//
// Incorrect:
//
//	ResolveRunfilesPath("intrinsic/skills/build_defs/tests/no_op_skill_py_manifest.pbbin")
func ResolveRunfilesPath(p string) (string, error) {
	r, err := runfiles.New()
	if err != nil {
		return "", err
	}
	return r.Rlocation(path.Join("ai_intrinsic_sdks", p))
}

// ResolveRunfilesOrLocalPath gets the runfiles or local location of a file.
//
// This is useful when packaging inside a container, where the runfiles directory
// is not available.
func ResolveRunfilesOrLocalPath(p string) (string, error) {
	resolvedPath, errRunfile := ResolveRunfilesPath(p)
	if errRunfile == nil {
		return resolvedPath, nil
	}
	resolvedRepo := "ai_intrinsic_sdks~override"
	resolvedPath = filepath.Join(".", resolvedRepo, p)
	if _, err := os.Stat(resolvedPath); err != nil {
		return "", fmt.Errorf("unable to resolve path %q:\n  Not available as runfile: %v\n  Not available as local file: %v", p, errRunfile, err)
	}
	return resolvedPath, nil
}
