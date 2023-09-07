// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package registryutil

import (
	"testing"

	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/testing/protocmp"
	anypb "google.golang.org/protobuf/types/known/anypb"
	apb "intrinsic/util/proto/testing/diamond_a_go_proto"
	bpb "intrinsic/util/proto/testing/diamond_b_go_proto"
	cpb "intrinsic/util/proto/testing/diamond_c_go_proto"
	dpb "intrinsic/util/proto/testing/diamond_d_go_proto"
	epb "intrinsic/util/proto/testing/embedded_go_proto"
	rpb "intrinsic/util/proto/testing/recursive_go_proto"
)

var (
	diamondSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&apb.A{}).ProtoReflect().Descriptor().ParentFile()),
			protodesc.ToFileDescriptorProto((&bpb.B{}).ProtoReflect().Descriptor().ParentFile()),
			protodesc.ToFileDescriptorProto((&cpb.C{}).ProtoReflect().Descriptor().ParentFile()),
			protodesc.ToFileDescriptorProto((&dpb.D{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
	embeddedSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&epb.TopLevel{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
	recursiveSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&rpb.Recursive{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
)

func mustMakeFiles(t *testing.T, set *descriptorpb.FileDescriptorSet) *protoregistry.Files {
	t.Helper()

	files, err := protodesc.NewFiles(set)
	if err != nil {
		t.Fatalf("protodesc.NewFiles(%v) = %v, want nil", set, err)
	}
	return files
}

func TestPopulateTypesFromFiles(t *testing.T) {
	tests := []struct {
		desc              string
		files             *protoregistry.Files
		wantNumEnums      int
		wantNumExtensions int
		wantNumMessages   int
		want              proto.Message
	}{
		{
			desc:              "diamond",
			files:             mustMakeFiles(t, diamondSet),
			wantNumEnums:      0,
			wantNumExtensions: 0,
			wantNumMessages:   4,
		},
		{
			desc:              "embedded",
			files:             mustMakeFiles(t, embeddedSet),
			wantNumEnums:      2,
			wantNumExtensions: 0,
			wantNumMessages:   4,
		},
		{
			desc:              "recursive",
			files:             mustMakeFiles(t, recursiveSet),
			wantNumEnums:      0,
			wantNumExtensions: 0,
			wantNumMessages:   1,
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			types := new(protoregistry.Types)
			if err := PopulateTypesFromFiles(types, tc.files); err != nil {
				t.Errorf("PopulateTypesFromFiles(%v) = %v, want nil", tc.files, err)
			}

			if want, got := tc.wantNumEnums, types.NumEnums(); got != want {
				t.Errorf("Want %d enums, got %d", want, got)
			}
			if want, got := tc.wantNumExtensions, types.NumExtensions(); got != want {
				t.Errorf("Want %d extensions, got %d", want, got)
			}
			if want, got := tc.wantNumMessages, types.NumMessages(); got != want {
				t.Errorf("Want %d messages, got %d", want, got)
			}
		})
	}

}

func TestNewTypesFromFileDescriptorSet(t *testing.T) {
	tests := []struct {
		desc              string
		set               *descriptorpb.FileDescriptorSet
		wantNumEnums      int
		wantNumExtensions int
		wantNumMessages   int
		want              proto.Message
	}{
		{
			desc:              "nil is empty",
			wantNumEnums:      0,
			wantNumExtensions: 0,
			wantNumMessages:   0,
		},
		{
			desc:              "diamond",
			set:               diamondSet,
			wantNumEnums:      0,
			wantNumExtensions: 0,
			wantNumMessages:   4,
		},
		{
			desc:              "embedded",
			set:               embeddedSet,
			wantNumEnums:      2,
			wantNumExtensions: 0,
			wantNumMessages:   4,
		},
		{
			desc:              "recursive",
			set:               recursiveSet,
			wantNumEnums:      0,
			wantNumExtensions: 0,
			wantNumMessages:   1,
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			types, err := NewTypesFromFileDescriptorSet(tc.set)
			if err != nil {
				t.Errorf("NewTypesFromFileDescriptorSet(%v) = %v, want nil", tc.set, err)
			}

			if want, got := tc.wantNumEnums, types.NumEnums(); got != want {
				t.Errorf("Want %d enums, got %d", want, got)
			}
			if want, got := tc.wantNumExtensions, types.NumExtensions(); got != want {
				t.Errorf("Want %d extensions, got %d", want, got)
			}
			if want, got := tc.wantNumMessages, types.NumMessages(); got != want {
				t.Errorf("Want %d messages, got %d", want, got)
			}
		})
	}

}

func TestReadTextAnyProtoWithResolver(t *testing.T) {
	types := new(protoregistry.Types)
	PopulateTypesFromFiles(types, mustMakeFiles(t, diamondSet))
	PopulateTypesFromFiles(types, mustMakeFiles(t, embeddedSet))
	options := prototext.UnmarshalOptions{Resolver: types}

	tests := []struct {
		desc  string
		value string
		want  proto.Message
	}{
		{
			desc: "A",
			value: `[intrinsic_proto.test.A] {
				value: "hello world"
			}`,
			want: &apb.A{
				Value: "hello world",
			},
		},
		{
			desc: "B",
			value: `[intrinsic_proto.test.B] {
				a {
					value: "hello world"
				}
			}`,
			want: &bpb.B{
				A: &apb.A{
					Value: "hello world",
				},
			},
		},
		{
			desc: "D",
			value: `[intrinsic_proto.test.D] {
				b {
					a { value: "hello" }
				}
				c {
					a { value: "world" }
				}
			}`,
			want: &dpb.D{
				B: &bpb.B{
					A: &apb.A{
						Value: "hello",
					},
				},
				C: &cpb.C{
					A: &apb.A{
						Value: "world",
					},
				},
			},
		},
		{
			desc: "Embedded",
			value: `[intrinsic_proto.test.TopLevel] {
				value: "40"
				shape: CIRCLE
				middle {
					a { value: 41 }
					b { value: 42 }
				}
			}`,
			want: &epb.TopLevel{
				Value: "40",
				Shape: epb.TopLevel_MiddleLevel_CIRCLE,
				Middle: &epb.TopLevel_MiddleLevel{
					A: &epb.TopLevel_MiddleLevel_BottomA{
						Value: 41,
					},
					B: &epb.TopLevel_MiddleLevel_BottomB{
						Value: 42,
					},
				},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			anyProto := &anypb.Any{}
			if err := options.Unmarshal([]byte(tc.value), anyProto); err != nil {
				t.Errorf("Unmarshal(%v) = %v, want nil", tc.value, err)
			}
			got := proto.Clone(tc.want)
			proto.Reset(got)
			if err := anypb.UnmarshalTo(anyProto, got, proto.UnmarshalOptions{Resolver: types}); err != nil {
				t.Errorf("anypb.Unmarshal(%v) = %v, want nil", anyProto, err)
			}

			if diff := cmp.Diff(tc.want, got, protocmp.Transform()); diff != "" {
				t.Errorf("anypb.UnmarshalTo(%v) returned unexpected diff (-want +got):\n%s", anyProto, diff)
			}
		})
	}
}
