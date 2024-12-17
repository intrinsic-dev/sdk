// Copyright 2023 Intrinsic Innovation LLC

// Package cleardefault defines the command clears the default version of a skill in the catalog.
package cleardefault

import (
	"context"
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	scgrpcpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	scpb "intrinsic/skills/catalog/proto/skill_catalog_go_grpc_proto"
	skillcmd "intrinsic/skills/tools/skill/cmd/cmd"
)

var cmdFlags = cmdutils.NewCmdFlags()

func clearDefaultVersion(ctx context.Context, cmd *cobra.Command, id string) error {
	pkg, err := idutils.PackageFrom(id)
	if err != nil {
		return fmt.Errorf("invalid package field in skill ID: %q", id)
	}
	name, err := idutils.NameFrom(id)
	if err != nil {
		return fmt.Errorf("invalid name field in skill ID: %q", id)
	}
	idProto, err := idutils.IDProtoFrom(pkg, name)
	if err != nil {
		return fmt.Errorf("invalid skill ID: %q", id)
	}

	req := &scpb.ClearDefaultRequest{Id: idProto}

	log.Printf("Clearing default version for skill %q from the catalog", id)

	conn, err := clientutils.DialCatalogFromInctl(cmd, cmdFlags)
	if err != nil {
		return fmt.Errorf("failed to create client connection: %v", err)
	}
	defer conn.Close()

	if cmdFlags.GetFlagDryRun() {
		log.Printf("Skipping call to skill catalog (dry-run)")
	} else if _, err := scgrpcpb.NewSkillCatalogClient(conn).ClearDefault(ctx, req); err != nil {
		return fmt.Errorf("could not clear the default version for skill %q: %v", id, err)
	}
	log.Printf("Finished clearing the default version for the skill: %q", id)
	return nil
}

var clearDefaultCmd = &cobra.Command{
	Use:   "clear_default skill_id",
	Short: "Clear the default version of a released skill in the catalog",
	Example: `
Clear the default version of some.package.my_skill skill in the catalog:
$ inctl skill clear_default some.package.my_skill
`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		id := args[0]
		return clearDefaultVersion(cmd.Context(), cmd, id)
	},
}

func init() {
	skillcmd.SkillCmd.AddCommand(clearDefaultCmd)
	cmdFlags.SetCommand(clearDefaultCmd)

	cmdFlags.AddFlagDryRun()

}
