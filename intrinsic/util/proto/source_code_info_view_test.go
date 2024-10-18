// Copyright 2023 Intrinsic Innovation LLC

package sourcecodeinfoview

import (
	"testing"

	dpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
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
		{
			desc:            "no source code info",
			protoDescriptor: clearSourceCodeInfo(mustLoadTestFiledDescriptor(t)),
			messageName:     "intrinsic.build_def.testing.TestMessageB",
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
