// Copyright 2023 Intrinsic Innovation LLC

// Package process contains all commands for handling processes (behavior trees).
package process

import (
	"context"
	"fmt"
	"os"
	"strings"

	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/orgutil"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	lrpb "cloud.google.com/go/longrunning/autogen/longrunningpb"
	"github.com/pkg/errors"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	apb "intrinsic/executive/proto/annotations_go_proto"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	execgrpcpb "intrinsic/executive/proto/executive_service_go_grpc_proto"
	rmdpb "intrinsic/executive/proto/run_metadata_go_proto"
	skillregistrygrpcpb "intrinsic/skills/proto/skill_registry_go_grpc_proto"
	skillspb "intrinsic/skills/proto/skills_go_proto"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/util/proto/registryutil"
)

const (
	keyFilter = "filter"
)

const (
	// TextProtoFormat is the textproto output format.
	TextProtoFormat = "textproto"
	// BinaryProtoFormat is the binary proto output format.
	BinaryProtoFormat = "binaryproto"
)

// AllowedFormats is a list of possible output formats.
var AllowedFormats = []string{TextProtoFormat, BinaryProtoFormat}

var (
	flagSolutionName  string
	flagClusterName   string
	flagInputFile     string
	flagOutputFile    string
	flagClearTreeID   bool
	flagClearNodeIDs  bool
	flagProcessFormat string
)

var (
	viperLocal = viper.New()
)

var (
	protoNameBehaviorTree     = proto.MessageName(new(btpb.BehaviorTree))
	protoNameBehaviorTreeNode = proto.MessageName(new(btpb.BehaviorTree_Node))
)

func clearField(fieldName string, refl protoreflect.Message) {
	field := refl.Descriptor().Fields().ByTextName(fieldName)
	if refl.Has(field) {
		refl.Clear(field)
	}
}

func clearTree(m proto.Message, clearTreeID bool, clearNodeIDs bool) error {
	refl := m.ProtoReflect()

	n := proto.MessageName(m)
	if clearTreeID && n == protoNameBehaviorTree {
		clearField("tree_id", refl)
	}
	if clearNodeIDs && n == protoNameBehaviorTreeNode {
		clearField("id", refl)
	}

	for i := 0; i < refl.Descriptor().Fields().Len(); i++ {
		field := refl.Descriptor().Fields().Get(i)
		if !refl.Has(field) {
			continue
		}
		options := field.Options().(*descriptorpb.FieldOptions)
		outputOnly := proto.GetExtension(options, apb.E_OutputOnly).(bool)

		if outputOnly {
			refl.Clear(field)
		}

		if field.Kind() == protoreflect.MessageKind {
			if field.IsList() {
				list := refl.Get(field).List()
				for j := 0; j < list.Len(); j++ {
					if err := clearTree(list.Get(j).Message().Interface(), clearTreeID, clearNodeIDs); err != nil {
						return err
					}
				}
			} else if !field.IsMap() {
				if err := clearTree(refl.Get(field).Message().Interface(), clearTreeID, clearNodeIDs); err != nil {
					return err
				}
			}
		}
	}
	return nil
}

func connectToCluster(ctx context.Context, projectName string, orgName string, solutionName string, clusterName string) (context.Context, *grpc.ClientConn, error) {
	// Establish a gRPC connection to project and organization.
	ctx, conn, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		CredName: projectName,
		CredOrg:  orgName,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create client connection: %w", err)
	}
	defer conn.Close()

	// Optionally resolve solution name to cluster name.
	if clusterName == "" {
		clusterName, err = solutionutil.GetClusterNameFromSolution(ctx, conn, solutionName)
		if err != nil {
			return nil, nil, errors.Wrapf(err, "could not resolve solution to cluster")
		}
	}

	// Establish a gRPC connection to cluster.
	ctxCluster, connCluster, err := dialerutil.DialConnectionCtx(ctx, dialerutil.DialInfoParams{
		Cluster:  clusterName,
		CredName: projectName,
		CredOrg:  orgName,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create client connection: %w", err)
	}

	return ctxCluster, connCluster, nil
}

