// Copyright 2023 Intrinsic Innovation LLC

// Package list defines the service command that lists installed services.
package list

import (
	"fmt"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	rrgrpcpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
	rrpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
)

// GetCommand returns the command to list installed services in a cluster.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List services",
		Example: `
		List the installed services on a particular cluster:
		$ inctl service list --org my_organization --solution my_solution_id

			To find a running solution's id, run:
			$ inctl solution list --project my_project --filter "running_on_hw,running_in_sim" --output json
		`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()

			ctx, conn, _, err := clientutils.DialClusterFromInctl(ctx, flags)
			if err != nil {
				return err
			}
			defer conn.Close()

			var pageToken string
			for {
				client := rrgrpcpb.NewResourceRegistryClient(conn)
				resp, err := client.ListServices(ctx, &rrpb.ListServicesRequest{
					PageToken: pageToken,
				})
				if err != nil {
					return fmt.Errorf("could not list services: %v", err)
				}
				for _, s := range resp.GetServices() {
					idVersion, err := idutils.IDVersionFromProto(s.GetMetadata().GetIdVersion())
					if err != nil {
						return fmt.Errorf("registry returned invalid id_version: %v", err)
					}
					fmt.Println(idVersion)
				}
				pageToken = resp.GetNextPageToken()
				if pageToken == "" {
					break
				}
			}

			return nil
		},
	}

	flags.SetCommand(cmd)
	flags.AddFlagsAddressClusterSolution()
	flags.AddFlagsProjectOrg()

	return cmd
}
