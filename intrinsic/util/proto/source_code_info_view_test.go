// Copyright 2023 Intrinsic Innovation LLC

package sourcecodeinfoview

import (
	"testing"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/proto"
	"intrinsic/util/proto/protoio"
)

const (
	testFile = "intrinsic/util/proto/build_defs/testing/test_message_proto_descriptors_transitive_set_sci.proto.bin"
)

func mustLoadTestFileDescriptor(t *testing.T) *dpb.FileDescriptorSet {
	t.Helper()
	fileDescriptorSet := new(dpb.FileDescriptorSet)
	if err := protoio.ReadBinaryProto(testFile, fileDescriptorSet); err != nil {
		t.Fatalf("Unable to read %v", testFile)
	}
	return fileDescriptorSet
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
			protoDescriptor: mustLoadTestFileDescriptor(t),
			messageName:     "some.message",
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			_, err := NestedFieldCommentMap(tc.protoDescriptor, tc.messageName)
			if err == nil {
				t.Errorf("NestedFieldCommentMap(%v, %v): unexpectedly succeeded", tc.protoDescriptor, tc.messageName)
			}
		})
	}
}

func TestGetLeadingCommentsByFieldNameWithValidNameSucceeds(t *testing.T) {
	fds := mustLoadTestFileDescriptor(t)

	tests := []struct {
		name            string
		messageFullName string
		want            map[string]string
	}{
		{
			name:            "intrinsic.build_def.testing.TestMessageB",
			messageFullName: "intrinsic.build_def.testing.TestMessageB",
			want: map[string]string{
				"intrinsic.build_def.testing.SubMessage":                         "",
				"intrinsic.build_def.testing.SubMessage.my_double":               " Your favorite double of all time.\n",
				"intrinsic.build_def.testing.SubMessageB":                        " A submessage\n",
				"intrinsic.build_def.testing.SubMessageB.hello":                  " a field\n",
				"intrinsic.build_def.testing.TestMessageB":                       " A test message\n",
				"intrinsic.build_def.testing.TestMessageB.submesage_b":           "",
				"intrinsic.build_def.testing.TestMessageB.submessage":            " A submessage\n",
				"intrinsic.build_def.testing.TestMessageB.submessage_no_comment": "",
			},
		},
		{
			name:            "intrinsic.build_def.testing.TestService",
			messageFullName: "intrinsic.build_def.testing.TestService",
			want: map[string]string{
				"intrinsic.build_def.testing.GetInfoRequest":            " A test request message\n",
				"intrinsic.build_def.testing.GetInfoRequest.name":       " The item's name.\n",
				"intrinsic.build_def.testing.GetInfoRequest.submessage": " A submessage\n",
				"intrinsic.build_def.testing.GetInfoResponse":           " A test response message\n",
				"intrinsic.build_def.testing.SubMessage":                "",
				"intrinsic.build_def.testing.SubMessage.my_double":      " Your favorite double of all time.\n",
				"intrinsic.build_def.testing.TestService":               " A test service\n",
				"intrinsic.build_def.testing.TestService.GetInfo":       " Retrieves information.\n",
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got, err := NestedFieldCommentMap(fds, tc.messageFullName)
			if err != nil {
				t.Fatalf("NestedFieldCommentMap(_, %q) returned an unexpected error: %v", tc.messageFullName, err)
			}

			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("NestedFieldCommentMap(_, %q) returned an unexpected diff (-want +got): %v", tc.messageFullName, diff)
			}
		})
	}
}

func TestPruningDoesNotAffectNestedFieldCommentMap(t *testing.T) {
	originalFDS := mustLoadTestFileDescriptor(t)

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
		{
			name:        "intrinsic.build_def.testing.TestService",
			messageName: "intrinsic.build_def.testing.TestService",
		},
		{
			name:        "intrinsic.build_def.testing.GetInfoRequest",
			messageName: "intrinsic.build_def.testing.GetInfoRequest",
		},
		{
			name:        "intrinsic.build_def.testing.GetInfoResponse",
			messageName: "intrinsic.build_def.testing.GetInfoResponse",
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			fds := proto.Clone(originalFDS).(*dpb.FileDescriptorSet)
			want, err := NestedFieldCommentMap(fds, tc.messageName)
			if err != nil {
				t.Fatalf("Unexpected error %v", err)
			}
			PruneSourceCodeInfo([]string{tc.messageName}, fds)

			got, err := NestedFieldCommentMap(fds, tc.messageName)
			if err != nil {
				t.Fatalf("Unexpected error %v", err)
			}

			// Non-Intrinsic code should be stripped out.
			delete(want, "google.protobuf.Duration")
			delete(want, "google.protobuf.Duration.nanos")
			delete(want, "google.protobuf.Duration.seconds")

			if diff := cmp.Diff(want, got); diff != "" {
				t.Errorf("NestedFieldCommentMap(_, %q) returned an unexpected diff (-want +got): %v", tc.messageName, diff)
			}
		})
	}
}

