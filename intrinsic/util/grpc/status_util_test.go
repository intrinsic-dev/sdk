// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

package statusutil

import (
	"context"
	"fmt"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	"github.com/pkg/errors"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/local"
	"google.golang.org/grpc/status"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	"intrinsic/testing/grpctest"
	pgrpcpb "intrinsic/util/grpc/testing/ping_go_grpc_proto"
)

var (
	deadlineExceeded = status.Errorf(codes.DeadlineExceeded, "test")
)

func TestWrap(t *testing.T) {
	tests := []struct {
		desc   string
		err    error
		format string
		args   []any
		want   error
	}{
		{
			desc: "nil returns nil",
		},
		{
			desc: "without context or args",
			err:  status.Errorf(codes.DeadlineExceeded, "test"),
			want: status.Errorf(codes.DeadlineExceeded, ": test"),
		},
		{
			desc:   "without args",
			err:    status.Errorf(codes.InvalidArgument, "test"),
			format: "no args",
			want:   status.Errorf(codes.InvalidArgument, "no args: test"),
		},
		{
			desc:   "with args",
			err:    status.Errorf(codes.Aborted, "test"),
			format: "with args %v %v",
			args: []any{
				"1",
				"2",
			},
			want: status.Errorf(codes.Aborted, "with args 1 2: test"),
		},
		{
			desc:   "is unknown on a non-grpc status error",
			err:    fmt.Errorf("something else"),
			format: "an attempt was made",
			want:   status.Errorf(codes.Unknown, "an attempt was made: something else"),
		},
		{
			desc:   "has code on wrapped error",
			err:    fmt.Errorf("inner %w", deadlineExceeded),
			format: "context",
			want:   status.Errorf(codes.DeadlineExceeded, "context: inner rpc error: code = DeadlineExceeded desc = test"),
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			got := Wrap(tc.err, tc.format, tc.args...)
			if diff := cmp.Diff(tc.want, got, cmpopts.EquateErrors()); diff != "" {
				t.Errorf("Wrap(...) returned unexpected result, diff (-want +got):\n%s", diff)
			}
		})
	}
}

func TestObscure(t *testing.T) {
	tests := []struct {
		desc   string
		err    error
		format string
		args   []any
		want   error
	}{
		{
			desc: "nil returns nil",
		},
		{
			desc: "without context or args",
			err:  status.Errorf(codes.DeadlineExceeded, "test"),
			want: status.Errorf(codes.DeadlineExceeded, ""),
		},
		{
			desc:   "without args",
			err:    status.Errorf(codes.InvalidArgument, "test"),
			format: "no args",
			want:   status.Errorf(codes.InvalidArgument, "no args"),
		},
		{
			desc:   "with args",
			err:    status.Errorf(codes.Aborted, "test"),
			format: "with args %v %v",
			args: []any{
				"1",
				"2",
			},
			want: status.Errorf(codes.Aborted, "with args 1 2"),
		},
		{
			desc:   "is unknown on a non-grpc status error",
			err:    fmt.Errorf("something else"),
			format: "an attempt was made",
			want:   status.Errorf(codes.Unknown, "an attempt was made"),
		},
		{
			desc:   "has code on wrapped error",
			err:    fmt.Errorf("inner %w", deadlineExceeded),
			format: "context",
			want:   status.Errorf(codes.DeadlineExceeded, "context"),
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			got := Obscure(tc.err, tc.format, tc.args...)
			if diff := cmp.Diff(tc.want, got, cmpopts.EquateErrors()); diff != "" {
				t.Errorf("Obscure(...) returned unexpected result, diff (-want +got):\n%s", diff)
			}
		})
	}
}

func mustStartServer(t *testing.T, s pgrpcpb.PingServiceServer) pgrpcpb.PingServiceClient {
	t.Helper()
	server := grpc.NewServer()
	pgrpcpb.RegisterPingServiceServer(server, s)
	address := grpctest.StartServerT(t, server)
	connection, err := grpc.Dial(address, grpc.WithTransportCredentials(local.NewCredentials()))
	if err != nil {
		t.Fatalf("Failed to dial server: %v", err)
	}
	t.Cleanup(func() { connection.Close() })

	return pgrpcpb.NewPingServiceClient(connection)
}

type wrapDeadlineExceeded struct{}

func (*wrapDeadlineExceeded) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, Wrap(deadlineExceeded, "context")
}

type fmtWrapContext struct{}

func (*fmtWrapContext) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, fmt.Errorf("context: %w", deadlineExceeded)
}

type fmtMultipleLayers struct{}

func (*fmtMultipleLayers) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	a := fmt.Errorf("a: %w", deadlineExceeded)
	b := fmt.Errorf("b: %w", a)
	return nil, fmt.Errorf("c: %w", b)
}

type errorsWrap struct{}

func (*errorsWrap) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, errors.Wrap(deadlineExceeded, "context")
}

func TestWrapWithServer(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		desc   string
		server pgrpcpb.PingServiceServer
		want   error
	}{
		{
			desc:   "wrap without args",
			server: new(wrapDeadlineExceeded),
			want:   status.Errorf(codes.DeadlineExceeded, "context: test"),
		},
		{
			desc:   "wrap using fmt.Errorf repeats code",
			server: new(fmtWrapContext),
			want:   status.Errorf(codes.DeadlineExceeded, "context: rpc error: code = DeadlineExceeded desc = test"),
		},
		{
			desc:   "wrap using errors.Wrap repeats code",
			server: new(fmtWrapContext),
			want:   status.Errorf(codes.DeadlineExceeded, "context: rpc error: code = DeadlineExceeded desc = test"),
		},
		{
			desc:   "status in any layer is unwrapped for client when using fmt",
			server: new(fmtMultipleLayers),
			want:   status.Errorf(codes.DeadlineExceeded, "c: b: a: rpc error: code = DeadlineExceeded desc = test"),
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			c := mustStartServer(t, tc.server)
			_, got := c.Ping(ctx, new(emptypb.Empty))
			if diff := cmp.Diff(tc.want, got, cmpopts.EquateErrors()); diff != "" {
				t.Errorf("Wrap(...) returned unexpected result, diff (-want +got):\n%s", diff)
			}
		})
	}
}
