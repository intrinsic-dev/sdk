// Copyright 2023 Intrinsic Innovation LLC

// Package load defines the skill load command which installs a skill.
package load

import (
	"fmt"
	"log"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/v1/google"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/spf13/cobra"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/dialerutil"
	"intrinsic/skills/tools/skill/cmd/registry"
	"intrinsic/skills/tools/skill/cmd/skillid"
	"intrinsic/skills/tools/skill/cmd/solutionutil"
	"intrinsic/skills/tools/skill/cmd/waitforskill"
)

var cmdFlags = cmdutils.NewCmdFlags()

func remoteOpt() remote.Option {
	authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
	if len(authUser) != 0 && len(authPwd) != 0 {
		return remote.WithAuth(authn.FromConfig(authn.AuthConfig{
			Username: authUser,
			Password: authPwd,
		}))
	}
	return remote.WithAuthFromKeychain(google.Keychain)
}

var loadCmd = &cobra.Command{
	Use:   "load --type=TYPE TARGET",
	Short: "Install a skill",
	Example: `Build a skill, upload it to a container registry, and install the skill
$ inctl skill load --type=build //abc:skill.tar --registry=gcr.io/my-registry --context=minikube

Upload skill image to a container registry, and install the skill
$ inctl skill load --type=archive abc/skill.tar --registry=gcr.io/my-registry --context=minikube

Install skill using an image that has already been pushed to the container registry
$ inctl skill load --type=image gcr.io/my-workcell/abc@sha256:20ab4f --context=minikube

Use the solution flag to automatically resolve the context (requires the solution to run)
$ inctl skill load --type=image gcr.io/my-workcell/abc@sha256:20ab4f --solution=my-solution
`,
	Args:    cobra.ExactArgs(1),
	Aliases: []string{"start"},
	RunE: func(command *cobra.Command, args []string) error {
		target := args[0]

		timeout, timeoutStr, err := cmdFlags.GetFlagSideloadStartTimeout()
		if err != nil {
			return err
		}

		authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
		imgpb, installerParams, err := registry.PushSkill(target, registry.PushOptions{
			AuthUser:   authUser,
			AuthPwd:    authPwd,
			Registry:   cmdFlags.GetFlagRegistry(),
			Type:       cmdFlags.GetFlagSideloadStartType(),
			Transferer: imagetransfer.RemoteTransferer(remoteOpt()),
		})
		if err != nil {
			return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
		}

		k8sContext, solution := cmdFlags.GetFlagsSideloadContextSolution()
		installerAddress := cmdFlags.GetFlagInstallerAddress()
		project := cmdFlags.GetFlagProject()
		org := cmdFlags.GetFlagOrganization()

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
			k8sContext,
		)
		if err != nil {
			return fmt.Errorf("could not resolve solution to cluster: %w", err)
		}

		// Install the skill to the registry
		ctx, conn, err = dialerutil.DialConnectionCtx(command.Context(), dialerutil.DialInfoParams{
			Address:  installerAddress,
			Cluster:  cluster,
			CredName: project,
		})
		if err != nil {
			return fmt.Errorf("could not establish connection: %w", err)
		}

		skillIDVersion, err := skillid.CreateSideloadedIDVersion(installerParams.SkillID)
		if err != nil {
			return fmt.Errorf("could not create sideloaded ID version: %w", err)
		}
		version, err := idutils.VersionFrom(skillIDVersion)
		if err != nil {
			return fmt.Errorf("could not parse version from ID version: %w", err)
		}
		log.Printf("Installing skill %q using the installer service at %q", skillIDVersion, installerAddress)
		err = imageutils.InstallContainer(ctx,
			&imageutils.InstallContainerParams{
				Address:    installerAddress,
				Connection: conn,
				Request: &installerpb.InstallContainerAddonRequest{
					Id:      installerParams.SkillID,
					Version: version,
					Type:    installerpb.AddonType_ADDON_TYPE_SKILL,
					Images: []*imagepb.Image{
						imgpb,
					},
				},
			})
		if err != nil {
			return fmt.Errorf("could not install the skill: %w", err)
		}
		log.Printf("Finished installing, skill container is now starting")

		if timeout == 0 {
			return nil
		}

		log.Printf("Waiting for the skill to be available for a maximum of %s", timeoutStr)
		err = waitforskill.WaitForSkill(ctx,
			&waitforskill.Params{
				Address:        installerAddress,
				Connection:     conn,
				SkillID:        installerParams.SkillID,
				SkillIDVersion: skillIDVersion,
				WaitDuration:   timeout,
			})
		if err != nil {
			return fmt.Errorf("failed waiting for skill: %w", err)
		}
		log.Printf("The skill is now available.")
		return nil
	},
}

func init() {
	cmd.SkillCmd.AddCommand(loadCmd)
	cmdFlags.SetCommand(loadCmd)

	cmdFlags.AddFlagInstallerAddress()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagRegistry()
	cmdFlags.AddFlagsRegistryAuthUserPassword()
	cmdFlags.AddFlagsSideloadContextSolution("skill")
	cmdFlags.AddFlagSideloadStartTimeout("skill")
	cmdFlags.AddFlagSideloadStartType()
}
