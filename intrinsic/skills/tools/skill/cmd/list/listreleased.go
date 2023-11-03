// Copyright 2023 Intrinsic Innovation LLC

// Package listreleased defines the skill list_released command which lists skills in a catalog.
package listreleased

import (
	"fmt"

	"github.com/spf13/cobra"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
)

var cmdFlags = cmdutil.NewCmdFlags()

var listReleasedCmd = &cobra.Command{
	Use:   "list_released",
	Short: "List released skills in the catalog",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		project := cmdFlags.GetFlagProject()
		org := cmdFlags.GetFlagOrganization()

		_, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
			CredName: project,
			CredOrg:  org,
		})
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()

		return fmt.Errorf("unimplemented")

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedCmd)
	cmdFlags.SetCommand(listReleasedCmd)

	cmdFlags.AddFlagsProjectOrg()
}
