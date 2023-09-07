// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package cmd contains the root command for the ICON hardware module installer tool.
package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// RootCmd is the top-level command of the ICON hardware module installer.
var RootCmd = &cobra.Command{
	Use:   "hwmodule",
	Short: "hwmodule is a command line tool for ICON hardware module management",
	Long:  "hwmodule is a command line tool used to install or remove ICON hardware modules from a workcell",
}

// Execute is the top-level function that runs the ICON hardware module installer and prints any errors.
func Execute() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
