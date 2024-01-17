// Copyright 2023 Intrinsic Innovation LLC

// Package listreleasedversions defines the skill list_released_versions command which lists versions of a skill in a catalog.
package listreleasedversions

import (
	"fmt"

	"github.com/spf13/cobra"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
)

var cmdFlags = cmdutil.NewCmdFlags()

var listReleasedVersionsCmd = &cobra.Command{
	Use:   "list_released_versions [skill_id]",
	Short: "List versions of a released skill in the catalog",
	Args:  cobra.ExactArgs(1), // skillId
	RunE: func(cmd *cobra.Command, args []string) error {
		return fmt.Errorf("unimplemented")

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedVersionsCmd)
	cmdFlags.SetCommand(listReleasedVersionsCmd)

	cmdFlags.AddFlagsProjectOrg()
}
