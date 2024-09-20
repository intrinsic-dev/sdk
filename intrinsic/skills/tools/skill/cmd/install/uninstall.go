// Copyright 2023 Intrinsic Innovation LLC

// Package uninstall defines the skill command which uninstalls a skill.
package uninstall

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/imageutils"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/skillio"
)

var cmdFlags = cmdutils.NewCmdFlags()

var uninstallCmd = &cobra.Command{
	Use:   "uninstall --type=TYPE TARGET",
	Short: "Remove a skill",
	Example: `Stop a running skill using its build target
$ inctl skill uninstall --type=build //abc:skill_bundle --context=minikube

Stop a running skill using an already-built image file
$ inctl skill uninstall --type=archive abc/skill.bundle.tar --context=minikube

Use the solution flag to automatically resolve the context (requires the solution to run)
$ inctl skill uninstall --type=archive abc/skill.bundle.tar --solution=my-solution

Stop a running skill by specifying its id
$ inctl skill uninstall --type=id com.foo.skill
`,
	Args: cobra.ExactArgs(1),
	Aliases: []string{
		"stop",
		"unload",
	},
	RunE: func(command *cobra.Command, args []string) error {
		ctx := command.Context()
		target := args[0]

		targetType := imageutils.TargetType(cmdFlags.GetFlagSideloadStopType())
		if targetType != imageutils.Build && targetType != imageutils.Archive && targetType != imageutils.ID {
			return fmt.Errorf("type must be one of (%s, %s, %s)", imageutils.Build, imageutils.Archive, imageutils.ID)
		}

		var skillID string
		var err error
		switch targetType {
		case imageutils.Archive:
			skillID, err = skillio.SkillIDFromArchive(target)
			if err != nil {
				return err
			}
		case imageutils.Build:
			skillID, err = skillio.SkillIDFromBuildTarget(target)
			if err != nil {
				return err
			}
		case imageutils.ID:
			skillID = target
		default:
			return fmt.Errorf("unimplemented target type: %v", targetType)
		}

		ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, cmdFlags)
		if err != nil {
			return err
		}
		defer conn.Close()

		log.Printf("Removing skill %q", skillID)
		if err := imageutils.RemoveContainer(ctx, &imageutils.RemoveContainerParams{
			Address:    address,
			Connection: conn,
			Request: &installerpb.RemoveContainerAddonRequest{
				Id:   skillID,
				Type: installerpb.AddonType_ADDON_TYPE_SKILL,
			},
		}); err != nil {
			return fmt.Errorf("could not remove the skill: %w", err)
		}
		log.Print("Finished removing the skill")

		return nil
	},
}

func init() {
	cmd.SkillCmd.AddCommand(uninstallCmd)
	cmdFlags.SetCommand(uninstallCmd)

	cmdFlags.AddFlagsAddressClusterSolution()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagSideloadStopType("skill")
}
