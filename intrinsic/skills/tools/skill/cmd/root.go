// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package cmd contains the root command for the skill installer tool.
package cmd

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
)

const (
	// KeyProject is the Google Cloud Project to use.
	KeyProject = "project"
	// KeySolution is the name of the solution to interact with.
	KeySolution = "solution"

	// SideloadedSkillPrefix is the prefix that is added to the id version of a sideloaded skill.
	SideloadedSkillPrefix = "sideloaded"
)

// SkillCmd is the super-command for everything skill management.
var SkillCmd = &cobra.Command{
	Use:   root.SkillCmdName,
	Short: "Manages skills",
	Long:  "Manages skills in a workcell, in a local repository or in the skill catalog",
}

func init() {
	SkillCmd.PersistentFlags().StringP(KeyProject, "p", "", `The Google Cloud Project (GCP) project to use.
	You can set the environment variable INTRINSIC_PROJECT=project_name to set a default project name.`)

	viper.BindPFlag(KeyProject, SkillCmd.PersistentFlags().Lookup(KeyProject))
	viper.BindEnv(KeyProject)
}
