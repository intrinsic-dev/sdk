// Copyright 2023 Intrinsic Innovation LLC

// Package listreleased defines the skill list_released command which lists skills in a catalog.
package listreleased

import (
	"fmt"

	"github.com/spf13/cobra"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
)

var cmdFlags = cmdutil.NewCmdFlags()

var listReleasedCmd = &cobra.Command{
	Use:   "list_released",
	Short: "List released skills in the catalog",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		return fmt.Errorf("unimplemented")

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedCmd)
	cmdFlags.SetCommand(listReleasedCmd)

	cmdFlags.AddFlagsProjectOrg()
}
