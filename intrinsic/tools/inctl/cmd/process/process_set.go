// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"context"
	"fmt"
	"io/ioutil"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoregistry"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/util/proto/registryutil"
)

var allowedSetFormats = []string{TextProtoFormat, BinaryProtoFormat}

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

	r := new(protoregistry.Files)
	for _, skill := range skills {
		for _, parameterDescriptorFile := range skill.GetParameterDescription().GetParameterDescriptorFileset().GetFile() {
			fd, err := protodesc.NewFile(parameterDescriptorFile, r)
			if err != nil {
				return nil, errors.Wrapf(err, "failed to add file to registry")
			}
			r.RegisterFile(fd)
		}
	}

	pt := new(protoregistry.Types)
	if err := registryutil.PopulateTypesFromFiles(pt, r); err != nil {
		return nil, errors.Wrapf(err, "failed to populate types from files")
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
		if flagInputFile == "" {
			return fmt.Errorf("--input_file must be specified")
		}

		projectName := viperLocal.GetString(orgutil.KeyProject)
		orgName := viperLocal.GetString(orgutil.KeyOrganization)
		ctx, conn, err := connectToCluster(cmd.Context(), projectName,
			orgName, flagServerAddress,
			flagSolutionName, flagClusterName)
		if err != nil {
			return errors.Wrapf(err, "could not dial connection")
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
	processSetCmd.Flags().StringVar(
		&flagProcessFormat, "process_format", TextProtoFormat,
		fmt.Sprintf("(optional) input format. One of: (%s)", strings.Join(allowedSetFormats, ", ")))
	processSetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to set the process on. For example, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions.")
	processSetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to set the process on.")
	processSetCmd.Flags().StringVar(&flagInputFile, "input_file", "", "File from which to read the process.")
	processCmd.AddCommand(processSetCmd)

}
