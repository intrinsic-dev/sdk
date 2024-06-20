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
	"intrinsic/assets/version"
	installergrpcpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	rrgrpcpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
)

// GetCommand returns a command to uninstall a service.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "uninstall ID|ID_VERSION",
		Short: "Remove a Service type (Note: This will fail if there are instances of it in the solution)",
		Example: `
		$ inctl service uninstall ai.intrinsic.realtime_control_service \
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
			idOrIDVersion := args[0]
			idv, err := idutils.IDOrIDVersionProtoFrom(idOrIDVersion)
			if err != nil {
				return fmt.Errorf("invalid identifier: %v", err)
			}

			ctx, conn, _, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return fmt.Errorf("could not connect to cluster: %w", err)
			}
			defer conn.Close()

			if err := version.Autofill(ctx, rrgrpcpb.NewResourceRegistryClient(conn), idv); err != nil {
				return err
			}

			client := installergrpcpb.NewInstallerServiceClient(conn)
			_, err = client.UninstallService(ctx, &installerpb.UninstallServiceRequest{
				IdVersion: idv,
			})
			if err != nil {
				return fmt.Errorf("could not uninstall the service: %w", err)
			}
			// Ignore the errors, since it was somehow successful already, just
			// use this to provide more clarity about exactly which version was
			// removed.
			if idvStr, err := idutils.IDVersionFromProto(idv); err != nil {
				idOrIDVersion = idvStr
			}
			log.Printf("Finished uninstalling %q", idOrIDVersion)

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()

	return cmd
}
