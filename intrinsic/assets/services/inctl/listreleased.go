// Copyright 2023 Intrinsic Innovation LLC

// Package listreleased defines the list_released command that lists services in a ServiceCatalog.
package listreleased

import (
	"context"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/catalog/assetdescriptions"
	acgrpcpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/listutils"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
	viewpb "intrinsic/assets/proto/view_go_proto"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const pageSize int64 = 50

func listAllServices(ctx context.Context, client acgrpcpb.AssetCatalogClient, prtr printer.Printer) error {
	filter := &acpb.ListAssetsRequest_AssetFilter{
		AssetTypes:  []atpb.AssetType{atpb.AssetType_ASSET_TYPE_SERVICE},
		OnlyDefault: proto.Bool(true),
	}
	services, err := listutils.ListAllAssets(ctx, client, pageSize, viewpb.AssetViewType_ASSET_VIEW_TYPE_BASIC, filter)
	if err != nil {
		return err
	}
	ad, err := assetdescriptions.FromCatalogAssets(services)
	if err != nil {
		return err
	}
	prtr.Print(assetdescriptions.IDVersionsStringView{Descriptions: ad})
	return nil
}

// GetCommand returns a command to list released services.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{
		Use:   "list_released",
		Short: "List services from the catalog",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			conn, err := clientutils.DialCatalogFromInctl(cmd, flags)
			if err != nil {
				return errors.Wrap(err, "failed to create client connection")
			}
			defer conn.Close()
			client := acgrpcpb.NewAssetCatalogClient(conn)
			prtr, err := printer.NewPrinter(root.FlagOutput)
			if err != nil {
				return err
			}
			return listAllServices(cmd.Context(), client, prtr)
		},
	}
	flags.SetCommand(cmd)
	return cmd
}
