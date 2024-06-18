// Copyright 2023 Intrinsic Innovation LLC

// Package version provides utilities for working with and looking up versions
// of assets.
package version

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"google.golang.org/protobuf/proto"
	"intrinsic/assets/idutils"
	idpb "intrinsic/assets/proto/id_go_proto"
	rrgrpcpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
	rrpb "intrinsic/resources/proto/resource_registry_go_grpc_proto"
)

var (
	errIDNotFound = errors.New("there is no currently installed resource with ID")
	errAmbiguous  = errors.New("could not disambiguate ID")
)

// Autofill updates an unspecified version in an IdVersion proto to be the only
// available version of the specified Id proto.  An error is returned if there
// is not exactly one version installed.
func Autofill(ctx context.Context, client rrgrpcpb.ResourceRegistryClient, idOrIDVersion *idpb.IdVersion) error {
	if idOrIDVersion.GetVersion() != "" {
		return nil
	}
	var versions []string
	nextPageToken := ""
	for {
		resp, err := client.ListResources(ctx, &rrpb.ListResourcesRequest{
			PageToken: nextPageToken,
		})
		if err != nil {
			return fmt.Errorf("could not retrieve currently installed resources: %w", err)
		}
		for _, r := range resp.GetResources() {
			if proto.Equal(idOrIDVersion.GetId(), r.GetMetadata().GetIdVersion().GetId()) {
				versions = append(versions, r.GetMetadata().GetIdVersion().GetVersion())
			}
		}
		nextPageToken = resp.GetNextPageToken()
		if nextPageToken == "" {
			break
		}
	}
	id, err := idutils.IDFromProto(idOrIDVersion.GetId())
	if err != nil {
		return err
	}
	if len(versions) == 0 {
		return fmt.Errorf("%w %q", errIDNotFound, id)
	} else if len(versions) > 1 {
		return fmt.Errorf("%w %q as there are multiple installed versions that match: %v", errAmbiguous, id, strings.Join(versions, ","))
	}
	idOrIDVersion.Version = versions[0]
	return nil
}
