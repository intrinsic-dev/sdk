// Copyright 2023 Intrinsic Innovation LLC

// Package install defines the skill command which installs a skill.
package install

import (
	"fmt"
	"log"

	"github.com/pborman/uuid"
	"github.com/spf13/cobra"
	"intrinsic/assets/clientutils"
	"intrinsic/assets/cmdutils"
	"intrinsic/assets/idutils"
	"intrinsic/assets/imagetransfer"
	"intrinsic/assets/imageutils"
	imagepb "intrinsic/kubernetes/workcell_spec/proto/image_go_proto"
	installerpb "intrinsic/kubernetes/workcell_spec/proto/installer_go_grpc_proto"
	"intrinsic/skills/tools/skill/cmd"
	"intrinsic/skills/tools/skill/cmd/directupload"
	"intrinsic/skills/tools/skill/cmd/registry"
	"intrinsic/skills/tools/skill/cmd/waitforskill"
)

var cmdFlags = cmdutils.NewCmdFlags()

var installCmd = &cobra.Command{
	Use:   "install --type=TYPE TARGET",
	Short: "Install a skill",
	Example: `Build a skill, upload it to a container registry, and install the skill
$ inctl skill install --type=build //abc:skill.tar --registry=gcr.io/my-registry --cluster=my_cluster

Upload skill image to a container registry, and install the skill
$ inctl skill install --type=archive abc/skill.tar --registry=gcr.io/my-registry --cluster=my_cluster

Install skill using an image that has already been pushed to the container registry
$ inctl skill install --type=image gcr.io/my-workcell/abc@sha256:20ab4f --cluster=my_cluster

Use the solution flag to automatically resolve the cluster (requires the solution to run)
$ inctl skill install --type=image gcr.io/my-workcell/abc@sha256:20ab4f --solution=my-solution
`,
	Args: cobra.ExactArgs(1),
	Aliases: []string{
		"load",
		"start",
	},
	RunE: func(command *cobra.Command, args []string) error {
		ctx := command.Context()
		target := args[0]

		timeout, timeoutStr, err := cmdFlags.GetFlagSideloadStartTimeout()
		if err != nil {
			return err
		}

		ctx, conn, address, err := clientutils.DialClusterFromInctl(ctx, cmdFlags)
		if err != nil {
			return err
		}
		defer conn.Close()

		// Install the skill to the registry
		flagRegistry := cmdFlags.GetFlagRegistry()

		// Upload skill, directly, to workcell, with fail-over legacy transfer if possible
		remoteOpt, err := clientutils.RemoteOpt(cmdFlags)
		if err != nil {
			return err
		}
		transfer := imagetransfer.RemoteTransferer(remoteOpt)
		// if --type=image we are going to skip direct injection as image is already
		// available in the repository and as such push is essentially no-op. Given
		// than underlying code requires image inspection, command have to have
		// access to given image and thus there should not be an issue to get
		// image during installation. The main reason we are skipping here
		// is that direct injection does not allow to read image from workcell
		// thus making request of --type=image invalid from DI perspective.
		if imageutils.TargetType(cmdFlags.GetFlagSideloadStartType()) != imageutils.Image &&
			!cmdFlags.GetFlagSkipDirectUpload() {
			opts := []directupload.Option{
				directupload.WithDiscovery(directupload.NewFromConnection(conn)),
				directupload.WithOutput(command.OutOrStdout()),
			}
			if flagRegistry != "" {
				// User set external registry, so we can use it as fail-over.
				opts = append(opts, directupload.WithFailOver(transfer))
			} else {
				// Fake name that ends in .local in order to indicate that this is local, directly uploaded
				// image.
				flagRegistry = "direct.upload.local"
			}
			transfer = directupload.NewTransferer(ctx, opts...)
		}

		log.Printf("Publishing skill image as %q", target)
		authUser, authPwd := cmdFlags.GetFlagsRegistryAuthUserPassword()
		imgpb, installerParams, err := registry.PushSkill(target, registry.PushOptions{
			AuthUser:   authUser,
			AuthPwd:    authPwd,
			Registry:   flagRegistry,
			Type:       cmdFlags.GetFlagSideloadStartType(),
			Transferer: transfer,
		})
		if err != nil {
			return fmt.Errorf("could not push target %q to the container registry: %v", target, err)
		}

		pkg, err := idutils.PackageFrom(installerParams.SkillID)
		if err != nil {
			return fmt.Errorf("could not parse package from ID: %w", err)
		}
		name, err := idutils.NameFrom(installerParams.SkillID)
		if err != nil {
			return fmt.Errorf("could not parse name from ID: %w", err)
		}
		// No deterministic data is available for generating the sideloaded version here. Use a random
		// string instead to keep the version unique. Ideally we would probably use the digest of the
		// skill image or similar.
		version := fmt.Sprintf("0.0.1+%s", uuid.New())
		idVersion, err := idutils.IDVersionFrom(pkg, name, version)
		if err != nil {
			return fmt.Errorf("could not create id_version: %w", err)
		}
		log.Printf("Installing skill %q", idVersion)

		installerCtx := ctx

		err = imageutils.InstallContainer(installerCtx,
			&imageutils.InstallContainerParams{
				Address:    address,
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
				Connection:     conn,
				SkillID:        installerParams.SkillID,
				SkillIDVersion: idVersion,
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
	cmd.SkillCmd.AddCommand(installCmd)
	cmdFlags.SetCommand(installCmd)

	cmdFlags.AddFlagsAddressClusterSolution()
	cmdFlags.AddFlagsProjectOrg()
	cmdFlags.AddFlagRegistry()
	cmdFlags.AddFlagsRegistryAuthUserPassword()
	cmdFlags.AddFlagSideloadStartTimeout("skill")
	cmdFlags.AddFlagSideloadStartType()
	cmdFlags.AddFlagSkipDirectUpload("skill")
}
