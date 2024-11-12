// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"context"
	"fmt"
	"io/ioutil"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoregistry"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	execgrpcpb "intrinsic/executive/proto/executive_service_go_grpc_proto"
	sgrpcpb "intrinsic/frontend/solution_service/proto/solution_service_go_grpc_proto"
	spb "intrinsic/frontend/solution_service/proto/solution_service_go_grpc_proto"
	skillregistrygrpcpb "intrinsic/skills/proto/skill_registry_go_grpc_proto"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/util/proto/registryutil"
)

var allowedSetFormats = []string{TextProtoFormat, BinaryProtoFormat}

type deserializer interface {
	deserialize(ctx context.Context, content []byte) (*btpb.BehaviorTree, error)
}

type textDeserializer struct {
	srC skillregistrygrpcpb.SkillRegistryClient
}

func (t *textDeserializer) deserialize(ctx context.Context, content []byte) (*btpb.BehaviorTree, error) {
	skills, err := getSkills(ctx, t.srC)
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

func newTextDeserializer(srC skillregistrygrpcpb.SkillRegistryClient) *textDeserializer {
	return &textDeserializer{srC: srC}
}

type binaryDeserializer struct {
}

func (b *binarySerializer) deserialize(ctx context.Context, content []byte) (*btpb.BehaviorTree, error) {
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
	exC          execgrpcpb.ExecutiveServiceClient
	srC          skillregistrygrpcpb.SkillRegistryClient
	soC          sgrpcpb.SolutionServiceClient
	name         string
	format       string
	content      []byte
	clearTreeID  bool
	clearNodeIDs bool
}

func deserializeBT(ctx context.Context, srC skillregistrygrpcpb.SkillRegistryClient, format string, content []byte) (*btpb.BehaviorTree, error) {
	var d deserializer
	switch format {
	case TextProtoFormat:
		d = newTextDeserializer(srC)
	case BinaryProtoFormat:
		d = newBinaryDeserializer()
	default:
		return nil, fmt.Errorf("unknown format %s", format)
	}

	bt, err := d.deserialize(ctx, content)
	if err != nil {
		return nil, errors.Wrapf(err, "could not serialize BT")
	}
	return bt, nil
}

func setProcess(ctx context.Context, params *setProcessParams) error {
	bt, err := deserializeBT(ctx, params.srC, params.format, params.content)
	if err != nil {
		return errors.Wrapf(err, "could not deserialize BT")
	}

	clearTree(bt, params.clearTreeID, params.clearNodeIDs)

	if params.name == "" {
		if err := setBT(ctx, params.exC, bt); err != nil {
			return errors.Wrapf(err, "could not set active behavior tree")
		}
	} else {
		if _, err := params.soC.CreateBehaviorTree(ctx, &spb.CreateBehaviorTreeRequest{
			BehaviorTreeId: params.name,
			BehaviorTree:   bt,
		}); err != nil {
			return errors.Wrapf(err, "could not create behavior tree in the solution")
		}
	}

	return nil
}

var processSetCmd = &cobra.Command{
	Use:   "set",
	Short: "Set process (behavior tree) of a solution. ",
	Long: `Set the process (behavior tree) of a currently deployed solution.

There are two main operation modes. The first one is to set the "active" process
in the executive. This prepares the process for execution. This is the default
behavior if no name is provided as the first argument.

inctl process set --solution my-solution --cluster my-cluster --input_file /tmp/my-process.textproto [--process_format textproto|binaryproto]

---

Alternatively, the process can be added to the solution. The command will do
this if you specify a name for the process as the first argument. This makes the
process available in the list of processes in the Flowstate frontend. The
process will NOT be loaded into the executive. It can instead be executed by
selecting it in the frontend and running from there.

Note: The name you provide as an argument will be set as the "name" field in the
process regardless of the value that may or may not already be present. If there
is already a process with the same name this will fail.

inctl process set name_to_store_with --solution my-solution --cluster my-cluster --input_file /tmp/my-process.textproto [--process_format textproto|binaryproto]`,
	Args: cobra.RangeArgs(0, 1),
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

		if err = setProcess(ctx, &setProcessParams{
			exC:          execgrpcpb.NewExecutiveServiceClient(conn),
			srC:          skillregistrygrpcpb.NewSkillRegistryClient(conn),
			soC:          sgrpcpb.NewSolutionServiceClient(conn),
			content:      content,
			name:         args[0],
			format:       flagProcessFormat,
			clearTreeID:  flagClearTreeID,
			clearNodeIDs: flagClearNodeIDs,
		}); err != nil {
			return errors.Wrapf(err, "could not set BT")
		}

		if args[0] == "" {
			fmt.Println("BT loaded successfully to the executive. To edit behavior tree in the frontend: Process -> Load -> From executive")
		} else {
			fmt.Println("BT added to the solution. To edit and execute the process in the frontend: Process -> Load -> <process name>")
		}

		return nil
	},
}

func init() {
	processSetCmd.Flags().StringVar(
		&flagProcessFormat, "process_format", TextProtoFormat,
		fmt.Sprintf("(optional) input format. One of: (%s)", strings.Join(allowedSetFormats, ", ")))
	processSetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to set the process on. For example, use `inctl solutions list --org orgname@projectname --output json [--filter running_in_sim]` to see the list of solutions.")
	processSetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to set the process on.")
	processSetCmd.Flags().StringVar(&flagInputFile, "input_file", "", "File from which to read the process.")
	processCmd.AddCommand(processSetCmd)

}
