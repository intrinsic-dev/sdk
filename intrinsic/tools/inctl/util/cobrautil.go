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
		RunE: func(cmd *cobra.Command, args []string) error {
			return fmt.Errorf("%s requires a valid subcommand.\n%s", cmd.Name(), cmd.UsageString())
		},
		// Flags are parsed before "RunE" so this should result in a better error if the command is invoked without a subcommand.
		DisableFlagParsing: true,
	}
}
