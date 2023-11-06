// Copyright 2023 Intrinsic Innovation LLC

// Package cobrautil provides common cobra utility functions.
package cobrautil

import (
	"fmt"

	"github.com/spf13/cobra"
)

// ParentOfNestedSubcommands returns the parent command used for nested subcommands.
func ParentOfNestedSubcommands(use string, short string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: short,
		// While this only changes the output by a single line, cobra defaults to returning 0
		// when it cannot find a subcommand.
		// This ensures that there's a proper error code for the shell to handle.
		RunE: func(cmd *cobra.Command, args []string) error {
			return fmt.Errorf("%s requires a valid subcommand.\n%s", cmd.Name(), cmd.UsageString())
		},
		// Flags are parsed before "RunE" so this should result in a better error if the command is invoked without a subcommand.
		// This is also used by orgutil to ensure the above RunE can run.
		DisableFlagParsing: true,
	}
}
