// Copyright 2023 Intrinsic Innovation LLC

package resolvercache

import (
	"context"
	"testing"

	descriptorpb "github.com/golang/protobuf/protoc-gen-go/descriptor"
	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	"google.golang.org/protobuf/encoding/prototext"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/testing/protocmp"
	anypb "google.golang.org/protobuf/types/known/anypb"
	apb "intrinsic/util/proto/testing/diamond_a_go_proto"
	bpb "intrinsic/util/proto/testing/diamond_b_go_proto"
	"intrinsic/util/proto/testing/prototestutil"
)

var (
	aSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&apb.A{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
	bSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&apb.A{}).ProtoReflect().Descriptor().ParentFile()),
			protodesc.ToFileDescriptorProto((&bpb.B{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
	incompleteSet = &descriptorpb.FileDescriptorSet{
		File: []*descriptorpb.FileDescriptorProto{
			protodesc.ToFileDescriptorProto((&bpb.B{}).ProtoReflect().Descriptor().ParentFile()),
		},
	}
)

type specificError struct{}

func (*specificError) Error() string {
	return "specific error"
}

var specificErr = new(specificError)

func TestGetPropagatesFetchError(t *testing.T) {
	ctx := context.Background()
	rc := NewResolverCache(
		FetchForFileDescriptorSet(func(_ context.Context, _ string) (*descriptorpb.FileDescriptorSet, error) {
			return nil, specificErr
		}),
	)

	value := "nothing really matters"
	_, err := rc.Get(ctx, value)
	if diff := cmp.Diff(specificErr, err, cmpopts.EquateErrors()); diff != "" {
		t.Errorf("rc.Get(ctx, %v) returned unexpected error, diff (-want +got):\n%s", value, diff)
	}
}

func TestFetchPropagatesErrorsCreatingResolver(t *testing.T) {
	ctx := context.Background()
	rc := NewResolverCache(
		FetchForFileDescriptorSet(func(_ context.Context, _ string) (*descriptorpb.FileDescriptorSet, error) {
			return incompleteSet, nil
		}),
	)
	if _, err := rc.Get(ctx, "nothing really matters"); err == nil {
		t.Errorf("Unexpected success from rc.Get() = %v, want error", err)
	}
}

func TestForceAlwaysCallsFetch(t *testing.T) {
	ctx := context.Background()
	calls := 0
	rc := NewResolverCache(
		FetchForFileDescriptorSet(func(_ context.Context, _ string) (*descriptorpb.FileDescriptorSet, error) {
			calls++
			return aSet, nil
		}),
	)

	id := "anything"
	for _, want := range []int{1, 2, 3} {
		if _, err := rc.Force(ctx, id); err != nil {
			t.Fatalf("Unexpected error from rc.Force(ctx, %v) = %v, want nil", id, err)
		}
		if got := calls; got != want {
			t.Errorf("got %d calls, want %d", got, want)
		}
	}
}

func TestGetAvoidsFetchWhenCached(t *testing.T) {
	ctx := context.Background()
	calls := 0
	rc := NewResolverCache(
		FetchForFileDescriptorSet(func(_ context.Context, _ string) (*descriptorpb.FileDescriptorSet, error) {
			calls++
			return aSet, nil
		}),
	)

	id := "anything"
	for _, want := range []int{1, 1, 1} {
		if _, err := rc.Get(ctx, id); err != nil {
			t.Fatalf("Unexpected error from rc.Get(ctx, %v) = %v, want nil", id, err)
		}
		if got := calls; got != want {
			t.Errorf("got %d calls, want %d", got, want)
		}
	}
}

func TestGetUsesFetchedValueBasedOnId(t *testing.T) {
	ctx := context.Background()
	rc := NewResolverCache(
		FetchForFileDescriptorSet(func(_ context.Context, id string) (*descriptorpb.FileDescriptorSet, error) {
			switch id {
			case "a":
				return aSet, nil
			case "b":
				return bSet, nil
			case "incomplete":
				return incompleteSet, nil
			case "error":
				return nil, specificErr
			default:
				t.Fatalf("Unexpected id of %q.  The test case should request known value.", id)
				return nil, nil
			}
		}),
	)

	tests := []struct {
		desc    string
		id      string
		value   string
		want    proto.Message
		wantErr error
	}{
		{
			desc: "simple message resolves",
			id:   "a",
			value: `[type.googleapis.com/intrinsic_proto.test.A] {
				value: "Test"
			}`,
			want: prototestutil.MustWrapInAny(t, &apb.A{
				Value: "Test",
			}),
		},
		{
			desc:    "get returns error provided by fetch function",
			id:      "error",
			wantErr: specificErr,
		},
		{
			desc: "an encosing message resolves with correct descriptors",
			id:   "b",
			value: `[type.googleapis.com/intrinsic_proto.test.B] {
				a {
					value: "Test"
				}
			}`,
			want: prototestutil.MustWrapInAny(t, &bpb.B{
				A: &apb.A{
					Value: "Test",
				},
			}),
		},
		{
			desc:    "creating a resolver for an incomplete file descriptor set fails",
			id:      "incomplete",
			wantErr: cmpopts.AnyError,
		},
	}
	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			resolver, err := rc.Get(ctx, tc.id)
			if diff := cmp.Diff(tc.wantErr, err, cmpopts.EquateErrors()); diff != "" {
				t.Errorf("rc.Get(ctx, %v) returned unexpected error, diff (-want +got):\n%s", tc.id, diff)
			}
			if tc.wantErr != nil {
				return
			}

			got := new(anypb.Any)
			options := prototext.UnmarshalOptions{Resolver: resolver}

			if err = options.Unmarshal([]byte(tc.value), got); err != nil {
				t.Errorf("Unexpected error from options.Unmarshal(%v) = %v, want nil", tc.value, err)
			}
			if diff := cmp.Diff(tc.want, got, protocmp.Transform()); diff != "" {
				t.Errorf("prototext.Unmarshal(%v) returned unexpected diff (-want +got):\n%s", tc.value, diff)
			}
		})
	}
}
