// Copyright 2023 Intrinsic Innovation LLC

// Package listreleasedversions defines the skill list_released_versions command which lists versions of a skill in a catalog.
package listreleasedversions

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
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

const pageSize int64 = 50

var cmdFlags = cmdutils.NewCmdFlags()

func listReleasedVersions(ctx context.Context, client acgrpcpb.AssetCatalogClient, skillID string, prtr printer.Printer) error {
	filter := &acpb.ListAssetsRequest_AssetFilter{
		Id:         proto.String(skillID),
		AssetTypes: []atpb.AssetType{atpb.AssetType_ASSET_TYPE_SKILL},
	}
	skills, err := listutils.ListAllAssets(ctx, client, pageSize, viewpb.AssetViewType_ASSET_VIEW_TYPE_VERSIONS, filter)
	if err != nil {
		return errors.Wrap(err, "could not list skill versions")
	}
	ad, err := assetdescriptions.FromCatalogAssets(skills)
	if err != nil {
		return err
	}
	prtr.Print(assetdescriptions.IDVersionsStringView{Descriptions: ad})
	return nil
}

var listReleasedVersionsCmd = &cobra.Command{
	Use:   "list_released_versions [skill_id]",
	Short: "List versions of a released skill in the catalog",
	Args:  cobra.ExactArgs(1), // skillId
	RunE: func(cmd *cobra.Command, args []string) error {
		conn, err := clientutils.DialCatalogFromInctl(cmd, cmdFlags)
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

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedVersionsCmd)
	cmdFlags.SetCommand(listReleasedVersionsCmd)

}