func getBT(ctx context.Context, conn *grpc.ClientConn) (*btpb.BehaviorTree, error) {
	client := execgrpcpb.NewExecutiveServiceClient(conn)
	listOpResp, err := client.ListOperations(ctx, &lrpb.ListOperationsRequest{})
	if err != nil {
		return nil, errors.Wrap(err, "unable to list executive operations")
	}

	if len(listOpResp.Operations) == 0 {
		return nil, fmt.Errorf("no operations found. Did you load a behavior tree into the executive?")
	}

	if len(listOpResp.Operations) > 1 {
		fmt.Fprintf(os.Stderr, "Found %d concurrent operations, getting first one", len(listOpResp.Operations))
	}
	operation := listOpResp.Operations[0]

	metadata := new(rmdpb.RunMetadata)
	if err := operation.GetMetadata().UnmarshalTo(metadata); err != nil {
		return nil, errors.Wrap(err, "unable to unmarshal RunMetadata proto")
	}

	return metadata.GetBehaviorTree(), nil
}

func setBT(ctx context.Context, conn *grpc.ClientConn, bt *btpb.BehaviorTree) error {
	client := execgrpcpb.NewExecutiveServiceClient(conn)

	listOpResp, err := client.ListOperations(ctx, &lrpb.ListOperationsRequest{})
	if err != nil {
		return errors.Wrap(err, "unable to list executive operations")
	}

	if len(listOpResp.Operations) > 1 {
		return errors.Errorf("More than one concurrently loaded BT/executive operation, please delete all but one")
	}

	if len(listOpResp.Operations) == 1 {
		operationToDelete := listOpResp.Operations[0]
		if _, err = client.DeleteOperation(ctx, &lrpb.DeleteOperationRequest{
			Name: operationToDelete.Name,
		}); err != nil {
			return errors.Wrap(err, "unable to delete operation")
		}
	}

	req := &execgrpcpb.CreateOperationRequest{}
	req.RunnableType = &execgrpcpb.CreateOperationRequest_BehaviorTree{BehaviorTree: bt}

	if _, err = client.CreateOperation(ctx, req); err != nil {
		return errors.Wrap(err, "unable to create executive operation")
	}

	return nil
}

func getSkills(ctx context.Context, conn *grpc.ClientConn) ([]*skillspb.Skill, error) {
	client := skillregistrygrpcpb.NewSkillRegistryClient(conn)
	resp, err := client.GetSkills(ctx, &emptypb.Empty{})
	if err != nil {
		return nil, fmt.Errorf("could not list skills: %w", err)
	}

	return resp.GetSkills(), nil
}

func populateProtoTypes(skills []*skillspb.Skill) (*protoregistry.Types, error) {
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

	t := new(protoregistry.Types)
	if err := registryutil.PopulateTypesFromFiles(t, r); err != nil {
		return nil, errors.Wrapf(err, "failed to populate types from files")
	}

	return t, nil
}

var processCmd = orgutil.WrapCmd(&cobra.Command{
	Use:     root.ProcessCmdName,
	Aliases: []string{root.ProcessCmdName},
	Short:   "Interacts with processes (behavior trees)",
	Long: `Interacts with processes (behavior trees)

	Examples:

	To download the current BT from the executive to a file:
	inctl process get --solution my-solution-id --cluster my-cluster --output_file /tmp/process.textproto

	To upload a BT from file to the executive:
	inctl process set --solution my-solution --cluster my-cluster --input_file /tmp/my-process.textproto

`,
	DisableFlagParsing: true,
}, viperLocal)

func init() {
	processCmd.PersistentFlags().StringVar(
		&flagProcessFormat, "process_format", TextProtoFormat,
		fmt.Sprintf("(optional) Output format. One of: (%s)", strings.Join(AllowedFormats, ", ")))
	processCmd.Flags().BoolVar(&flagClearTreeID, "clear_tree_id", true, "Clear the tree_id field from the BT proto.")
	processCmd.Flags().BoolVar(&flagClearNodeIDs, "clear_node_ids", true, "Clear the nodes' id fields from the BT proto.")
	root.RootCmd.AddCommand(processCmd)
}
