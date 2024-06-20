// Copyright 2023 Intrinsic Innovation LLC

// Package uninstall defines the command to uninstall a Service.
package uninstall

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	installergrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
)

// GetCommand returns a command to uninstall a service.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "uninstall ID_VERSION",
		Short: "Remove a Service type (Note: This will fail if there are instances of it in the solution)",
		Example: `
		$ inctl service uninstall id_version \
				--project my_project \
				--solution my_solution_id

				To find a service's id_version, run:
				$ inctl service list --org my_organization --solution my_solution_id

				To find a running solution's id, run:
				$ inctl solution list --project my-project --filter "running_on_hw,running_in_sim" --output json
	`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			idVersionStr := args[0]
			if !idutils.IsIDVersion(idVersionStr) {
				return fmt.Errorf("the requested id_version %q is not a valid id_version", idVersionStr)
			}

			ctx, conn, _, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return fmt.Errorf("could not connect to cluster: %w", err)
			}
			defer conn.Close()

			client := installergrpcpb.NewInstallerServiceClient(conn)

			idVersion, err := idutils.IDOrIDVersionProtoFrom(idVersionStr)
			if err != nil {
				return fmt.Errorf("could not parse id_version: %w", err)
			}
			_, err = client.UninstallService(ctx, &installerpb.UninstallServiceRequest{
				IdVersion: idVersion,
			})
			if err != nil {
				return fmt.Errorf("could not uninstall the service: %w", err)
			}
			log.Printf("Finished uninstalling %q", idVersionStr)

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()

	return cmd
}
