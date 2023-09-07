// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package bazel contains the 'inctl bazel' sub-command.
package bazel

import (
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/cobrautil"
)

// bazelCmd is the super-command for managing Bazel workspaces when working
// with the Intrinsic SDK.
var bazelCmd = cobrautil.ParentOfNestedSubcommands("bazel", "Interact with Bazel workspaces")

func init() {
	root.RootCmd.AddCommand(bazelCmd)
}
