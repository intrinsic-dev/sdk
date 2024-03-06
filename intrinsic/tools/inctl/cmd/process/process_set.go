// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"context"
	"fmt"
	"io/ioutil"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	"intrinsic/tools/inctl/util/orgutil"
)

type deserializer interface {
	deserialize([]byte) (*btpb.BehaviorTree, error)
}

type textDeserializer struct {
	ctx  context.Context
	conn *grpc.ClientConn
}

func (t *textDeserializer) deserialize(content []byte) (*btpb.BehaviorTree, error) {
	skills, err := getSkills(t.ctx, t.conn)
	if err != nil {
		return nil, errors.Wrapf(err, "could not list skills")
	}

	pt, err := populateProtoTypes(skills)
	if err != nil {
		return nil, errors.Wrapf(err, "failed to populate proto types")
	}

	unmarshaller := prototext.UnmarshalOptions{
		Resolver:       pt,
		AllowPartial:   true,
		DiscardUnknown: true,
	}

	bt := &btpb.BehaviorTree{}
	if err := unmarshaller.Unmarshal(content, bt); err != nil {
		return nil, errors.Wrapf(err, "could not parse input file")
	}
	return bt, nil
}

func newTextDeserializer(ctx context.Context, conn *grpc.ClientConn) *textDeserializer {
	return &textDeserializer{ctx: ctx, conn: conn}
}

type binaryDeserializer struct {
}

func (b *binarySerializer) deserialize(content []byte) (*btpb.BehaviorTree, error) {
	bt := &btpb.BehaviorTree{}
	if err := proto.Unmarshal(content, bt); err != nil {
		return nil, errors.Wrapf(err, "could not parse input file")
	}
	return bt, nil
}

func newBinaryDeserializer() *binarySerializer {
	return &binarySerializer{}
}

type setProcessParams struct {
	format       string
	content      []byte
	clearTreeID  bool
	clearNodeIDs bool
}

func deserializeBT(ctx context.Context, conn *grpc.ClientConn, format string, content []byte) (*btpb.BehaviorTree, error) {
	var d deserializer
	switch format {
	case TextProtoFormat:
		d = newTextDeserializer(ctx, conn)
	case BinaryProtoFormat:
		d = newBinaryDeserializer()
	default:
		return nil, fmt.Errorf("unknown format %s", format)
	}

	bt, err := d.deserialize(content)
	if err != nil {
		return nil, errors.Wrapf(err, "could not serialize BT")
	}
	return bt, nil
}

func setProcess(ctx context.Context, conn *grpc.ClientConn, params *setProcessParams) error {
	bt, err := deserializeBT(ctx, conn, params.format, params.content)
	if err != nil {
		return errors.Wrapf(err, "could not deserialize BT")
	}

	clearTree(bt, params.clearTreeID, params.clearNodeIDs)

	if err := setBT(ctx, conn, bt); err != nil {
		return errors.Wrapf(err, "could not set behavior tree")
	}

	return nil
}

var processSetCmd = &cobra.Command{
	Use:   "set",
	Short: "Set process (behavior tree) of a solution. ",
	Long: `Set the active process (behavior tree) of a currently deployed solution.

Example:
inctl process set --solution my-solution --cluster my-cluster --input_file /tmp/my-process.textproto [--process_format textproto|binaryproto]
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

		content, err := ioutil.ReadFile(flagInputFile)
		if err != nil {
			return errors.Wrapf(err, "could not read input file")
		}

		if err = setProcess(ctx, conn, &setProcessParams{
			content:      content,
			format:       flagProcessFormat,
			clearTreeID:  flagClearTreeID,
			clearNodeIDs: flagClearNodeIDs,
		}); err != nil {
			return errors.Wrapf(err, "could not set BT")
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
