// Copyright 2023 Intrinsic Innovation LLC

// Package directupload implements direct upload transferer for inctl tools
// and discovery mechanism for finding the best possible upload path to the target
package directupload

import (
	"context"

	"google.golang.org/grpc"
	artifactgrpcpb "intrinsic/storage/artifacts/proto/artifact_go_grpc_proto"
)

// TargetDiscovery interface represent an implementation of the discovery
// mechanism to find the most efficient path between client and target workcell
// to maximize speed of the upload.
type TargetDiscovery interface {
	// GetClient gets ArtifactServiceApiClient with the best possible path
	GetClient(ctx context.Context) (artifactgrpcpb.ArtifactServiceApiClient, error)
}

// NewFromConnection creates new TargetDiscovery implementation using provided
// grpc.ClientConnection to create a client.
func NewFromConnection(conn *grpc.ClientConn) TargetDiscovery {
	return &staticConnection{conn: conn}
}

type staticConnection struct {
	conn *grpc.ClientConn
}

func (s *staticConnection) GetClient(_ context.Context) (artifactgrpcpb.ArtifactServiceApiClient, error) {
	return artifactgrpcpb.NewArtifactServiceApiClient(s.conn), nil
}
