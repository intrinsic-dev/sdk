// Copyright 2023 Intrinsic Innovation LLC

// Package listreleasedversions defines the skill list_released_versions command which lists versions of a skill in a catalog.
package listreleasedversions

import (
	"fmt"

	"github.com/spf13/cobra"
	"google.golang.org/protobuf/proto"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	viewpb "intrinsic/assets/proto/view_go_proto"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/listutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

var cmdFlags = cmdutils.NewCmdFlags()

var listReleasedVersionsCmd = &cobra.Command{
	Use:   "list_released_versions [skill_id]",
	Short: "List versions of a released skill in the catalog",
	Args:  cobra.ExactArgs(1), // skillId
	RunE: func(cmd *cobra.Command, args []string) error {
		conn, err := clientutils.DialCatalogFromInctl(cmd, cmdFlags)
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()

		client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
		skillID := args[0]
		req := &skillcatalogpb.ListSkillsRequest{
			View:      viewpb.AssetViewType_ASSET_VIEW_TYPE_VERSIONS,
			PageToken: "",
			PageSize:  50,
			StrictFilter: &skillcatalogpb.ListSkillsRequest_Filter{
				Id: proto.String(skillID),
			}}
		skills, err := listutil.ListWithCatalogClient(cmd.Context(), client, req)
		if err != nil {
			return fmt.Errorf("could not list skill versions: %w", err)
		}

		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		sd, err := listutil.SkillDescriptionsFromCatalogSkills(skills)
		if err != nil {
			return err
		}

		prtr.Print(sd)

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedVersionsCmd)
	cmdFlags.SetCommand(listReleasedVersionsCmd)
}
