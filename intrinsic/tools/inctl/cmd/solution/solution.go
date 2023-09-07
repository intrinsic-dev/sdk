// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package solution contains all commands for solution handling.
package solution

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
)

const (
	keyIntrinsic = "intrinsic"
	keyProject   = "project"
	keyFilter    = "filter"
)

var (
	viperLocal = viper.New()
)

var solutionCmd = &cobra.Command{
	Use:                root.SolutionCmdName,
	Aliases:            []string{root.SolutionsCmdName},
	Short:              "Solution interacts with solutions",
	DisableFlagParsing: true,
}

func init() {
	root.RootCmd.AddCommand(solutionCmd)
	solutionCmd.PersistentFlags().StringP(keyProject, "p", "",
		`The Google Cloud Project (GCP) project to use. You can set the environment variable
		INTRINSIC_PROJECT=project_name to set a default project name.`)

	viperLocal.SetEnvPrefix(keyIntrinsic)
	viperLocal.BindPFlag(keyProject, solutionCmd.PersistentFlags().Lookup(keyProject))
	viperLocal.BindEnv(keyProject)

	if viperLocal.GetString(keyProject) == "" {
		solutionCmd.MarkPersistentFlagRequired(keyProject)
	}
}
