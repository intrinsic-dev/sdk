// Copyright 2023 Intrinsic Innovation LLC

// Package listreleased defines the skill list_released command which lists skills in a catalog.
package listreleased

import (
	"context"
	"fmt"

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

// listAllSkills retrieves skills by pagination.
func listAllSkills(ctx context.Context, client acgrpcpb.AssetCatalogClient, prtr printer.Printer) error {
	filter := &acpb.ListAssetsRequest_AssetFilter{
		AssetTypes:  []atpb.AssetType{atpb.AssetType_ASSET_TYPE_SKILL},
		OnlyDefault: proto.Bool(true),
	}
	skills, err := listutils.ListAllAssets(ctx, client, pageSize, viewpb.AssetViewType_ASSET_VIEW_TYPE_BASIC, filter)
	if err != nil {
		return err
	}
	ad, err := assetdescriptions.FromCatalogAssets(skills)
	if err != nil {
		return err
	}
	prtr.Print(assetdescriptions.IDVersionsStringView{Descriptions: ad})
	return nil
}

var cmdFlags = cmdutils.NewCmdFlags()

var listReleasedCmd = &cobra.Command{
	Use:   "list_released",
	Short: "List released skills in the catalog",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		conn, err := clientutils.DialCatalogFromInctl(cmd, cmdFlags)
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()
		client := acgrpcpb.NewAssetCatalogClient(conn)
		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}
		return listAllSkills(cmd.Context(), client, prtr)
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedCmd)
	cmdFlags.SetCommand(listReleasedCmd)

}
