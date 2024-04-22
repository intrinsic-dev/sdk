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
)

// GetCommand returns the command to list installed services in a cluster.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List services",
		Example: `
		List the installed services on a particular cluster
		$ inctl service list --context=minikube --project=my_project
		`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()

			ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
				Address:  flags.GetFlagAddress(),
				Cluster:  flags.GetFlagSideloadContext(),
				CredName: flags.GetFlagProject(),
				CredOrg:  flags.GetFlagOrganization(),
			})
			if err != nil {
				return fmt.Errorf("could not create connection options for the installer: %v", err)
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
	flags.AddFlagSideloadContext()
	flags.AddFlagAddress()

	return cmd
}
