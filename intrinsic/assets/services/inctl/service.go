// Copyright 2023 Intrinsic Innovation LLC

// Package service contains all commands for handling service assets.
package service

import (
	"github.com/spf13/cobra"
	"intrinsic/assets/services/inctl/add"
	deletecmd "intrinsic/assets/services/inctl/delete"
	"intrinsic/assets/services/inctl/install"
	"intrinsic/assets/services/inctl/list"
	"intrinsic/assets/services/inctl/uninstall"
	"intrinsic/tools/inctl/cmd/root"
)

// ServiceCmd is the super-command for everything to manage services.
var serviceCmd = &cobra.Command{
	Use:   root.ServiceCmdName,
	Short: "Manages service assets",
	Long:  "Manages service assets",
}

func init() {
	serviceCmd.AddCommand(add.GetCommand())
	serviceCmd.AddCommand(deletecmd.GetCommand())
	serviceCmd.AddCommand(install.GetCommand())
	serviceCmd.AddCommand(list.GetCommand())
	serviceCmd.AddCommand(uninstall.GetCommand())

	root.RootCmd.AddCommand(serviceCmd)
}
