// Copyright 2023 Intrinsic Innovation LLC

// Package cluster contains the externally available commands for cluster handling.
package cluster

import (
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/cobrautil"
	"intrinsic/tools/inctl/util/orgutil"
)

const (
	// KeyIntrinsic is used across inctl cluster to specify the prefix for viper's env integration.
	KeyIntrinsic = "intrinsic"
)

// ClusterCmdViper is used across inctl cluster to integrate cmdline parsing with environment variables.
var ClusterCmdViper = viper.New()

// ClusterCmd is the `inctl cluster` command.
var ClusterCmd = orgutil.WrapCmd(cobrautil.ParentOfNestedSubcommands(
	root.ClusterCmdName, "Workcell cluster handling"), ClusterCmdViper)

func init() {
	root.RootCmd.AddCommand(ClusterCmd)
}
