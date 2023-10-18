// Copyright 2023 Intrinsic Innovation LLC

package cluster

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	clusterdeletiongrpcpb "intrinsic/frontend/cloud/api/clusterdeletion_grpc_go_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/util/orgutil"
)

func deleteCluster(ctx context.Context, conn *grpc.ClientConn, cluster string) error {
	client := clusterdeletiongrpcpb.NewClusterDeletionServiceClient(conn)
	if _, err := client.DeleteCluster(
		ctx, &clusterdeletiongrpcpb.DeleteClusterRequest{ClusterName: cluster}); err != nil {
		return fmt.Errorf("request to delete cluster: %w", err)
	}

	return nil
}

var clusterDeleteCmd = &cobra.Command{
	Use:   "delete",
	Short: "Delete a cluster in a project",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, argv []string) error {
		projectName := ClusterCmdViper.GetString(orgutil.KeyProject)
		orgName := ClusterCmdViper.GetString(orgutil.KeyOrganization)

		ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
			CredName: projectName,
			CredOrg:  orgName,
		})
		if err != nil {
			return fmt.Errorf("could not create connection for the cluster deletion service: %w", err)
		}

		return deleteCluster(ctx, conn, argv[0])
	},
}

func init() {
	ClusterCmd.AddCommand(clusterDeleteCmd)
}
