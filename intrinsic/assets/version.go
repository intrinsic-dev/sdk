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
	iagrpcpb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
	iapb "intrinsic/assets/proto/installed_assets_go_grpc_proto"
)

var (
	errIDNotFound = errors.New("there is no currently installed resource with ID")
	errAmbiguous  = errors.New("could not disambiguate ID")
)

// Autofill updates an unspecified version in an IdVersion proto to be the only
// available version of the specified Id proto.  An error is returned if there
// is not exactly one version installed.
func Autofill(ctx context.Context, client iagrpcpb.InstalledAssetsClient, idOrIDVersion *idpb.IdVersion) error {
	if idOrIDVersion.GetVersion() != "" {
		return nil
	}
	versions, err := List(ctx, client, idOrIDVersion.GetId())
	if err != nil {
		return err
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

// List returns all installed versions of a particular asset id.
func List(ctx context.Context, client iagrpcpb.InstalledAssetsClient, id *idpb.Id) ([]string, error) {
	var versions []string
	nextPageToken := ""
	for {
		resp, err := client.ListInstalledAssets(ctx, &iapb.ListInstalledAssetsRequest{
			PageToken: nextPageToken,
		})
		if err != nil {
			return nil, fmt.Errorf("could not retrieve currently installed resources: %w", err)
		}
		for _, r := range resp.GetInstalledAssets() {
			if proto.Equal(id, r.GetMetadata().GetIdVersion().GetId()) {
				versions = append(versions, r.GetMetadata().GetIdVersion().GetVersion())
			}
		}
		nextPageToken = resp.GetNextPageToken()
		if nextPageToken == "" {
			break
		}
	}
	return versions, nil
}
