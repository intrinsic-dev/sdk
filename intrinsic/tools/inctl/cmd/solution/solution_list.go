// Copyright 2023 Intrinsic Innovation LLC

package solution

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	clusterdiscoverygrpcpb "intrinsic/frontend/cloud/api/clusterdiscovery_api_go_grpc_proto"
	solutiondiscoverygrpcpb "intrinsic/frontend/cloud/api/solutiondiscovery_api_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/tools/inctl/util/printer"
)

var (
	flagFilter     []string
	allowedFilters = []string{"not_running", "running_in_sim", "running_on_hw"}
)

type listSolutionsParams struct {
	filter  []string
	printer printer.Printer
}

// ListSolutionDescriptionsResponse embeds solutiondiscoverygrpcpb.ListSolutionDescriptionsResponse.
type ListSolutionDescriptionsResponse struct {
	m *solutiondiscoverygrpcpb.ListSolutionDescriptionsResponse
}

// MarshalJSON converts a ListSolutionDescriptionsResponse to a byte slice.
func (res *ListSolutionDescriptionsResponse) MarshalJSON() ([]byte, error) {
	type solution struct {
		Name        string `json:"name,omitempty"`
		State       string `json:"state,omitempty"`
		DisplayName string `json:"displayName,omitempty"`
		ClusterName string `json:"clusterName,omitempty"`
	}
	solutions := make([]solution, len(res.m.GetSolutions()))
	for i, c := range res.m.GetSolutions() {
		solutions[i] = solution{
			Name:        c.GetName(),
			State:       c.GetState().String(),
			DisplayName: c.GetDisplayName(),
			ClusterName: c.GetClusterName(),
		}
	}
	return json.Marshal(struct {
		// solution intentionally not omitted when empty
		Solutions []solution `json:"solutions"`
	}{Solutions: solutions})
}

// String converts a ListSolutionDescriptionsResponse to a string
func (res *ListSolutionDescriptionsResponse) String() string {
	const formatString = "%-60s %s"
	lines := []string{}
	lines = append(lines, fmt.Sprintf(formatString, "Name", "State"))
	for _, c := range res.m.GetSolutions() {
		name := c.GetDisplayName()
		if name == "" {
			name = c.GetName()
		}

		statusStr := strings.TrimPrefix(c.GetState().String(), "SOLUTION_STATE_")
		if c.GetClusterName() != "" {
			statusStr = fmt.Sprintf("%s on %s", statusStr, c.GetClusterName())
		}

		lines = append(
			lines,
			fmt.Sprintf(formatString, name, statusStr))
	}
	return strings.Join(lines, "\n")
}

func validateAndGetFilters(filterNames []string) ([]clusterdiscoverygrpcpb.SolutionState, error) {
	filters := []clusterdiscoverygrpcpb.SolutionState{}

	if len(filterNames) == 0 {
		return filters, nil
	}

	for _, filterName := range filterNames {
		filter, ok := clusterdiscoverygrpcpb.SolutionState_value["SOLUTION_STATE_"+strings.ToUpper(filterName)]
		if !ok {
			return filters,
				fmt.Errorf("Filter needs to be one of %s but is %s",
					strings.Join(allowedFilters, ", "), filterName)
		}
		filters = append(filters, clusterdiscoverygrpcpb.SolutionState(filter))
	}

	return filters, nil

}

func listSolutions(ctx context.Context, conn *grpc.ClientConn, params *listSolutionsParams) error {
	filters, err := validateAndGetFilters(params.filter)
	if err != nil {
		return err
	}

	client := solutiondiscoverygrpcpb.NewSolutionDiscoveryServiceClient(conn)
	resp, err := client.ListSolutionDescriptions(
		ctx, &solutiondiscoverygrpcpb.ListSolutionDescriptionsRequest{Filters: filters})

	if err != nil {
		return fmt.Errorf("request to list solutions failed: %w", err)
	}

	params.printer.Print(&ListSolutionDescriptionsResponse{m: resp})
	return nil
}

var solutionListCmd = &cobra.Command{
	Use:   "list",
	Short: "List solutions in a project",
	Long:  "List solutions on the given project.",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		projectName := viperLocal.GetString(orgutil.KeyProject)
		orgName := viperLocal.GetString(orgutil.KeyOrganization)
		ctx, conn, err := dialerutil.DialConnectionCtx(cmd.Context(), dialerutil.DialInfoParams{
			CredName: projectName,
			CredOrg:  orgName,
		})
		if err != nil {
			return fmt.Errorf("failed to create client connection: %w", err)
		}
		defer conn.Close()

		err = listSolutions(ctx, conn, &listSolutionsParams{
			filter:  flagFilter,
			printer: prtr,
		})
		if err != nil {
			return err
		}
		return nil
	},
}

func init() {
	solutionCmd.AddCommand(solutionListCmd)
	solutionListCmd.PersistentFlags().StringSliceVarP(&flagFilter, keyFilter, "", []string{},
		fmt.Sprintf("Filter solutions by state. Available filters: %s."+
			" Separate multiple filters with a comma (without whitespaces in between).",
			strings.Join(allowedFilters, ",")))
}
