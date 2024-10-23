// Copyright 2023 Intrinsic Innovation LLC

package sourcecodeinfoview

import (
	"testing"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
	"intrinsic/util/proto/protoio"
)

const (
	testFile = "intrinsic/util/proto/build_defs/testing/test_message_proto_descriptors_transitive_set_sci.proto.bin"
)

func mustLoadTestFiledDescriptor(t *testing.T) *dpb.FileDescriptorSet {
	t.Helper()
	fileDescriptorSet := new(dpb.FileDescriptorSet)
	if err := protoio.ReadBinaryProto(testFile, fileDescriptorSet); err != nil {
		t.Fatalf("Unable to read %v", testFile)
	}
	return fileDescriptorSet
}

func clearSourceCodeInfo(fds *dpb.FileDescriptorSet) *dpb.FileDescriptorSet {
	for _, file := range fds.GetFile() {
		file.SourceCodeInfo = nil
	}
	return fds
}

func TestFailures(t *testing.T) {
	tests := []struct {
		desc            string
		protoDescriptor *dpb.FileDescriptorSet
		messageName     string
	}{
		{
			desc:            "nil protoDescriptor",
			protoDescriptor: nil,
			messageName:     "some.message",
		},
		{
			desc:            "empty protoDescriptor",
			protoDescriptor: new(dpb.FileDescriptorSet),
			messageName:     "some.message",
		},
		{
			desc:            "non existent message",
			protoDescriptor: mustLoadTestFiledDescriptor(t),
			messageName:     "some.message",
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			_, err := GetNestedFieldCommentMap(tc.protoDescriptor, tc.messageName)
			if err == nil {
				t.Errorf("GetNestedFieldCommentMap(%v, %v): unexpectedly succeeded", tc.protoDescriptor, tc.messageName)
			}
		})
	}
}

func TestGetLeadingCommentsByFieldNameWithValidNameSucceeds(t *testing.T) {
	givenFileDescriptorSet, givenMessageName := mustLoadTestFiledDescriptor(t), "intrinsic.build_def.testing.TestMessageB"
	got, err := GetNestedFieldCommentMap(givenFileDescriptorSet, givenMessageName)
	if err != nil {
		t.Fatalf("Unexpected error %v", err)
	}
	want := map[string]string{
		"intrinsic.build_def.testing.SubMessageB.hello":                  " a field\n",
		"intrinsic.build_def.testing.SubMessageB":                        " A submessage\n",
		"intrinsic.build_def.testing.SubMessage":                         "",
		"intrinsic.build_def.testing.TestMessageB":                       " A test message\n",
		"intrinsic.build_def.testing.TestMessageB.submesage_b":           "",
		"intrinsic.build_def.testing.TestMessageB.submessage":            " A submessage\n",
		"intrinsic.build_def.testing.TestMessageB.submessage_no_comment": "",
		"intrinsic.build_def.testing.SubMessage.my_double":               " Your favorite double of all time.\n",
	}
	if diff := cmp.Diff(want, got, protocmp.Transform()); diff != "" {
		t.Errorf("GetNestedFieldCommentMap(%v, %v) returned unexpected diff (-want +got):\n%s", givenFileDescriptorSet, givenMessageName, diff)
	}
}

func TestPruningDoesNotAffectGetNestedFieldCommentMap(t *testing.T) {
	originalFDS := mustLoadTestFiledDescriptor(t)

	tests := []struct {
		name            string
		protoDescriptor *dpb.FileDescriptorSet
		messageName     string
	}{
		{
			name:        "intrinsic.build_def.testing.TestMessage",
			messageName: "intrinsic.build_def.testing.TestMessage",
		},
		{
			name:        "intrinsic.build_def.testing.TestMessageB",
			messageName: "intrinsic.build_def.testing.TestMessageB",
		},
		{
			name:        "intrinsic.build_def.testing.SubMessage",
			messageName: "intrinsic.build_def.testing.SubMessage",
		},
		{
			name:        "intrinsic.build_def.testing.SubMessageB",
			messageName: "intrinsic.build_def.testing.SubMessageB",
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			fds := proto.Clone(originalFDS).(*dpb.FileDescriptorSet)
			want, err := GetNestedFieldCommentMap(fds, tc.messageName)
			if err != nil {
				t.Fatalf("Unexpected error %v", err)
			}
			PruneSourceCodeInfo([]string{tc.messageName}, fds)

			got, err := GetNestedFieldCommentMap(fds, tc.messageName)
			if err != nil {
				t.Fatalf("Unexpected error %v", err)
			}

			// Non-Intrinsic code should be stripped out.
			delete(want, "google.protobuf.Duration")
			delete(want, "google.protobuf.Duration.nanos")
			delete(want, "google.protobuf.Duration.seconds")

			if diff := cmp.Diff(want, got); diff != "" {
				t.Errorf("GetNestedFieldCommentMap(_, %q) returned an unexpected diff (-want +got): %v", tc.messageName, diff)
			}
		})
	}
}

