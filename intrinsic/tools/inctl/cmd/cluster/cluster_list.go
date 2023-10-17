// Copyright 2023 Intrinsic Innovation LLC

package cluster

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	clusterdiscoverygrpcpb "intrinsic/frontend/cloud/api/clusterdiscovery_grpc_go_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/printer"
)

// ListClusterDescriptionsResponse embeds clusterdiscoverygrpcpb.ListClusterDescriptionsResponse.
type ListClusterDescriptionsResponse struct {
	m *clusterdiscoverygrpcpb.ListClusterDescriptionsResponse
}

// MarshalJSON converts a ListClusterDescriptionsResponse to a byte slice.
func (res *ListClusterDescriptionsResponse) MarshalJSON() ([]byte, error) {
	type cluster struct {
		ClusterName string `json:"clusterName,omitempty"`
		K8sContext  string `json:"k8sContext,omitempty"`
		Region      string `json:"region,omitempty"`
		CanDoSim    bool   `json:"canDoSim,omitempty"`
		CanDoReal   bool   `json:"canDoReal,omitempty"`
		HasGpu      bool   `json:"hasGpu,omitempty"`
	}
	clusters := make([]cluster, len(res.m.Clusters))
	for i, c := range res.m.Clusters {
		clusters[i] = cluster{
			ClusterName: c.GetClusterName(),
			K8sContext:  c.GetK8SContext(),
			Region:      c.GetRegion(),
			CanDoSim:    c.GetCanDoSim(),
			CanDoReal:   c.GetCanDoReal(),
			HasGpu:      c.GetHasGpu(),
		}
	}
	return json.Marshal(struct {
		Clusters []cluster `json:"clusters"`
	}{Clusters: clusters})
}

// String converts a ListClusterDescriptionsResponse to a string
func (res *ListClusterDescriptionsResponse) String() string {
	const formatString = "%-35s %-10s %s"
	lines := []string{}
	lines = append(lines, fmt.Sprintf(formatString, "Name", "Region", "K8S Context"))
	for _, c := range res.m.Clusters {
		lines = append(
			lines,
			fmt.Sprintf(formatString, c.GetClusterName(), c.GetRegion(), c.GetK8SContext()))
	}
	return strings.Join(lines, "\n")
}

func fetchAndPrintClusters(ctx context.Context, conn *grpc.ClientConn, prtr printer.Printer) error {
	client := clusterdiscoverygrpcpb.NewClusterDiscoveryServiceClient(conn)
	resp, err := client.ListClusterDescriptions(
		ctx, &clusterdiscoverygrpcpb.ListClusterDescriptionsRequest{})
	if err != nil {
		return fmt.Errorf("request to list clusters failed: %w", err)
	}

	prtr.Print(&ListClusterDescriptionsResponse{m: resp})

	return nil
}

var clusterListCmd = &cobra.Command{
	Use:   "list",
	Short: "List clusters in a project",
	Long:  "List compute cluster on the given project.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
			CredName: ClusterCmdViper.GetString(orgutil.KeyProject),
			CredOrg:  ClusterCmdViper.GetString(orgutil.KeyOrganization),
		})
		if err != nil {
			return fmt.Errorf("could not create connection options for the cluster discovery service: %w", err)
		}
		defer conn.Close()

		return fetchAndPrintClusters(ctx, conn, prtr)
	},
}

func init() {
	ClusterCmd.AddCommand(clusterListCmd)
}
