// Copyright 2023 Intrinsic Innovation LLC

package client

import (
	"context"
	"fmt"
	"strings"

	"google.golang.org/grpc"
)

type renamer func(string) string

type renameConnection struct {
	delegate grpc.ClientConnInterface
	rename   renamer
}

// NewRenamedConnection wraps provided connection to allow for service renaming.
// It returns thin wrapper which renames service portion on method into newName.
func NewRenamedConnection(conn grpc.ClientConnInterface, newName string) grpc.ClientConnInterface {
	return &renameConnection{
		delegate: conn,
		rename: func(s string) string {
			// method string is /<service>/<Method> ...
			methodSeparator := strings.LastIndex(s, "/")
			return fmt.Sprintf("/%s/%s", newName, s[methodSeparator+1:])
		},
	}
}

func (r *renameConnection) Invoke(ctx context.Context, method string, args any, reply any, opts ...grpc.CallOption) error {
	return r.delegate.Invoke(ctx, r.rename(method), args, reply, opts...)
}

func (r *renameConnection) NewStream(ctx context.Context, desc *grpc.StreamDesc, method string, opts ...grpc.CallOption) (grpc.ClientStream, error) {
	return r.delegate.NewStream(ctx, desc, r.rename(method), opts...)
}