func TestDependencyGraph(t *testing.T) {
	fds := mustLoadTestFileDescriptor(t)

	got, _, err := dependencyGraph(fds)
	if err != nil {
		t.Fatalf("unexpected error in dependencyGraph(): %v", err)
	}
	wanted := map[string]map[string]struct{}{
		"intrinsic.build_def.testing.TestMessage": map[string]struct{}{
			"intrinsic.build_def.testing.TestMessage": {},
			"intrinsic.build_def.testing.SubMessage":  {},
			"google.protobuf.Duration":                {},
		},
		"intrinsic.build_def.testing.TestMessageB": map[string]struct{}{
			"intrinsic.build_def.testing.TestMessageB": {},
			"intrinsic.build_def.testing.SubMessage":   {},
			"intrinsic.build_def.testing.SubMessageB":  {},
		},
		"intrinsic.build_def.testing.SubMessage": map[string]struct{}{
			"intrinsic.build_def.testing.SubMessage": {},
		},
		"intrinsic.build_def.testing.SubMessageB": map[string]struct{}{
			"intrinsic.build_def.testing.SubMessageB": {},
		},
		"intrinsic.build_def.testing.TestService": map[string]struct{}{
			"intrinsic.build_def.testing.TestService":     {},
			"intrinsic.build_def.testing.GetInfoRequest":  {},
			"intrinsic.build_def.testing.GetInfoResponse": {},
		},
		"intrinsic.build_def.testing.GetInfoRequest": map[string]struct{}{
			"intrinsic.build_def.testing.GetInfoRequest": {},
			"intrinsic.build_def.testing.SubMessage":     {},
		},
		"intrinsic.build_def.testing.GetInfoResponse": map[string]struct{}{
			"intrinsic.build_def.testing.GetInfoResponse": {},
		},
		"google.protobuf.Duration": map[string]struct{}{
			"google.protobuf.Duration": {},
		},
	}
	if diff := cmp.Diff(wanted, got); diff != "" {
		t.Errorf("dependencyGraph() returned an unexpected diff (-want +got): %v", diff)
	}
}

func TestAllDependencies(t *testing.T) {
	fds := mustLoadTestFileDescriptor(t)
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
			name:      "intrinsic.build_def.testing.TestService",
			fullNames: []string{"intrinsic.build_def.testing.TestService"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.TestService":     {},
				"intrinsic.build_def.testing.GetInfoRequest":  {},
				"intrinsic.build_def.testing.GetInfoResponse": {},
				"intrinsic.build_def.testing.SubMessage":      {},
			},
		},
		{
			name:      "intrinsic.build_def.testing.GetInfoRequest",
			fullNames: []string{"intrinsic.build_def.testing.GetInfoRequest"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.GetInfoRequest": {},
				"intrinsic.build_def.testing.SubMessage":     {},
			},
		},
		{
			name:      "intrinsic.build_def.testing.GetInfoResponse",
			fullNames: []string{"intrinsic.build_def.testing.GetInfoResponse"},
			want: map[string]struct{}{
				"intrinsic.build_def.testing.GetInfoResponse": {},
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
	originalFDS := mustLoadTestFileDescriptor(t)

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
		{
			name:      "intrinsic.build_def.testing.TestService",
			fullNames: []string{"intrinsic.build_def.testing.TestService"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     true,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": true,
			},
		},
		{
			name:      "intrinsic.build_def.testing.GetInfoRequest",
			fullNames: []string{"intrinsic.build_def.testing.GetInfoRequest"},
			want: map[string]bool{
				"google/protobuf/duration.proto":                                 false,
				"intrinsic/util/proto/build_defs/testing/test_message.proto":     true,
				"intrinsic/util/proto/build_defs/testing/test_message_dep.proto": true,
			},
		},
		{
			name:      "intrinsic.build_def.testing.GetInfoResponse",
			fullNames: []string{"intrinsic.build_def.testing.GetInfoResponse"},
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
