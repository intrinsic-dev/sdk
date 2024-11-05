// Copyright 2023 Intrinsic Innovation LLC

// Package listutils provides utility functions for listing assets from a catalog.
package listutils

import (
	"context"
	"fmt"

	"google.golang.org/grpc"
	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	viewpb "intrinsic/assets/proto/view_go_proto"
)

type assetLister interface {
	ListAssets(ctx context.Context, req *acpb.ListAssetsRequest, options ...grpc.CallOption) (*acpb.ListAssetsResponse, error)
}

// ListAllAssets lists all assets from a catalog that match the specified filter.
func ListAllAssets(ctx context.Context, client assetLister, pageSize int64, view viewpb.AssetViewType, filter *acpb.ListAssetsRequest_AssetFilter) ([]*acpb.Asset, error) {
	nextPageToken := ""
	var assets []*acpb.Asset
	for {
		resp, err := client.ListAssets(ctx, &acpb.ListAssetsRequest{
			View:         view,
			PageToken:    nextPageToken,
			PageSize:     pageSize,
			StrictFilter: filter,
		})
		if err != nil {
			return nil, fmt.Errorf("could not list assets: %w", err)
		}
		assets = append(assets, resp.GetAssets()...)
		nextPageToken = resp.GetNextPageToken()
		if nextPageToken == "" {
			break
		}
	}
	return assets, nil
}
