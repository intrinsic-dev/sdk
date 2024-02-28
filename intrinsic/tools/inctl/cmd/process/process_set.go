// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"fmt"
	"io/ioutil"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/protobuf/encoding/prototext"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	"intrinsic/tools/inctl/util/orgutil"
)

var processSetCmd = &cobra.Command{
	Use:   "set",
	Short: "Set process (behavior tree) of a solution. ",
	Long: `Set the active process (behavior tree) of a currently deployed solution. 

Example:
inctl process set --solution my-solution --cluster my-cluster --input_file /tmp/my-process.textproto
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
		if flagInputFile == "" {
			return fmt.Errorf("--input_file must be specified")
		}

		ctx, conn, err := connectToCluster(cmd.Context(), projectName, orgName, solutionName, clusterName)
		if err != nil {
			return errors.Wrapf(err, "could not connect to cluster")
		}
		defer conn.Close()

		skills, err := getSkills(ctx, conn)
		if err != nil {
			return errors.Wrapf(err, "could not list skills")
		}

		t, err := populateProtoTypes(skills)
		if err != nil {
			return errors.Wrapf(err, "failed to populate proto types")
		}

		content, err := ioutil.ReadFile(flagInputFile)

		if err != nil {
			return errors.Wrapf(err, "could not read input file")
		}

		unmarshaller := prototext.UnmarshalOptions{
			Resolver:       t,
			AllowPartial:   true,
			DiscardUnknown: true,
		}

		bt := &btpb.BehaviorTree{}
		if err := unmarshaller.Unmarshal(content, bt); err != nil {
			return errors.Wrapf(err, "could not parse input file")
		}

		clearTree(bt, flagClearTreeID, flagClearNodeIDs)

		if err := setBT(ctx, conn, bt); err != nil {
			return errors.Wrapf(err, "could not set behavior tree")
		}

		fmt.Println("BT loaded successfully to the executive. To edit behavior tree in the frontend, click on Process -> Load -> From executive.")

		return nil
	},
}

func init() {
	processSetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to set the process on. For example, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions.")
	processSetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to set the process on.")
	processSetCmd.Flags().StringVar(&flagInputFile, "input_file", "", "File from which to read the process.")
	processCmd.AddCommand(processSetCmd)

}
