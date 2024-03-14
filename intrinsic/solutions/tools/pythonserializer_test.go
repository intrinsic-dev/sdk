// Copyright 2023 Intrinsic Innovation LLC

package pythonserializer

import (
	"testing"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/reflect/protodesc"
	btpb "intrinsic/executive/proto/behavior_tree_go_proto"
	skillspb "intrinsic/skills/proto/skills_go_proto"
	mypb "intrinsic/solutions/tools/proto/my_msg_go_proto"
)

const (
	treeWithData = `
		tree_id: "tree_id"
		name: "tree_name"
		root {
			sequence {
				children {
					task {
						call_behavior {
							skill_id: "my_skill"
							parameters {
								[type.googleapis.com/intrinsic_proto.solutions.tools.MyMsg] {
									string_value: "my_msg"
									bool_value: true
									int32_value: 1111
									int64_value: 2222
									uint32_value: 3333
									uint64_value: 4444
									float_value: 5.5
									double_value: 6.6
									enum_value: VALUE_A
									msg_value {
										string_value: "nested_msg"
									}
									repeated_msg_value {
										string_value: "repeated_msg"
									}
								}
							}
						}
					}
				}
				children {
					task {
						call_behavior {
							skill_id: "my_skill"
							parameters {
								[type.googleapis.com/intrinsic_proto.solutions.tools.MyMsg] {
									float_value: 5
									double_value: 6
								}
							}
						}
					}
				}
				children {
				  name: "node_with_a_name"
					task {
						call_behavior {
							skill_id: "my_skill"
							parameters {
								[type.googleapis.com/intrinsic_proto.solutions.tools.MyMsg] {
								}
							}
						}
					}
				}
			}
		}
	`
)

func mustParseTree(t *testing.T, content string) *btpb.BehaviorTree {
	t.Helper()
	unmarshaller := prototext.UnmarshalOptions{}
	bt := &btpb.BehaviorTree{}
	if err := unmarshaller.Unmarshal([]byte(content), bt); err != nil {
		t.Fatalf("failed to unmarshal textproto: %v", err)
	}
	return bt
}

func TestSerializeToPythonCode(t *testing.T) {
	bt := mustParseTree(t, treeWithData)

	msg := mypb.MyMsg{}
	refl := msg.ProtoReflect()
	fd := refl.Descriptor().ParentFile()
	fdp := protodesc.ToFileDescriptorProto(fd)

	sk := []*skillspb.Skill{
		&skillspb.Skill{
			Id:        "my_skill",
			SkillName: "my_skill",
			ParameterDescription: &skillspb.ParameterDescription{
				ParameterMessageFullName: "intrinsic_proto.solutions.tools.MyMsg",
				ParameterDescriptorFileset: &dpb.FileDescriptorSet{
					File: []*dpb.FileDescriptorProto{fdp},
				},
			},
		},
	}

	serializer, err := NewPythonSerializer(sk)
	if err != nil {
		t.Fatalf("failed to create serializer: %v", err)
	}
	got, err := serializer.Serialize(bt)
	if err != nil {
		t.Fatalf("failed to serialize: %v", err)
	}

	expected := `my_skill = bt.Task(action=skills.my_skill(
  bool_value=True,
  int32_value=1111,
  int64_value=2222,
  uint32_value=3333,
  uint64_value=4444,
  float_value=5.5,
  double_value=6.6,
  string_value="my_msg",
  enum_value=1,
  msg_value=skills.my_skill.MyMsg(
    string_value="nested_msg"),
  repeated_msg_value=[
    skills.my_skill.MyMsg(
      string_value="repeated_msg")]))
my_skill_2 = bt.Task(action=skills.my_skill(
  float_value=5.0,
  double_value=6.0))
node_with_a_name = bt.Task(name="node_with_a_name", action=skills.my_skill(
  ))
sequence = bt.Sequence(children=[my_skill, my_skill_2, node_with_a_name])
tree = bt.BehaviorTree(name="tree_name", root=sequence)
`
	if diff := cmp.Diff(expected, string(got)); diff != "" {
		t.Errorf("getProcess() returned diff (-want +got):\n%s\n\ngot:\n%s\n\nwant:\n%s", diff, got, expected)
	}
}
