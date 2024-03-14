// Copyright 2023 Intrinsic Innovation LLC

package process

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoregistry"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	"intrinsic/solutions/tools/pythonserializer"
	"intrinsic/tools/inctl/util/orgutil"
	"intrinsic/util/proto/registryutil"
)

var allowedGetFormats = []string{TextProtoFormat, BinaryProtoFormat, PythonScriptFormat, PythonMinimalFormat, PythonNotebookFormat}

const (
	pythonScriptTemplate = `from intrinsic.solutions import deployments
from intrinsic.solutions import behavior_tree as bt
from intrinsic.math.python import data_types

solution = deployments.connect_to_selected_solution()

executive = solution.executive
resources = solution.resources
skills = solution.skills
world = solution.world

%s
executive.run(tree)
`
	pythonNotebookTemplate = `{
"cells": [
	{
	"cell_type": "code",
	"execution_count": null,
	"metadata": {},
	"outputs": [],
	"source": [
		"from intrinsic.solutions import behavior_tree as bt\n",
		"from intrinsic.solutions import deployments\n",
		"\n",
		"solution = deployments.connect_to_selected_solution()\n",
		"\n",
		"executive = solution.executive\n",
		"resources = solution.resources\n",
		"skills = solution.skills\n",
		"world = solution.world\n"
	]
	},
	{
	"cell_type": "code",
	"execution_count": null,
	"metadata": {},
	"outputs": [],
	"source": [
		%s
	]
	},
	{
		"cell_type": "code",
		"execution_count": null,
		"metadata": {},
		"outputs": [],
		"source": [
			"executive.run(tree)\n"
		]
	}
],
"metadata": {
	"kernelspec": {
	"display_name": "Python 3",
	"language": "python",
	"name": "python3"
	},
	"language_info": {
	"codemirror_mode": {
		"name": "ipython",
		"version": 3
	},
	"file_extension": ".py",
	"mimetype": "text/x-python",
	"name": "python",
	"nbconvert_exporter": "python",
	"pygments_lexer": "ipython3",
	"version": "3.10.13"
	}
},
"nbformat": 4,
"nbformat_minor": 2
}`
)

type serializer interface {
	Serialize(*btpb.BehaviorTree) ([]byte, error)
}

type textSerializer struct {
	pt *protoregistry.Types
}

// Serialize serializes the given behavior tree to textproto.
func (t *textSerializer) Serialize(bt *btpb.BehaviorTree) ([]byte, error) {
	marshaller := prototext.MarshalOptions{
		Resolver:  t.pt,
		Indent:    "  ",
		Multiline: true,
	}
	s := marshaller.Format(bt)
	return []byte(s), nil
}

func newTextSerializer(ctx context.Context, conn *grpc.ClientConn) (*textSerializer, error) {
	skills, err := getSkills(ctx, conn)
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
	return &textSerializer{pt: pt}, nil
}

type binarySerializer struct {
}

// Serialize serializes the given behavior tree to binary proto.
func (b *binarySerializer) Serialize(bt *btpb.BehaviorTree) ([]byte, error) {
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
	var err error
	switch format {
	case TextProtoFormat:
		s, err = newTextSerializer(ctx, conn)
		if err != nil {
			return nil, errors.Wrapf(err, "could not create textproto serializer")
		}
	case BinaryProtoFormat:
		s = newBinarySerializer()
	case PythonScriptFormat, PythonMinimalFormat, PythonNotebookFormat:
		sk, err := getSkills(ctx, conn)
		if err != nil {
			return nil, errors.Wrapf(err, "could not list skills")
		}

		s, err = pythonserializer.NewPythonSerializer(sk)
		if err != nil {
			return nil, errors.Wrapf(err, "could not create python serializer")
		}
	default:
		return nil, fmt.Errorf("unknown format %s", format)
	}

	data, err := s.Serialize(bt)
	if err != nil {
		return nil, errors.Wrapf(err, "could not serialize BT")
	}

	if format == PythonScriptFormat {
		data = []byte(fmt.Sprintf(pythonScriptTemplate, string(data)))
	}
	if format == PythonNotebookFormat {
		lines := strings.SplitN(string(data), "\n", -1)
		for i, line := range lines {
			line = strings.Replace(line, "\"", "\\\"", -1)
			lines[i] = fmt.Sprintf("\t\t\"%s\"", line)
		}
		quotedLines := strings.Join(lines, ",\n")
		data = []byte(fmt.Sprintf(pythonNotebookTemplate, quotedLines))
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
		ctx, conn, err := connectToCluster(cmd.Context(), projectName,
			orgName, flagServerAddress,
			flagSolutionName, flagClusterName)
		if err != nil {
			return errors.Wrapf(err, "could not dial connection")
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
	processGetCmd.Flags().StringVar(
		&flagProcessFormat, "process_format", TextProtoFormat,
		fmt.Sprintf("(optional) output format. One of: (%s)", strings.Join(allowedGetFormats, ", ")))
	processGetCmd.Flags().StringVar(&flagSolutionName, "solution", "", "Solution to get the process from. For example, use `inctl solutions list --project intrinsic-workcells --output json [--filter running_in_sim]` to see the list of solutions.")
	processGetCmd.Flags().StringVar(&flagClusterName, "cluster", "", "Cluster to get the process from.")
	processGetCmd.Flags().StringVar(&flagOutputFile, "output_file", "", "If set, writes the process to the given file instead of stdout.")
	processCmd.AddCommand(processGetCmd)

}
