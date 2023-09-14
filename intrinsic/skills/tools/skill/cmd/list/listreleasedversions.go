// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package listreleasedversions defines the skill list_released_versions command which lists versions of a skill in a catalog.
package listreleasedversions

import (
	"fmt"

	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	skillcataloggrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcatalogpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillCmd "intrinsic/skills/tools/skill/cmd/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/listutil"
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/printer"
)

var cmdFlags = cmdutil.NewCmdFlags()

var listReleasedVersionsCmd = &cobra.Command{
	Use:   "list_released_versions [skill_id]",
	Short: "List versions of a released skill in the catalog",
	Args:  cobra.ExactArgs(1), // skillId
	RunE: func(cmd *cobra.Command, args []string) error {
		skillID := args[0]
		project := cmdFlags.GetFlagProject()
		catalogAddress := fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project)

		ctx, dialerOpts, err := dialerutil.DialInfoCtx(cmd.Context(), dialerutil.DialInfoParams{
			Address:  catalogAddress,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not list skills: %v", err)
		}

		conn, err := grpc.DialContext(ctx, catalogAddress, *dialerOpts...)
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()

		client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
		resp, err := client.ListSkillVersions(ctx, &skillcatalogpb.ListSkillVersionsRequest{Id: skillID})
		if err != nil {
			return fmt.Errorf("could not list skill versions: %w", err)
		}

		prtr, err := printer.NewPrinter(root.FlagOutput)
		if err != nil {
			return err
		}

		prtr.Print(listutil.SkillDescriptionsFromSkillMetas(resp.GetSkills()))

		return nil
	},
}

func init() {
	skillCmd.SkillCmd.AddCommand(listReleasedVersionsCmd)
	cmdFlags.SetCommand(listReleasedVersionsCmd)

	cmdFlags.AddFlagProject()
}
