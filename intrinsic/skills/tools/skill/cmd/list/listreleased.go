// Copyright 2023 Intrinsic Innovation LLC

// Package listreleased defines the skill list_released command which lists skills in a catalog.
package listreleased

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	releasetagpb "intrinsic/assets/proto/release_tag_go_proto"
	viewpb "intrinsic/assets/proto/view_go_proto"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/listutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

var cmdFlags = cmdutils.NewCmdFlags()

// listAllSkills retrieves skills by pagination
func listAllSkills(ctx context.Context, client skillcataloggrpcpb.SkillCatalogClient, prtr printer.Printer, pageSize int64) error {
	req := &skillcatalogpb.ListSkillsRequest{
		View:      viewpb.AssetViewType_ASSET_VIEW_TYPE_BASIC,
		PageToken: "",
		PageSize:  pageSize,
		StrictFilter: &skillcatalogpb.ListSkillsRequest_Filter{
			ReleaseTag: releasetagpb.ReleaseTag_RELEASE_TAG_DEFAULT.Enum(),
		}}
	skills, err := listutil.ListWithCatalogClient(ctx, client, req)
	if err != nil {
		return err
	}
	sd, err := listutil.SkillDescriptionsFromCatalogSkills(skills)
	if err != nil {
		return err
	}
	prtr.Print(sd)
	return nil
}

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

		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}
		client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
		var pageSize int64 = 50
		if err := listAllSkills(cmd.Context(), client, prtr, pageSize); err != nil {
			return err
		}

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedCmd)
	cmdFlags.SetCommand(listReleasedCmd)

}
