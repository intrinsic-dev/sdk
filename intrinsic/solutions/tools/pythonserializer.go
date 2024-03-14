// Copyright 2023 Intrinsic Innovation LLC

// Package pythonserializer serializes a BT to Python code.
package pythonserializer

import (
	"bytes"
	"fmt"
	"slices"
	"strconv"
	"strings"

	"github.com/pkg/errors"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	bcpb "intrinsic/executive/proto/behavior_call_go_proto"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	skillspb "intrinsic/skills/proto/skills_go_proto"
	"intrinsic/util/proto/registryutil"
)

// PythonSerializer is a single-use serializer of BTs to Python code.
// Not thread-safe as it accumulates the string and list of identifiers as part of its state.
type PythonSerializer struct {
	skills         map[string]*skillspb.Skill
	pt             *protoregistry.Types
	identifiers    []string
	skillPrefix    string
	resourcePrefix string
	indent         string
	buffer         *bytes.Buffer
}

// NewPythonSerializer creates a new PythonSerializer instance.
// Note that this is single-use only and not thread-safe (as it keeps internal state).
func NewPythonSerializer(sk []*skillspb.Skill) (*PythonSerializer, error) {
	skills := make(map[string]*skillspb.Skill)
	for _, skill := range sk {
		skills[skill.GetId()] = skill
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

	return &PythonSerializer{
		skills:         skills,
		pt:             pt,
		skillPrefix:    "skills",
		resourcePrefix: "resources",
		identifiers:    []string{"deployments", "solutions", "executive", "world", "skills"},
		indent:         "  ",
		buffer:         bytes.NewBuffer([]byte{}),
	}, nil
}

func (t *PythonSerializer) indentString(indent int) string {
	return strings.Repeat(t.indent, indent)
}

func (t *PythonSerializer) generateUniqueIdentifier(baseName string) string {
	baseName = strings.ToLower(baseName)              // Convert to lowercase
	baseName = strings.ReplaceAll(baseName, " ", "_") // Replace spaces with underscores
	baseName = strings.ReplaceAll(baseName, "-", "_") // Replace hyphens with underscores

	for i := 1; ; i++ { // Use a loop for incrementing
		candidate := baseName
		if i > 1 {
			candidate += "_" + strconv.Itoa(i) // Append counter if needed
		}
		if !slices.Contains(t.identifiers, candidate) {
			t.identifiers = append(t.identifiers, candidate)
			return candidate // Return if unique
		}
	}
}

// Serialize serializes the given BT to Python code.
func (t *PythonSerializer) Serialize(bt *btpb.BehaviorTree) ([]byte, error) {
	_, err := t.serializeBT(bt)
	if err != nil {
		return nil, errors.Wrapf(err, "could not serialize BT")
	}

	return t.buffer.Bytes(), nil
}

func (t *PythonSerializer) serializeBT(bt *btpb.BehaviorTree) (string, error) {
	childIdentifier, err := t.serializeNode(bt.GetRoot())
	if err != nil {
		return "", err
	}

	identifier := t.generateUniqueIdentifier("tree")

	var optionalNameParam string
	if bt.GetName() != "" {
		optionalNameParam = fmt.Sprintf("name=%q, ", bt.GetName())
	}

	fmt.Fprintf(t.buffer, "%s = bt.BehaviorTree(%sroot=%s)\n", identifier, optionalNameParam, childIdentifier)

	return identifier, nil
}

func (t *PythonSerializer) serializeNode(node *btpb.BehaviorTree_Node) (string, error) {
	switch node.GetNodeType().(type) {
	case *btpb.BehaviorTree_Node_Sequence:
		return t.serializeSequence(node)
	case *btpb.BehaviorTree_Node_Task:
		return t.serializeTask(node)
	default:
	}
	return "", fmt.Errorf("unimplemented node type: %T", node.GetNodeType())
}

func (t *PythonSerializer) serializeSequence(node *btpb.BehaviorTree_Node) (string, error) {
	var childIdentifiers []string
	for _, child := range node.GetSequence().GetChildren() {
		identifier, err := t.serializeNode(child)
		if err != nil {
			return "", err
		}
		childIdentifiers = append(childIdentifiers, identifier)
	}

	var optionalNameParam string
	if node.GetName() != "" {
		optionalNameParam = fmt.Sprintf("name=%q, ", node.GetName())
	}

	name := node.GetName()
	if name == "" {
		name = "sequence"
	}
	identifier := t.generateUniqueIdentifier(name)
	fmt.Fprintf(t.buffer, "%s = bt.Sequence(%schildren=[%s])\n", identifier, optionalNameParam, strings.Join(childIdentifiers, ", "))

	if node.GetDecorators() != nil {
		return "", fmt.Errorf("decorators are not yet implemented")
	}

	return identifier, nil
}

func (t *PythonSerializer) serializeTask(node *btpb.BehaviorTree_Node) (string, error) {
	var name string
	if node.GetName() != "" {
		name = node.GetName()
	} else {
		name = node.GetTask().GetCallBehavior().GetSkillId()
	}
	identifierPrefix := strings.ReplaceAll(name, ".", "_")

	taskIdentifier := t.generateUniqueIdentifier(identifierPrefix)

	action, err := t.serializeAction(node.GetTask().GetCallBehavior())
	if err != nil {
		return "", err
	}

	var optionalNameParam string
	if node.GetName() != "" {
		optionalNameParam = fmt.Sprintf("name=%q, ", node.GetName())
	}
	fmt.Fprintf(t.buffer, "%s = bt.Task(%saction=%s)\n", taskIdentifier, optionalNameParam, action)

	if node.GetDecorators() != nil {
		return "", fmt.Errorf("decorators are not yet implemented")
	}

	return taskIdentifier, nil
}

func (t *PythonSerializer) serializeAction(action *bcpb.BehaviorCall) (string, error) {
	indent := 1
	var params []string

	skillInfo := t.skills[action.GetSkillId()]
	if skillInfo == nil {
		return "", fmt.Errorf("could not find skill info for %s", action.GetSkillId())
	}

	paramMessageType, err := t.pt.FindMessageByName(protoreflect.FullName(skillInfo.GetParameterDescription().GetParameterMessageFullName()))
	if err != nil {
		return "", fmt.Errorf("could not find message by name, skill_id=%s, message name=%s", action.GetSkillId(), protoreflect.FullName(skillInfo.GetParameterDescription().GetParameterMessageFullName()))
	}
	paramMessage := paramMessageType.New().Interface()
	if err := action.GetParameters().UnmarshalTo(paramMessage); err != nil {
		return "", errors.Wrap(err, "could not unmarshal parameters")
	}
	refl := paramMessage.ProtoReflect()
	for i := 0; i < refl.Descriptor().Fields().Len(); i++ {
		field := refl.Descriptor().Fields().Get(i)
		if !refl.Has(field) {
			continue
		}
		pythonRepr, err := t.serializeField(skillInfo.GetSkillName(), refl.Get(field), indent+1)
		if err != nil {
			return "", err
		}
		params = append(params, fmt.Sprintf("%s=%s", field.Name(), pythonRepr))
	}

	for entry := range action.GetResources() {
		resourceParam := fmt.Sprintf("%s.%s", t.resourcePrefix, strings.ReplaceAll(action.GetResources()[entry].GetHandle(), ":", "_"))
		params = append(params, fmt.Sprintf("%s=%s", entry, resourceParam))
	}

	if action.GetReturnValueName() != "" {
		params = append(params, fmt.Sprintf("return_value_key=%q", action.GetReturnValueName()))
	}

	indentString := t.indentString(indent)
	return fmt.Sprintf("%s.%s(\n%s%s)", t.skillPrefix, skillInfo.GetSkillName(), indentString, strings.Join(params, fmt.Sprintf(",\n%s", indentString))), nil
}

func (t *PythonSerializer) serializeField(skillName string, value protoreflect.Value, indent int) (string, error) {
	switch value.Interface().(type) {
	case bool:
		if value.Bool() {
			return "True", nil
		}
		return "False", nil
	case int32:
		return strconv.FormatInt(value.Int(), 10), nil
	case int64:
		return strconv.FormatInt(value.Int(), 10), nil
	case uint32:
		return strconv.FormatUint(value.Uint(), 10), nil
	case uint64:
		return strconv.FormatUint(value.Uint(), 10), nil
	case float32:
		var s string
		if value.Float() == float64(int(value.Float())) {
			// Force a decimal point to indicate to Python that this is a float.
			s = ".0"
		}
		return strconv.FormatFloat(value.Float(), 'g', -1, 32) + s, nil
	case float64:
		var s string
		if value.Float() == float64(int(value.Float())) {
			// Force a decimal point to indicate to Python that this is a float.
			s = ".0"
		}
		return strconv.FormatFloat(value.Float(), 'g', -1, 64) + s, nil
	case string:
		s := value.String()
		s = strings.ReplaceAll(s, "\\", "\\\\")
		s = strings.ReplaceAll(s, "\"", "\\\"")
		return fmt.Sprintf("\"%s\"", s), nil
	case protoreflect.EnumNumber:
		enum := value.Enum()
		return strconv.FormatInt(int64(enum), 10), nil
	case protoreflect.Message:
		return t.serializeMessage(skillName, value.Message(), indent)
	case protoreflect.List:
		var listRepr []string
		for i := 0; i < value.List().Len(); i++ {
			v := value.List().Get(i)
			s, err := t.serializeField(skillName, v, indent+1)
			if err != nil {
				return "", errors.Wrapf(err, "could not serialize list field %v", v)
			}
			listRepr = append(listRepr, s)
		}
		indentString := t.indentString(indent)
		return fmt.Sprintf("[\n%s%s]", indentString, strings.Join(listRepr, fmt.Sprintf(",\n%s", indentString))), nil
	case protoreflect.Map:
		return "", fmt.Errorf("unimplemented: cannot serialize map field")
	default:
		return "", fmt.Errorf("unimplemented field type %T", value.Interface())
	}
}

func (t *PythonSerializer) serializeMessage(skillName string, msg protoreflect.Message, indent int) (string, error) {
	var params []string
	refl := msg.Interface().ProtoReflect()
	for i := 0; i < refl.Descriptor().Fields().Len(); i++ {
		field := refl.Descriptor().Fields().Get(i)
		if !refl.Has(field) {
			continue
		}
		pythonRepr, err := t.serializeField(skillName, refl.Get(field), indent+1)
		if err != nil {
			return "", err
		}
		params = append(params, fmt.Sprintf("%s=%s", field.Name(), pythonRepr))
	}

	fullMsgName := msg.Interface().ProtoReflect().Descriptor().FullName()
	parts := strings.Split(string(fullMsgName), ".")
	shortMsgName := parts[len(parts)-1]
	indentString := t.indentString(indent)
	s := fmt.Sprintf("%s.%s.%s(\n%s%s)", t.skillPrefix, skillName, shortMsgName, indentString, strings.Join(params, fmt.Sprintf(",\n%s", indentString)))
	return s, nil
}
