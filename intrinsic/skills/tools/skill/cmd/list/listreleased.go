// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package listreleased defines the skill list_released command which lists skills in a catalog.
package listreleased

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

var listReleasedCmd = &cobra.Command{
	Use:   "list_released",
	Short: "List released skills in the catalog",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, _ []string) error {
		project := cmdFlags.GetFlagProject()
		catalogAddress := fmt.Sprintf("dns:///www.endpoints.%s.cloud.goog:443", project)

		ctx, dialerOpts, err := dialerutil.DialInfoCtx(cmd.Context(), dialerutil.DialInfoParams{
			Address:  catalogAddress,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not list released skills: %v", err)
		}

		conn, err := grpc.DialContext(ctx, catalogAddress, *dialerOpts...)
		if err != nil {
			return fmt.Errorf("failed to create client connection: %v", err)
		}
		defer conn.Close()

		client := skillcataloggrpcpb.NewSkillCatalogClient(conn)
		resp, err := client.ListSkills(ctx, &skillcatalogpb.ListSkillsRequest{})
		if err != nil {
			return fmt.Errorf("could not list skills: %w", err)
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
	skillCmd.SkillCmd.AddCommand(listReleasedCmd)
	cmdFlags.SetCommand(listReleasedCmd)

	cmdFlags.AddFlagProject()
}
