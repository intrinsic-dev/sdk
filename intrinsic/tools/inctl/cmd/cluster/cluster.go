// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package cluster contains the externally available commands for cluster handling.
package cluster

import (
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/cobrautil"
)

var (
	// FlagProject holds the value of the --project flag.
	FlagProject string
)

// ClusterCmd is the `inctl cluster` command.
var ClusterCmd = cobrautil.ParentOfNestedSubcommands(
	root.ClusterCmdName, "Workcell cluster handling")

func init() {
	root.RootCmd.AddCommand(ClusterCmd)
	ClusterCmd.PersistentFlags().StringVarP(&FlagProject, "project", "p", "", "The GCP cloud project to use.")
}