func TestDependencyGraph(t *testing.T) {
	fds := mustLoadTestFiledDescriptor(t)

	got, _, err := dependencyGraph(fds)
	if err != nil {
		t.Fatalf("unexpected error in dependencyGraph(): %v", err)
	}
	wanted := map[string]map[string]struct{}{
		"intrinsic.build_def.testing.TestMessage": map[string]struct{}{
			"google.protobuf.Duration":               {},
			"intrinsic.build_def.testing.SubMessage": {},
		},
		"intrinsic.build_def.testing.TestMessageB": map[string]struct{}{
			"intrinsic.build_def.testing.SubMessage":  {},
			"intrinsic.build_def.testing.SubMessageB": {},
		},
	}
	if diff := cmp.Diff(wanted, got); diff != "" {
		t.Errorf("dependencyGraph() returned an unexpected diff (-want +got): %v", diff)
	}
}

func TestAllDependencies(t *testing.T) {
	fds := mustLoadTestFiledDescriptor(t)
	graph, _, err := dependencyGraph(fds)
	if err != nil {
		t.Fatalf("unexpected error in dependencyGraph(): %v", err)
	}

	tests := []struct {
		name      string
		fullNames []string
		want      map[string]struct{}
	}{
		{
			name:      "intrinsic.build_def.testing.TestMessage",
			fullNames: []string{"intrinsic.build_def.testing.TestMessage"},
			want: map[string]struct{}{
				"google.protobuf.Duration":                {},
				"intrinsic.build_def.testing.SubMessage":  {},
				"intrinsic.build_def.testing.TestMessage": {},
			},
		},
		{
			name:      "intrinsic.build_def.testing.TestMessageB",
			fullNames: []string{"intrinsic.build_def.testing.TestMessageB"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.SubMessage":   {},
				"intrinsic.build_def.testing.SubMessageB":  {},
				"intrinsic.build_def.testing.TestMessageB": {},
			},
		},
		{
			name:      "intrinsic.build_def.testing.SubMessage",
			fullNames: []string{"intrinsic.build_def.testing.SubMessage"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.SubMessage": {},
			},
		},
		{
			name:      "intrinsic.build_def.testing.SubMessageB",
			fullNames: []string{"intrinsic.build_def.testing.SubMessageB"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.SubMessageB": {},
			},
		},
		{
			name: "multiple",
			fullNames: []string{
				"intrinsic.build_def.testing.TestMessage",
				"intrinsic.build_def.testing.TestMessageB",
			},
			want: map[string]struct{}{
				"google.protobuf.Duration":                 {},
				"intrinsic.build_def.testing.SubMessage":   {},
				"intrinsic.build_def.testing.SubMessageB":  {},
				"intrinsic.build_def.testing.TestMessage":  {},
				"intrinsic.build_def.testing.TestMessageB": {},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := allDependencies(tc.fullNames, graph)
			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("allDependencies(%v, %v) returned an unexpected diff (-want +got): %v", tc.fullNames, graph, diff)
			}
		})
	}
}

func TestPruneSourceCodeInfo(t *testing.T) {
	originalFDS := mustLoadTestFiledDescriptor(t)

	tests := []struct {
		name      string
		fullNames []string
		want      map[string]bool
	}{
		{
			name:      "intrinsic.build_def.testing.TestMessage",
			fullNames: []string{"intrinsic.build_def.testing.TestMessage"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     true,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": true,
			},
		},
		{
			name:      "intrinsic.build_def.testing.TestMessageB",
			fullNames: []string{"intrinsic.build_def.testing.TestMessageB"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     true,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": true,
			},
		},
		{
			name:      "intrinsic.build_def.testing.SubMessage",
			fullNames: []string{"intrinsic.build_def.testing.SubMessage"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     false,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": true,
			},
		},
		{
			name:      "intrinsic.build_def.testing.SubMessageB",
			fullNames: []string{"intrinsic.build_def.testing.SubMessageB"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     true,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": false,
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			fds := proto.Clone(originalFDS).(*dpb.FileDescriptorSet)
			PruneSourceCodeInfo(tc.fullNames, fds)

			hasComments := map[string]bool{}
			for _, f := range fds.GetFile() {
				hasComments[f.GetName()] = len(f.GetSourceCodeInfo().GetLocation()) > 0
				for _, l := range f.GetSourceCodeInfo().GetLocation() {
					if l.LeadingDetachedComments != nil {
						t.Errorf("PruneSourceCodeInfo(%v) did not remove all detached comments", tc.fullNames)
					}
				}
			}
			if diff := cmp.Diff(tc.want, hasComments); diff != "" {
				t.Errorf("PruneSourceCodeInfo(%v) made an unexpected diff (-want +got): %v", tc.fullNames, diff)
			}
		})
	}
}
