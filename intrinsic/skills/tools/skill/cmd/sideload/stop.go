// Copyright 2023 Intrinsic Innovation LLC

// Package stop defines the skill stop command which removes a skill.
package stop

import (
	"fmt"
	"log"

	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"

	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/cmdutil"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/imagetransfer"
	"intrinsic/skills/tools/skill/cmd/imageutil"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
)

var cmdFlags = cmdutil.NewCmdFlags()

var stopCmd = &cobra.Command{
	Use:   "stop --type=TYPE TARGET",
	Short: "Remove a skill",
	Example: `Stop a running skill using its build target
$ inctl skill stop --type=build //abc:skill.tar --context=minikube

Stop a running skill using an already-built image file
$ inctl skill stop --type=archive abc/skill.tar --context=minikube

Stop a running skill using an already-pushed image
$ inctl skill stop --type=image gcr.io/my-workcell/abc@sha256:20ab4f --context=minikube

Use the solution flag to automatically resolve the context (requires the solution to run)
$ inctl skill stop --type=archive abc/skill.tar --solution=my-solution

Stop a running skill by specifying its id
$ inctl skill stop --type=id com.foo.skill

Stop a running skill by specifying its name [deprecated]
$ inctl skill stop --type=id skill
`,
	Args: cobra.ExactArgs(1),
	RunE: func(command *cobra.Command, args []string) error {
		target := args[0]
		targetType := imageutil.TargetType(cmdFlags.GetFlagSideloadStopType())
		if targetType != imageutil.Build && targetType != imageutil.Archive && targetType != imageutil.Image && targetType != imageutil.ID && targetType != imageutil.Name {
			return fmt.Errorf("type must be one of (%s, %s, %s, %s, %s)", imageutil.Build, imageutil.Archive, imageutil.Image, imageutil.ID, imageutil.Name)
		}

		context, solution := cmdFlags.GetFlagsSideloadContextSolution()
		installerAddress := cmdFlags.GetFlagInstallerAddress()
		project := cmdFlags.GetFlagProject()
		org := cmdFlags.GetFlagOrganization()

		skillID, err := imageutil.SkillIDFromTarget(target, imageutil.TargetType(targetType), imagetransfer.RemoteTransferer(remote.WithAuthFromKeychain(google.Keychain)))
		if err != nil {
			return fmt.Errorf("could not get skill ID: %v", err)
		}

		ctx, conn, err := dialerutil.DialConnectionCtx(command.Context(), dialerutil.DialInfoParams{
			Address:  installerAddress,
			CredName: project,
			CredOrg:  org,
		})
		if err != nil {
			return fmt.Errorf("could not create connection: %w", err)
		}
		defer conn.Close()

		cluster, err := solutionutil.GetClusterNameFromSolutionOrDefault(
			ctx,
			conn,
			solution,
			context,
		)
		if err != nil {
			return fmt.Errorf("could not resolve solution to cluster: %s", err)
		}

		// Remove the skill from the registry
		ctx, conn, err = dialerutil.DialConnectionCtx(command.Context(), dialerutil.DialInfoParams{
			Address:  installerAddress,
			Cluster:  cluster,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not remove the skill: %w", err)
		}

		log.Printf("Removing skill %q using the installer service at %q", skillID, installerAddress)
		if err := imageutil.RemoveContainer(ctx, &imageutil.RemoveContainerParams{
			Address:    installerAddress,
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
	cmd.SkillCmd.AddCommand(stopCmd)
	cmdFlags.SetCommand(stopCmd)

	cmdFlags.AddFlagInstallerAddress()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagsSideloadContextSolution("skill")
	cmdFlags.AddFlagSideloadStopType("skill")
}
