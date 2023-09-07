// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package stop defines the hardware module stop command which removes a hardware module.
package stop

import (
	"context"
	"fmt"
	"log"

	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerservicegrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"intrinsic/icon/hal/tools/hwmodule/cmd/cmd"
)

var (
	flagInstallerAddress   string
	flagHardwareModuleName string
)

func removeHardwareModule(address, moduleName string) error {
	log.Printf("Removing hardware module %q using the installer service at %q", moduleName, address)
	conn, err := grpc.Dial(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return fmt.Errorf("could not establish connection at address %s: %w", address, err)
	}
	defer conn.Close()

	client := installerservicegrpcpb.NewInstallerServiceClient(conn)
	ctx := context.Background()
	request := &installerpb.RemoveContainerAddonRequest{
		Name: moduleName,
		Type: installerpb.AddonType_ADDON_TYPE_ICON_HARDWARE_MODULE,
	}
	log.Printf("%v", request)
	_, err = client.RemoveContainerAddon(ctx, request)
	if err != nil {
		return fmt.Errorf("could not remove the hardware module: %w", err)
	}
	log.Print("Finished removing the hardware module")
	return nil
}

var stopCmd = &cobra.Command{
	Use:   "stop [target]",
	Short: "Removes a hardware module",
	RunE: func(cmd *cobra.Command, args []string) error {
		installerAddress := flagInstallerAddress
		moduleName := flagHardwareModuleName

		// Remove the hardware module from the server.
		if err := removeHardwareModule(installerAddress, moduleName); err != nil {
			return fmt.Errorf("could not remove the hardware module: %w", err)
		}

		return nil
	},
}

func init() {
	cmd.RootCmd.AddCommand(stopCmd)

	stopCmd.PersistentFlags().StringVar(&flagInstallerAddress, "installer_address", "localhost:17080", "The address of the installer service.")
	stopCmd.PersistentFlags().StringVar(&flagHardwareModuleName, "hardware_module_name", "arm_hardware_module", "The name of the hw module to stop.")

	stopCmd.MarkPersistentFlagRequired("install_address")
}
