// Copyright 2023 Intrinsic Innovation LLC

// Package cluster contains the externally available commands for cluster handling.
package cluster

import (
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/cobrautil"
)

const (
	// KeyProject is used across inctl cluster to specify the target project.
	KeyProject = "project"
	// KeyIntrinsic is used across inctl cluster to specify the prefix for viper's env integration.
	KeyIntrinsic = "intrinsic"
)

// ClusterCmdViper is used across inctl cluster to integrate cmdline parsing with environment variables.
var ClusterCmdViper = viper.New()

// ClusterCmd is the `inctl cluster` command.
var ClusterCmd = cobrautil.ParentOfNestedSubcommands(
	root.ClusterCmdName, "Workcell cluster handling")

func init() {
	root.RootCmd.AddCommand(ClusterCmd)
	ClusterCmd.PersistentFlags().StringP(KeyProject, "p", "", `The Google Cloud Project (GCP) project to use.
	You can set the environment variable INTRINSIC_PROJECT=project_name to set a default project name.`)

	ClusterCmdViper.SetEnvPrefix(KeyIntrinsic)
	ClusterCmdViper.BindPFlag(KeyProject, ClusterCmd.PersistentFlags().Lookup(KeyProject))
	ClusterCmdViper.BindEnv(KeyProject)
}
