// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package cmd contains the root command for the skill installer tool.
package cmd

import (
	"github.com/spf13/cobra"
	"intrinsic/tools/inctl/cmd/root"
)

const (
	// SideloadedSkillPrefix is the prefix that is added to the id version of a sideloaded skill.
	SideloadedSkillPrefix = "sideloaded"
)

// SkillCmd is the super-command for everything skill management.
var SkillCmd = &cobra.Command{
	Use:   root.SkillCmdName,
	Short: "Manages skills",
	Long:  "Manages skills in a workcell, in a local repository or in the skill catalog",
}
