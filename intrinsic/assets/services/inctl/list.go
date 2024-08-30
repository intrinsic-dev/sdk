// Copyright 2023 Intrinsic Innovation LLC

// Package list defines the service command that lists installed services.
package list

import (
	"fmt"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
	iagrpcpb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
	iapb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
)

func ptr[T any](value T) *T {
	return &value
}

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
				client := iagrpcpb.NewInstalledAssetsClient(conn)
				resp, err := client.ListInstalledAssets(ctx, &iapb.ListInstalledAssetsRequest{
					StrictFilter: &iapb.ListInstalledAssetsRequest_Filter{
						AssetType: ptr(atpb.AssetType_ASSET_TYPE_SERVICE),
					},
					PageToken: pageToken,
				})
				if err != nil {
					return fmt.Errorf("could not list services: %v", err)
				}
				for _, s := range resp.GetInstalledAssets() {
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
