// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package cluster

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"google.golang.org/grpc"
	clusterdiscoverygrpcpb "intrinsic/frontend/cloud/api/clusterdiscovery_grpc_go_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const (
	keyProject   = "project"
	keyIntrinsic = "intrinsic"
)

var viperLocal = viper.New()

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

type listClustersParams struct {
	serverAddr string
	dialerOpts []grpc.DialOption
	printer    printer.Printer
}

func listClusters(ctx context.Context, params *listClustersParams) error {
	conn, err := grpc.DialContext(ctx, params.serverAddr, params.dialerOpts...)
	if err != nil {
		return fmt.Errorf("failed to create client connection: %w", err)
	}
	defer conn.Close()

	client := clusterdiscoverygrpcpb.NewClusterDiscoveryServiceClient(conn)
	resp, err := client.ListClusterDescriptions(
		ctx, &clusterdiscoverygrpcpb.ListClusterDescriptionsRequest{})
	if err != nil {
		return fmt.Errorf("request to list clusters failed: %w", err)
	}

	params.printer.Print(&ListClusterDescriptionsResponse{m: resp})
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

		projectName := viperLocal.GetString(keyProject)
		serverAddr := "dns:///www.endpoints." + projectName + ".cloud.goog:443"
		ctx, dialerOpts, err := dialerutil.DialInfoCtx(cmd.Context(), dialerutil.DialInfoParams{
			Address:  serverAddr,
			CredName: projectName,
		})
		if err != nil {
			return fmt.Errorf("could not create connection options for the cluster discovery service: %w", err)
		}

		err = listClusters(ctx, &listClustersParams{
			serverAddr: serverAddr,
			dialerOpts: *dialerOpts,
			printer:    prtr,
		})
		if err != nil {
			return err
		}

		return nil
	},
}

func init() {
	ClusterCmd.AddCommand(clusterListCmd)
	clusterListCmd.PersistentFlags().StringP(keyProject, "p", "", `The Google Cloud Project (GCP) project to use.
	You can set the environment variable INTRINSIC_PROJECT=project_name to set a default project name.`)

	viperLocal.SetEnvPrefix(keyIntrinsic)
	viperLocal.BindPFlag(keyProject, clusterListCmd.PersistentFlags().Lookup(keyProject))
	viperLocal.BindEnv(keyProject)

	if viperLocal.GetString(keyProject) == "" {
		clusterListCmd.MarkPersistentFlagRequired(keyProject)
	}
}
