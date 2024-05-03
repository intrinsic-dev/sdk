// Copyright 2023 Intrinsic Innovation LLC

// Package list defines the service command that lists installed services.
package list

import (
	"fmt"

	"github.com/spf13/cobra"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	rrgrpcpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
	rrpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
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
			project := flags.GetFlagProject()
			org := flags.GetFlagOrganization()

			cluster, solution, err := flags.GetFlagsListClusterSolution()
			if err != nil {
				return fmt.Errorf("could not get flags (ie. address, cluster, solution): %v", err)
			}

			if solution != "" {
				// attempt to get cluster name from solution id
				ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
					CredName: project,
					CredOrg:  org,
				})
				if err != nil {
					return fmt.Errorf("could not create connection options for list services: %v", err)
				}
				defer conn.Close()

				cluster, err = solutionutil.GetClusterNameFromSolution(ctx, conn, solution)
				if err != nil {
					return fmt.Errorf("could not get cluster name from solution: %v", err)
				}
			}

			ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
				Cluster:  cluster,
				CredName: project,
				CredOrg:  org,
			})
			if err != nil {
				return fmt.Errorf("could not create connection options for listing services: %v", err)
			}

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
	flags.AddFlagsProjectOrg()
	flags.AddFlagsListClusterSolution("service")

	return cmd
}
