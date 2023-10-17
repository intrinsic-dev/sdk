// Copyright 2023 Intrinsic Innovation LLC

// Package solution contains all commands for solution handling.
package solution

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/orgutil"
)

const (
	keyFilter = "filter"
)

var (
	viperLocal = viper.New()
)

var solutionCmd = orgutil.WrapCmd(&cobra.Command{
	Use:                root.SolutionCmdName,
	Aliases:            []string{root.SolutionsCmdName},
	Short:              "Solution interacts with solutions",
	DisableFlagParsing: true,
}, viperLocal)

func init() {
	root.RootCmd.AddCommand(solutionCmd)
}
