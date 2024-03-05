// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"context"
	"fmt"
	"os"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/prototext"
	"intrinsic/tools/inctl/util/orgutil"
)

func getProcessAsTextProto(ctx context.Context, conn *grpc.ClientConn, clearTreeID bool, clearNodeIDs bool) (string, error) {
	skills, err := getSkills(ctx, conn)
	if err != nil {
		return "", errors.Wrapf(err, "could not list skills")
	}

	t, err := populateProtoTypes(skills)
	if err != nil {
		return "", errors.Wrapf(err, "failed to populate proto types")
	}

	bt, err := getBT(ctx, conn)
	if err != nil {
		return "", errors.Wrapf(err, "could not get behavior tree")
	}

	clearTree(bt, clearTreeID, clearNodeIDs)

	marshaller := prototext.MarshalOptions{
		Resolver:  t,
		Indent:    "  ",
		Multiline: true,
	}
	return marshaller.Format(bt), nil
}

var processGetCmd = &cobra.Command{
	Use:   "get",
	Short: "Get process (behavior tree) of a solution. ",
	Long: `Get the active process (behavior tree) of a currently deployed solution.

Example:
inctl process get --solution my-solution-id --cluster my-cluster [--output_file /tmp/process.textproto]

	`,
	Args: cobra.ExactArgs(0),
	RunE: func(cmd *cobra.Command, args []string) error {
		projectName := viperLocal.GetString(orgutil.KeyProject)
		orgName := viperLocal.GetString(orgutil.KeyOrganization)
		solutionName := flagSolutionName
		clusterName := flagClusterName
		if (solutionName == "" && clusterName == "") || solutionName != "" && clusterName != "" {
			return fmt.Errorf("exactly one of --solution or --cluster must be specified. To find the solution name, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions")
		}

		ctx, conn, err := connectToCluster(cmd.Context(), projectName, orgName, solutionName, clusterName)
		if err != nil {
			return errors.Wrapf(err, "could not connect to cluster")
		}
		defer conn.Close()

		s, err := getProcessAsTextProto(ctx, conn, flagClearTreeID, flagClearNodeIDs)
		if err != nil {
			return errors.Wrapf(err, "could not get BT as text")
		}

		if flagOutputFile != "" {
			if err := os.WriteFile(flagOutputFile, []byte(s), 0644); err != nil {
				return errors.Wrapf(err, "could not write to file %s", flagOutputFile)
			}
			return nil
		}

		fmt.Println(s)

		return nil
	},
}

func init() {
	processGetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to get the process from. For example, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions.")
	processGetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to get the process from.")
	processGetCmd.Flags().StringVar(&flagOutputFile, "output_file", "", "If set, writes the process to the given file instead of stdout.")
	processCmd.AddCommand(processGetCmd)

}
