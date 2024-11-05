// Copyright 2023 Intrinsic Innovation LLC

// Package listreleasedversions defines the list_released_versions command that lists versions of a service in a ServiceCatalog.
package listreleasedversions

import (
	"context"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	acgrpcpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	acpb "intrinsic/assets/catalog/proto/v1/asset_catalog_go_grpc_proto"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/listutils"
	atpb "intrinsic/assets/proto/asset_type_go_proto"
	viewpb "intrinsic/assets/proto/view_go_proto"
	"intrinsic/assets/services/inctl/servicedescriptions"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const pageSize int64 = 50

func listReleasedVersions(ctx context.Context, client acgrpcpb.AssetCatalogClient, serviceID string, prtr printer.Printer) error {
	filter := &acpb.ListAssetsRequest_AssetFilter{
		Id:         proto.String(serviceID),
		AssetTypes: []atpb.AssetType{atpb.AssetType_ASSET_TYPE_SERVICE},
	}
	services, err := listutils.ListAllAssets(ctx, client, pageSize, viewpb.AssetViewType_ASSET_VIEW_TYPE_VERSIONS, filter)
	if err != nil {
		return errors.Wrap(err, "could not list service versions")
	}
	sd, err := servicedescriptions.FromCatalogServices(services)
	if err != nil {
		return err
	}
	prtr.Print(sd.IDVersionsString())
	return nil
}

// GetCommand returns a command to list versions of a released service in the catalog.
func GetCommand() *cobra.Command {
	flags := cmdutils.NewCmdFlags()
	cmd := &cobra.Command{Use: "list_released_versions service_id",
		Short: "List versions of a released service in the catalog",
		Args:  cobra.ExactArgs(1), // serviceId
		RunE: func(cmd *cobra.Command, args []string) error {
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
			return listReleasedVersions(cmd.Context(), client, args[0], prtr)
		},
	}
	flags.SetCommand(cmd)
	return cmd
}
