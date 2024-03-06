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
	"google.golang.org/protobuf/proto"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	"intrinsic/tools/inctl/util/orgutil"
)

type serializer interface {
	serialize(*btpb.BehaviorTree) ([]byte, error)
}

type textSerializer struct {
	ctx  context.Context
	conn *grpc.ClientConn
}

func (t *textSerializer) serialize(bt *btpb.BehaviorTree) ([]byte, error) {
	skills, err := getSkills(t.ctx, t.conn)
	if err != nil {
		return nil, errors.Wrapf(err, "could not list skills")
	}

	pt, err := populateProtoTypes(skills)
	if err != nil {
		return nil, errors.Wrapf(err, "failed to populate proto types")
	}

	marshaller := prototext.MarshalOptions{
		Resolver:  pt,
		Indent:    "  ",
		Multiline: true,
	}
	s := marshaller.Format(bt)
	return []byte(s), nil
}

func newTextSerializer(ctx context.Context, conn *grpc.ClientConn) *textSerializer {
	return &textSerializer{ctx: ctx, conn: conn}
}

type binarySerializer struct {
}

func (b *binarySerializer) serialize(bt *btpb.BehaviorTree) ([]byte, error) {
	marshaller := proto.MarshalOptions{}
	content, err := marshaller.Marshal(bt)
	if err != nil {
		return nil, errors.Wrapf(err, "could not marshal BT")
	}
	return content, nil
}

func newBinarySerializer() *binarySerializer {
	return &binarySerializer{}
}

func serializeBT(ctx context.Context, conn *grpc.ClientConn, bt *btpb.BehaviorTree, format string) ([]byte, error) {
	var s serializer
	switch format {
	case TextProtoFormat:
		s = newTextSerializer(ctx, conn)
	case BinaryProtoFormat:
		s = newBinarySerializer()
	default:
		return nil, fmt.Errorf("unknown format %s", format)
	}

	data, err := s.serialize(bt)
	if err != nil {
		return nil, errors.Wrapf(err, "could not serialize BT")
	}
	return data, nil
}

func getProcess(ctx context.Context, conn *grpc.ClientConn, format string, clearTreeID bool, clearNodeIDs bool) ([]byte, error) {
	bt, err := getBT(ctx, conn)
	if err != nil {
		return nil, errors.Wrapf(err, "could not get behavior tree")
	}

	clearTree(bt, clearTreeID, clearNodeIDs)

	return serializeBT(ctx, conn, bt, format)
}

var processGetCmd = &cobra.Command{
	Use:   "get",
	Short: "Get process (behavior tree) of a solution. ",
	Long: `Get the active process (behavior tree) of a currently deployed solution.

Example:
inctl process get --solution my-solution-id --cluster my-cluster [--output_file /tmp/process.textproto] [--process_format textproto|binaryproto]

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

		content, err := getProcess(ctx, conn, flagProcessFormat, flagClearTreeID, flagClearNodeIDs)
		if err != nil {
			return errors.Wrapf(err, "could not get BT")
		}

		if flagOutputFile != "" {
			if err := os.WriteFile(flagOutputFile, content, 0644); err != nil {
				return errors.Wrapf(err, "could not write to file %s", flagOutputFile)
			}
			return nil
		}

		fmt.Println(string(content))

		return nil
	},
}

func init() {
	processGetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to get the process from. For example, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions.")
	processGetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to get the process from.")
	processGetCmd.Flags().StringVar(&flagOutputFile, "output_file", "", "If set, writes the process to the given file instead of stdout.")
	processCmd.AddCommand(processGetCmd)

}
