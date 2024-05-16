// Copyright 2023 Intrinsic Innovation LLC

// Package runfiles provides functionality to access runfiles
package runfiles

import (

	"github.com/bazelbuild/rules_go/go/runfiles"
)

// Root returns path to runfiles root
func Root() (string, error) {
	r, err := runfiles.New()
	if err != nil {
		return "", err
	}
	root, err := r.Rlocation(".")
	if err != nil {
		return "", err
	}
	return root, nil
}
